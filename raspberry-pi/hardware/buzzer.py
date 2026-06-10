# -*- coding: utf-8 -*-
"""
蜂鳴器模組 (buzzer.py)
============================================================
Keyes 無源蜂鳴器:靠 PWM 送不同頻率的方波才會發聲(有源的才是通電即響)。
提供兩種語意化提示音:
  - beep_error()   :認證/操作失敗的「簡短提示聲」
  - beep_warning() :偷拿別人食物的「警告聲」(較急促)
"""

import time
import config

# 只有在實機模式才匯入 gpiozero,避免一般電腦缺套件而崩潰。
if not config.MOCK_MODE:
    from gpiozero import PWMOutputDevice


class Buzzer:
    """無源蜂鳴器(PWM 發聲)。"""

    def __init__(self, pin: int = config.BUZZER_PIN):
        """
        :param pin: 蜂鳴器訊號腳 (BCM 編號)
        """
        self.pin = pin
        # frequency 決定音高,value(占空比)0=不響、0.5=發聲
        self._dev = None if config.MOCK_MODE else \
            PWMOutputDevice(pin, frequency=1000, initial_value=0)

    def _tone(self, freq: int, duration: float):
        """以指定頻率發聲 duration 秒。"""
        self._dev.frequency = freq
        self._dev.value = 0.5
        time.sleep(duration)
        self._dev.value = 0

    def beep_error(self):
        """認證/操作失敗:短促兩聲提示。"""
        if config.MOCK_MODE:
            print("[Mock] 蜂鳴器:嗶嗶(失敗提示聲)")
            return
        for _ in range(2):
            self._tone(1200, 0.12)
            time.sleep(0.08)

    def beep_warning(self):
        """警告(非物主取食物):高低交替的急促警報聲。"""
        if config.MOCK_MODE:
            print("[Mock] 蜂鳴器:嗶—嗶—嗶(警告聲)")
            return
        for _ in range(4):
            self._tone(1800, 0.15)
            self._tone(600, 0.15)

    def cleanup(self):
        """釋放 GPIO 資源。"""
        if config.MOCK_MODE:
            print("[Mock] 釋放蜂鳴器 GPIO 資源")
            return
        if self._dev is not None:
            self._dev.off()
            self._dev.close()
