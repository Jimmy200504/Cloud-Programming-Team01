# -*- coding: utf-8 -*-
"""
LED 控制模組 (led.py)
============================================================
提供兩種 LED 控制:
  - LEDControl:單色 LED(開/關/閃爍),用於專用指示燈(電源、開鎖、錄音)
  - StatusLight:RGB 主狀態燈,用顏色表達系統狀態(待機/處理中/錯誤/警示)
"""

import config

# 只有在實機模式才匯入 gpiozero,避免一般電腦缺套件而崩潰。
if not config.MOCK_MODE:
    from gpiozero import LED, RGBLED


class LEDControl:
    """單色 LED 控制:提供開、關、閃爍功能。"""

    def __init__(self, pin: int):
        """
        :param pin: 控制 LED 的 GPIO 腳位 (BCM 編號)
        """
        self.pin = pin
        self._led = None if config.MOCK_MODE else LED(pin)

    def on(self):
        if config.MOCK_MODE:
            print(f"[Mock] LED 開啟 (PIN {self.pin})")
            return
        self._led.on()

    def off(self):
        if config.MOCK_MODE:
            print(f"[Mock] LED 關閉 (PIN {self.pin})")
            return
        self._led.off()

    def blink(self, on_time: float = 0.5, off_time: float = 0.5,
              n: int = None, background: bool = True):
        if config.MOCK_MODE:
            print(f"[Mock] LED 閃爍 (PIN {self.pin}, 亮 {on_time}s/暗 {off_time}s, 次數={n})")
            return
        self._led.blink(on_time=on_time, off_time=off_time, n=n, background=background)

    def cleanup(self):
        if config.MOCK_MODE:
            print(f"[Mock] 釋放 LED GPIO 資源 (PIN {self.pin})")
            return
        if self._led is not None:
            self._led.close()


# 預先定義的顏色 (R, G, B),數值 0~1
_RED = (1, 0, 0)
_GREEN = (0, 1, 0)
_BLUE = (0, 0, 1)
_OFF = (0, 0, 0)


class StatusLight:
    """RGB 主狀態燈:用顏色表達系統當下狀態。"""

    def __init__(self,
                 r_pin: int = config.RGB_LED_R_PIN,
                 g_pin: int = config.RGB_LED_G_PIN,
                 b_pin: int = config.RGB_LED_B_PIN,
                 active_high: bool = config.RGB_LED_ACTIVE_HIGH):
        """
        :param r_pin/g_pin/b_pin: RGB 三通道的 GPIO 腳位
        :param active_high: 共陰極=True(拉高點亮);共陽極=False
        """
        self.pins = (r_pin, g_pin, b_pin)
        if config.MOCK_MODE:
            self._rgb = None
        else:
            # pwm=True 讓三通道可調亮度以混出任意顏色
            self._rgb = RGBLED(r_pin, g_pin, b_pin, active_high=active_high, pwm=True)

    def _solid(self, color, name):
        if config.MOCK_MODE:
            print(f"[Mock] 狀態燈 → {name} {color}")
            return
        self._rgb.color = color

    # ---- 語意化狀態 ----
    def idle(self):
        """待機/正常:綠燈恆亮。"""
        self._solid(_GREEN, "待機(綠)")

    def processing(self):
        """處理中(認證/上傳/辨識):藍燈恆亮。"""
        self._solid(_BLUE, "處理中(藍)")

    def error(self):
        """錯誤/認證失敗:紅燈恆亮。"""
        self._solid(_RED, "錯誤(紅)")

    def success(self):
        """成功:綠燈快閃 3 下。"""
        if config.MOCK_MODE:
            print("[Mock] 狀態燈 → 成功(綠閃 3 下)")
            return
        self._rgb.blink(on_time=0.15, off_time=0.15, n=3,
                        on_color=_GREEN, off_color=_OFF, background=True)

    def alert(self):
        """警示(非物主取食物):紅燈持續閃爍。"""
        if config.MOCK_MODE:
            print("[Mock] 狀態燈 → 警示(紅閃)")
            return
        self._rgb.blink(on_time=0.3, off_time=0.3,
                        on_color=_RED, off_color=_OFF, background=True)

    def off(self):
        """熄滅。"""
        if config.MOCK_MODE:
            print("[Mock] 狀態燈 → 熄滅")
            return
        self._rgb.off()

    def cleanup(self):
        if config.MOCK_MODE:
            print("[Mock] 釋放 RGB 狀態燈 GPIO 資源")
            return
        if self._rgb is not None:
            self._rgb.close()
