# -*- coding: utf-8 -*-
"""
Nextion HMI interface.

Display design contract:
  - Main buttons:
      Put button -> printh 01
      Get button -> printh 02
  - Flow buttons:
      Confirm button (b_confirm) -> printh 13
  - Status text component:
      t_status

Nextion commands sent from Python are terminated with three 0xFF bytes.
`printh XX` button actions are received as raw bytes, so this module parses
single-byte event codes from the serial stream.
"""

from __future__ import annotations

import os
import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

try:
    import config
except ImportError:  # Allows importing this file from tools/tests.
    config = None


TERMINATOR = b"\xff\xff\xff"
DEFAULT_PORT = "/dev/serial0"
DEFAULT_BAUDRATE = 9600
DEFAULT_TIMEOUT_SECONDS = 0.1
DEFAULT_WAIT_TIMEOUT_SECONDS = None
RESPONSE_CHECK_TIMEOUT_SECONDS = 0.03


@dataclass(frozen=True)
class HMIEvent:
    """A button event received from the HMI."""

    code: int
    name: str


class HMIEvents:
    PUT = HMIEvent(0x01, "put")
    GET = HMIEvent(0x02, "get")
    CONFIRM = HMIEvent(0x13, "confirm")


EVENTS_BY_CODE = {
    event.code: event
    for event in (
        HMIEvents.PUT,
        HMIEvents.GET,
        HMIEvents.CONFIRM,
    )
}

BUTTON_EVENTS = {
    "put": HMIEvents.PUT,
    "get": HMIEvents.GET,
    "confirm": HMIEvents.CONFIRM,
    "b_confirm": HMIEvents.CONFIRM,
    "確認": HMIEvents.CONFIRM,
    "photo_done": HMIEvents.CONFIRM,
    "record_done": HMIEvents.CONFIRM,
    "拍好了": HMIEvents.CONFIRM,
    "錄好了": HMIEvents.CONFIRM,
}

FLOW_BUTTON_COMPONENTS = {
    "confirm": "b_confirm",
    "b_confirm": "b_confirm",
    "確認": "b_confirm",
    "photo_done": "b_confirm",
    "record_done": "b_confirm",
    "拍好了": "b_confirm",
    "錄好了": "b_confirm",
}


