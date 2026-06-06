# -*- coding: utf-8 -*-
"""
Device Shadow 互動測試監聽器 (shadow_listen.py) —— 開發用
============================================================
連上 AWS IoT Core、訂閱 Shadow delta,並把目前狀態回報到 reported。
收到 lock/led 指令時印出來,並「模擬執行」後回報相符的 reported(讓 delta 消掉),
藉此觀察完整的 雲端 desired ←→ 裝置 reported 同步閉環。

用法:
    cd raspberry-pi
    venv/bin/python shadow_listen.py
    # 然後在「另一個終端」用 aws iot-data update-thing-shadow 改 desired,
    # 或到 AWS Console 編輯 Shadow,看這裡有沒有即時收到。
    # Ctrl+C 結束。
"""

import time
import config
config.MOCK_MODE = False

from aws_iot.mqtt_client import MQTTClient
from aws_iot.shadow_manager import ShadowManager


def main():
    mqtt = MQTTClient()
    mqtt.connect()
    sm = ShadowManager(mqtt.connection)

    def on_lock(value):
        print(f"\n>>> 收到 lock 指令: {value}  → 模擬執行,回報 reported.lock={value}")
        sm.report_lock(value)          # 回報相符狀態 → delta 的 lock 會消失

    def on_led(value):
        print(f"\n>>> 收到 led 指令: {value}  → 模擬執行,回報 reported.led={value}")
        # led=off 時連 desired 一起清掉(對應契約:警示結束)
        sm.report_led(value, clear_desired=(value == config.SHADOW_LED_OFF))

    sm.set_lock_callback(on_lock)
    sm.set_led_callback(on_led)
    sm.start()

    # 回報初始狀態
    sm.report_lock(config.SHADOW_LOCK_LOCKED)
    sm.report_led(config.SHADOW_LED_OFF)
    print("\n監聽中… 去改 desired 看這裡會不會即時收到。Ctrl+C 結束。\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n結束,中斷連線。")
        mqtt.disconnect()


if __name__ == "__main__":
    main()
