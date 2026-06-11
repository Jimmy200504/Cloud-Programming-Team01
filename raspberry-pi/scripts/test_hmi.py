#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive HMI serial test.

Run on the Raspberry Pi:
    cd raspberry-pi
    python3 scripts/test_hmi.py

Expected HMI button events:
    Put      -> printh 01
    Get      -> printh 02
    b_confirm -> printh 13
    Back     -> printh 14
"""

import os
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config
from hardware.hmi import HMI, HMIEvents


def main():
    print("=== HMI serial test ===")
    print(f"Port: {config.HMI_SERIAL_PORT}")
    print(f"Baudrate: {config.HMI_BAUDRATE}")
    print("Press Ctrl+C to stop.\n")

    hmi = HMI(mock=False)
    try:
        hmi.show_status("HMI test ready")
        hmi.show_climate(4.2, 55)
        time.sleep(0.5)
        hmi.show_status("請按任一按鈕")
        time.sleep(0.5)
        print("Sending direct command: vis b_confirm,1")
        hmi.send_command("vis b_confirm,1")

        while True:
            event = hmi.wait_event(timeout=1)
            if event is None:
                continue

            print(f"received: 0x{event.code:02X} ({event.name})")

            if event == HMIEvents.PUT:
                hmi.show_status("Put pressed")
            elif event == HMIEvents.GET:
                hmi.show_status("Get pressed")
            elif event == HMIEvents.CONFIRM:
                hmi.show_status("b_confirm pressed")
            elif event == HMIEvents.BACK:
                hmi.show_status("Back pressed")
    except KeyboardInterrupt:
        print("\nStopping HMI test.")
    finally:
        hmi.show_status("HMI test stopped")
        hmi.close()


if __name__ == "__main__":
    main()
