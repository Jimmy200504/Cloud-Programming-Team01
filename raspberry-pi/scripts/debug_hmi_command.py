#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send one raw Nextion command and print the response frame.

Run:
    cd raspberry-pi
    python3 scripts/debug_hmi_command.py 'vis b_confirm,1'
"""

import os
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config


TERMINATOR = b"\xff\xff\xff"

NEXTION_STATUS = {
    0x00: "invalid instruction",
    0x01: "success",
    0x02: "invalid component ID",
    0x03: "invalid page ID",
    0x04: "invalid picture ID",
    0x05: "invalid font ID",
    0x11: "invalid baud rate",
    0x12: "invalid curve control/channel",
    0x1A: "invalid variable name or attribute",
    0x1B: "invalid variable operation",
    0x1C: "assignment failed",
    0x1D: "EEPROM operation failed",
    0x1E: "invalid parameter quantity",
    0x1F: "IO operation failed",
    0x20: "undefined escape character",
    0x23: "variable name too long",
}


def read_frame(ser, timeout=1.0):
    deadline = time.monotonic() + timeout
    data = bytearray()
    while time.monotonic() < deadline:
        chunk = ser.read(1)
        if not chunk:
            continue
        data.extend(chunk)
        if data.endswith(TERMINATOR):
            return bytes(data)
    return bytes(data)


def send(ser, command):
    print(f">>> {command}")
    ser.write(command.encode("utf-8") + TERMINATOR)
    ser.flush()
    frame = read_frame(ser)
    if not frame:
        print("<<< no response")
        return
    hex_frame = " ".join(f"{b:02X}" for b in frame)
    first = frame[0]
    meaning = NEXTION_STATUS.get(first, "non-status/data frame")
    print(f"<<< {hex_frame}  ({meaning})")


def main():
    try:
        import serial
    except ImportError as err:
        raise RuntimeError("pyserial is required: pip install pyserial") from err

    command = sys.argv[1] if len(sys.argv) > 1 else "vis b_confirm,1"

    print("=== HMI raw command debug ===")
    print(f"Port: {config.HMI_SERIAL_PORT}")
    print(f"Baudrate: {config.HMI_BAUDRATE}")

    with serial.Serial(config.HMI_SERIAL_PORT, config.HMI_BAUDRATE, timeout=0.1, write_timeout=1) as ser:
        ser.reset_input_buffer()
        send(ser, "bkcmd=3")
        time.sleep(0.1)
        if getattr(config, "HMI_PAGE_NAME", None):
            send(ser, f"page {config.HMI_PAGE_NAME}")
            time.sleep(0.1)
        send(ser, command)


if __name__ == "__main__":
    main()
