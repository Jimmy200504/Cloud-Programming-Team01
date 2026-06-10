# -*- coding: utf-8 -*-
"""
電子鎖控制模組 (lock.py)
============================================================
以 SG90 伺服馬達當作門鎖:轉到不同角度代表「上鎖 / 解鎖」。

  解鎖 → 轉到 LOCK_UNLOCKED_ANGLE
  上鎖 → 轉到 LOCK_LOCKED_ANGLE

轉到定位後會 detach(停止送 PWM),避免 SG90 持續抖動/嗡嗡叫;
鎖舌靠機構停在原位。介面 unlock()/lock() 與舊版相同,上層不需改動。
"""

import time
import config

# 只有在實機模式才匯入 gpiozero,避免一般電腦缺套件而崩潰。
if not config.MOCK_MODE:
    from gpiozero import AngularServo

# SG90 全行程脈寬(讓 0~180° 對應正確;gpiozero 預設只給約 90°)
_MIN_PULSE_WIDTH = 0.0005   # 0.5 ms
_MAX_PULSE_WIDTH = 0.0025   # 2.5 ms


class Lock:
    """SG90 伺服馬達門鎖。"""

    def __init__(self, pin: int = config.LOCK_PIN,
                 locked_angle: float = config.LOCK_LOCKED_ANGLE,
                 unlocked_angle: float = config.LOCK_UNLOCKED_ANGLE):
        """
        :param pin:            伺服馬達訊號腳位 (BCM 編號)
        :param locked_angle:   上鎖角度
        :param unlocked_angle: 解鎖角度
        """
        self.pin = pin
        self.locked_angle = locked_angle
        self.unlocked_angle = unlocked_angle

        if config.MOCK_MODE:
            self._servo = None
        else:
            self._servo = AngularServo(
                pin, min_angle=0, max_angle=180,
                min_pulse_width=_MIN_PULSE_WIDTH,
                max_pulse_width=_MAX_PULSE_WIDTH,
            )
            # 啟動時先轉到上鎖位置(安全預設)
            self._move(self.locked_angle)

    def _move(self, angle: float):
        """轉到指定角度,稍待到位後 detach 以停止抖動。"""
        self._servo.angle = angle
        time.sleep(0.5)
        self._servo.detach()

    def unlock(self):
        """解鎖:轉到解鎖角度。"""
        if config.MOCK_MODE:
            print(f"[Mock] 鎖已開啟 (伺服馬達轉到 {self.unlocked_angle}°)")
            return
        self._move(self.unlocked_angle)

    def lock(self):
        """上鎖:轉到上鎖角度。"""
        if config.MOCK_MODE:
            print(f"[Mock] 鎖已關閉 (伺服馬達轉到 {self.locked_angle}°)")
            return
        self._move(self.locked_angle)

    def cleanup(self):
        """釋放 GPIO 資源 (程式結束時呼叫)。"""
        if config.MOCK_MODE:
            print("[Mock] 釋放電子鎖 GPIO 資源")
            return
        if self._servo is not None:
            self._servo.close()
