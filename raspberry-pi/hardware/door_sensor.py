# -*- coding: utf-8 -*-
"""
門感測器模組 (door_sensor.py)
============================================================
使用 LM393 磁簧開關模組(D0 數位輸出)偵測冰箱門是否開啟。
提供 `DoorSensor` 類別:查詢目前門狀態,以及「等待門打開 / 等待門關上」。

純本地流程控制用(不寫入 Device Shadow,維持雲端契約乾淨)。
"""

import time
import config

# 只有在實機模式才匯入 gpiozero,避免一般電腦缺套件而崩潰。
if not config.MOCK_MODE:
    from gpiozero import DigitalInputDevice


class DoorSensor:
    """磁簧開關門感測器。"""

    def __init__(self, pin: int = config.DOOR_SENSOR_PIN,
                 open_when_high: bool = config.DOOR_SENSOR_OPEN_WHEN_HIGH):
        """
        :param pin: D0 接的 GPIO 腳位 (BCM 編號)
        :param open_when_high: 門「開」時 D0 為高電位則 True
        """
        self.pin = pin
        self.open_when_high = open_when_high
        # D0 為主動驅動的數位輸出,直接讀其電位
        self._dev = None if config.MOCK_MODE else DigitalInputDevice(pin)

    # ---- 狀態查詢 ----
    def is_open(self) -> bool:
        """門目前是否開啟。"""
        if config.MOCK_MODE:
            return False  # 模擬模式預設視為關閉
        high = bool(self._dev.value)          # D0 是否為高電位
        return high if self.open_when_high else (not high)

    def is_closed(self) -> bool:
        """門目前是否關閉。"""
        if config.MOCK_MODE:
            return True
        return not self.is_open()

    # ---- 等待事件(流程用)----
    def wait_for_open(self, timeout: float = 30.0) -> bool:
        """
        等待門被打開,最多等 timeout 秒。
        :return: True=偵測到開門;False=逾時
        """
        if config.MOCK_MODE:
            print("[Mock] 磁簧開關:偵測到門已開啟")
            return True
        print("等待開門中…")
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_open():
                print("磁簧開關:偵測到門已開啟")
                return True
            time.sleep(0.1)
        print("等待開門逾時")
        return False

    def wait_for_close(self, timeout: float = 30.0) -> bool:
        """
        等待門被關上,最多等 timeout 秒。
        :return: True=偵測到關門;False=逾時
        """
        if config.MOCK_MODE:
            print("[Mock] 磁簧開關:偵測到門已關閉")
            return True
        print("等待關門中…")
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_closed():
                print("磁簧開關:偵測到門已關閉")
                return True
            time.sleep(0.1)
        print("等待關門逾時")
        return False

    def cleanup(self):
        """釋放 GPIO 資源。"""
        if config.MOCK_MODE:
            print("[Mock] 釋放門感測器 GPIO 資源")
            return
        if self._dev is not None:
            self._dev.close()
