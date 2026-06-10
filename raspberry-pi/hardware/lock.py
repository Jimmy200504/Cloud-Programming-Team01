# -*- coding: utf-8 -*-
"""
電子鎖控制模組 (lock.py)
============================================================
提供 `Lock` 類別，採「高電位觸發解鎖」的方式控制電子鎖。

接線假設：
  GPIO(LOCK_PIN) ── 控制 MOSFET / 繼電器 ── 電子鎖
  輸出「高電位」→ 通電 → 解鎖
  輸出「低電位」→ 斷電 → 上鎖 (預設安全狀態)
"""

import config

# 只有在「實機模式」才匯入 gpiozero。
# 這樣在一般電腦 (未安裝 gpiozero) 跑模擬模式時，import 不會失敗。
if not config.MOCK_MODE:
    from gpiozero import OutputDevice


class Lock:
    """電子鎖控制類別 (高電位觸發解鎖)。"""

    def __init__(self, pin: int = config.LOCK_PIN):
        """
        :param pin: 控制電子鎖的 GPIO 腳位 (BCM 編號)
        """
        self.pin = pin

        if config.MOCK_MODE:
            # 模擬模式：不建立任何實體裝置
            self._device = None
        else:
            # active_high=True   → 呼叫 on() 時輸出高電位 (= 解鎖)
            # initial_value=False → 初始輸出低電位 (= 上鎖，較安全)
            self._device = OutputDevice(
                pin, active_high=True, initial_value=False
            )

    def unlock(self):
        """解鎖：輸出高電位。"""
        if config.MOCK_MODE:
            print(f"[Mock] 鎖已開啟 (PIN {self.pin} 輸出高電位)")
            return
        self._device.on()

    def lock(self):
        """上鎖：輸出低電位。"""
        if config.MOCK_MODE:
            print(f"[Mock] 鎖已關閉 (PIN {self.pin} 輸出低電位)")
            return
        self._device.off()

    def cleanup(self):
        """釋放 GPIO 資源 (程式結束時呼叫)。"""
        if config.MOCK_MODE:
            print("[Mock] 釋放電子鎖 GPIO 資源")
            return
        if self._device is not None:
            self._device.close()
