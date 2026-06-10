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
    確認     -> printh 11
    拍好了   -> printh 12
    錄好了   -> printh 13
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
        hmi.hide_flow_buttons()
        hmi.show_status("HMI test ready")
        time.sleep(0.5)
        hmi.show_status("請按任一按鈕")

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
                hmi.show_status("確認 pressed")
            elif event == HMIEvents.PHOTO_DONE:
                hmi.show_status("拍好了 pressed")
            elif event == HMIEvents.RECORD_DONE:
                hmi.show_status("錄好了 pressed")
    except KeyboardInterrupt:
        print("\nStopping HMI test.")
    finally:
        hmi.show_status("HMI test stopped")
        hmi.close()


if __name__ == "__main__":
    main()