class HMI:
    """
    Serial interface for the HMI screen.

    In real mode this opens the configured UART and starts a background reader.
    In mock mode it keeps the same API but does not touch serial hardware.
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: Optional[int] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        mock: Optional[bool] = None,
        on_event: Optional[Callable[[HMIEvent], None]] = None,
    ):
        self.port = port or _config_value("HMI_SERIAL_PORT", os.environ.get("HMI_PORT", DEFAULT_PORT))
        self.baudrate = int(
            baudrate
            or _config_value("HMI_BAUDRATE", os.environ.get("HMI_BAUDRATE", DEFAULT_BAUDRATE))
        )
        self.timeout = timeout
        self.mock = _config_value("MOCK_MODE", False) if mock is None else mock
        self.on_event = on_event

        self._serial = None
        self._events: "queue.Queue[HMIEvent]" = queue.Queue()
        self._write_lock = threading.Lock()
        self._reader_stop = threading.Event()
        self._reader_thread = None

        if not self.mock:
            self.open()

    # ========================================================
    #  Connection lifecycle
    # ========================================================
    def open(self):
        """Open the serial port and start receiving button events."""
        if self._serial is not None:
            return

        try:
            import serial
        except ImportError as err:
            raise RuntimeError(
                "pyserial is required for the HMI serial interface. "
                "Install it with: pip install pyserial"
            ) from err

        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
            write_timeout=1,
        )
        self._configure_display()
        self._reader_stop.clear()
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

    def close(self):
        """Stop receiving and close the serial port."""
        self._reader_stop.set()
        if self._reader_thread is not None:
            self._reader_thread.join(timeout=1)
            self._reader_thread = None
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    # ========================================================
    #  Send logic: Raspberry Pi -> HMI
    # ========================================================
    def _configure_display(self):
        """Reduce serial noise from Nextion command acknowledgements."""
        self._serial.write(b"bkcmd=0" + TERMINATOR)
        self._serial.flush()
        time.sleep(0.05)
        self._serial.reset_input_buffer()

    def send_command(self, command: str):
        """Send one Nextion command, adding the required 0xFF terminator."""
        payload = command.encode("utf-8") + TERMINATOR
        if self.mock:
            print(f"[Mock HMI] send: {command}")
            return
        if self._serial is None:
            self.open()
        with self._write_lock:
            self._serial.write(payload)
            self._serial.flush()

    def set_text(self, component: str, text: str):
        """Set a Nextion text component value."""
        escaped = _escape_nextion_text(text)
        self.send_command(f'{component}.txt="{escaped}"')

    def show_status(self, text: str):
        """Update the `t_status` text component."""
        self.set_text("t_status", text)

    def show(self, text: str):
        """Compatibility alias for status text updates."""
        self.show_status(text)

    def set_visible(self, component: str, visible: bool):
        """Show or hide one Nextion component."""
        self.send_command(f"vis {component},{1 if visible else 0}")

    def show_button(self, name: str):
        """Show one named flow button."""
        self.set_visible(FLOW_BUTTON_COMPONENTS[name], True)

    def hide_button(self, name: str):
        """Hide one named flow button."""
        self.set_visible(FLOW_BUTTON_COMPONENTS[name], False)

    def hide_flow_buttons(self):
        """Hide the flow confirm button."""
        for component in sorted(set(FLOW_BUTTON_COMPONENTS.values())):
            self.set_visible(component, False)

    def show_only_flow_button(self, name: str):
        """Show one flow button and hide the other flow buttons."""
        target = FLOW_BUTTON_COMPONENTS[name]
        for component in sorted(set(FLOW_BUTTON_COMPONENTS.values())):
            self.set_visible(component, component == target)

    # ========================================================
    #  Receive logic: HMI -> Raspberry Pi
    # ========================================================
    def _read_loop(self):
        while not self._reader_stop.is_set():
            try:
                data = self._serial.read(1)
            except Exception as err:
                print(f"HMI serial read failed: {err}")
                time.sleep(0.2)
                continue
            if not data:
                continue
            self._handle_serial_byte(data[0])

    def _handle_serial_byte(self, value: int):
        if value == 0xFF:
            return

        if value in EVENTS_BY_CODE:
            suffix = self._read_response_suffix()
            if suffix == TERMINATOR:
                print(f"HMI ignored Nextion response frame: 0x{value:02x}ffffff")
                return
            self._queue_event(value)
            for extra in suffix:
                self._handle_serial_byte(extra)
            return

        print(f"HMI ignored unknown event byte: 0x{value:02x}")

    def _read_response_suffix(self) -> bytes:
        """Read a short suffix to distinguish `printh 02` from `02 FF FF FF`."""
        if self._serial is None:
            return b""

        old_timeout = self._serial.timeout
        self._serial.timeout = RESPONSE_CHECK_TIMEOUT_SECONDS
        try:
            suffix = self._serial.read(3)
        finally:
            self._serial.timeout = old_timeout
        return suffix

    def _queue_event(self, value: int):
        event = EVENTS_BY_CODE.get(value)
        if event is None:
            print(f"HMI ignored unknown event byte: 0x{value:02x}")
            return
        print(f"HMI received button: 0x{value:02x} ({event.name})")
        self._events.put(event)
        if self.on_event is not None:
            self.on_event(event)

    def wait_event(self, timeout: Optional[float] = DEFAULT_WAIT_TIMEOUT_SECONDS) -> Optional[HMIEvent]:
        """Wait for any known button event."""
        if self.mock:
            return self._wait_mock_event(timeout)
        try:
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear_events(self, settle_seconds: float = 0.0) -> int:
        """
        Drop queued button events.

        A short settle window is useful after page changes because the display
        can still deliver touch bytes from the previous page.
        """
        deadline = time.monotonic() + max(0.0, settle_seconds)
        cleared = 0

        while True:
            try:
                self._events.get_nowait()
                cleared += 1
                continue
            except queue.Empty:
                pass

            if time.monotonic() >= deadline:
                break

            time.sleep(0.01)

        if cleared:
            print(f"HMI cleared {cleared} queued event(s)")
        return cleared

    def wait_button(
        self,
        name: str,
        timeout: Optional[float] = DEFAULT_WAIT_TIMEOUT_SECONDS,
        visible_while_waiting: bool = True,
    ) -> Optional[HMIEvent]:
        """Wait until a specific logical button is pressed."""
        expected = BUTTON_EVENTS[name]
        deadline = None if timeout is None else time.monotonic() + timeout

        if visible_while_waiting and name in FLOW_BUTTON_COMPONENTS:
            self.show_only_flow_button(name)

        try:
            while True:
                remaining = None if deadline is None else max(0, deadline - time.monotonic())
                event = self.wait_event(timeout=remaining)
                if event is None:
                    return None
                if event == expected:
                    return event
        finally:
            if visible_while_waiting and name in FLOW_BUTTON_COMPONENTS:
                self.hide_flow_buttons()

    def wait_menu_choice(self, timeout: Optional[float] = DEFAULT_WAIT_TIMEOUT_SECONDS) -> Optional[str]:
        """Wait for Put/Get and return 'put' or 'get'."""
        while True:
            event = self.wait_event(timeout=timeout)
            if event is None:
                return None
            if event == HMIEvents.PUT:
                self._wait_for_menu_page_transition()
                return "put"
            if event == HMIEvents.GET:
                self._wait_for_menu_page_transition()
                return "get"

    def _wait_for_menu_page_transition(self):
        delay = float(_config_value("HMI_MENU_PAGE_SETTLE_SECONDS", 0.0) or 0.0)
        if delay > 0:
            time.sleep(delay)

    def inject_event(self, code: int):
        """Test helper for feeding a raw `printh` byte into the parser."""
        self._queue_event(code)

    def _wait_mock_event(self, timeout: Optional[float]) -> Optional[HMIEvent]:
        prompt = (
            "[Mock HMI] press: "
            "1=put, 2=get, 13=confirm, q=timeout/quit: "
        )
        raw = input(prompt).strip().lower()
        if raw in ("", "q"):
            return None
        try:
            value = int(raw, 16)
        except ValueError:
            print(f"[Mock HMI] invalid event: {raw}")
            return None
        return EVENTS_BY_CODE.get(value)


def _config_value(name: str, default):
    if config is None:
        return default
    return getattr(config, name, default)


def _escape_nextion_text(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace('"', '\\"')


_default_hmi = None


def get_default_hmi() -> HMI:
    global _default_hmi
    if _default_hmi is None:
        _default_hmi = HMI()
    return _default_hmi


def hmi_show(text: str):
    """Drop-in helper for code that only needs to update `t_status`."""
    get_default_hmi().show_status(text)


def hmi_button(name: str, timeout: Optional[float] = DEFAULT_WAIT_TIMEOUT_SECONDS) -> Optional[HMIEvent]:
    """Drop-in helper for waiting on a named HMI button."""
    return get_default_hmi().wait_button(name, timeout=timeout)
