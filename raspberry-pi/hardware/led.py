# -*- coding: utf-8 -*-
"""
LED 指示燈控制模組 (led.py)
============================================================
提供 `LEDControl` 類別，封裝 LED 的「開、關、閃爍」三種功能，
常用於提示使用者目前狀態 (例如：解鎖中、處理中)。
"""

import config

# 只有在實機模式才匯入 gpiozero，避免一般電腦缺套件而崩潰。
if not config.MOCK_MODE:
    from gpiozero import LED


class LEDControl:
    """LED 控制類別：提供開、關、閃爍功能。"""

    def __init__(self, pin: int = config.LED_PIN):
        """
        :param pin: 控制 LED 的 GPIO 腳位 (BCM 編號)
        """
        self.pin = pin

        if config.MOCK_MODE:
            self._led = None
        else:
            self._led = LED(pin)

    def on(self):
        """點亮 LED。"""
        if config.MOCK_MODE:
            print(f"[Mock] LED 開啟 (PIN {self.pin})")
            return
        self._led.on()

    def off(self):
        """熄滅 LED。"""
        if config.MOCK_MODE:
            print(f"[Mock] LED 關閉 (PIN {self.pin})")
            return
        self._led.off()

    def blink(self, on_time: float = 0.5, off_time: float = 0.5,
              n: int = None, background: bool = True):
        """
        讓 LED 閃爍。

        :param on_time:   每次亮的秒數
        :param off_time:  每次暗的秒數
        :param n:         閃爍次數 (None = 無限閃爍)
        :param background: True = 在背景閃爍 (不阻塞主程式)
        """
        if config.MOCK_MODE:
            print(f"[Mock] LED 閃爍 (PIN {self.pin}, 亮 {on_time}s / 暗 {off_time}s, 次數={n})")
            return
        # gpiozero 的 blink 預設即為非阻塞 (background=True)
        self._led.blink(on_time=on_time, off_time=off_time,
                        n=n, background=background)

    def cleanup(self):
        """釋放 GPIO 資源。"""
        if config.MOCK_MODE:
            print("[Mock] 釋放 LED GPIO 資源")
            return
        if self._led is not None:
            self._led.close()
