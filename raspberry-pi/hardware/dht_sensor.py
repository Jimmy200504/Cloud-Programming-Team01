# -*- coding: utf-8 -*-
"""
DHT22 溫濕度感測器模組 (dht_sensor.py)
============================================================
提供 `DHTSensor` 類別，使用 adafruit-circuitpython-dht 讀取溫濕度。

⚠️ 重要：DHT22 是出了名「容易讀取失敗」的感測器，常會丟出
   RuntimeError。因此本模組實作了「Try-Catch + Retry (重試)」機制，
   讀取失敗時會自動重試數次，全部失敗才回傳 (None, None)。
"""

import time
import config

# 只有在實機模式才匯入 Adafruit 函式庫與 board (腳位對應)。
if not config.MOCK_MODE:
    import adafruit_dht
    import board


class DHTSensor:
    """DHT22 溫濕度感測器 (含重試機制)。"""

    def __init__(self, pin: int = config.DHT_PIN,
                 retries: int = 3, retry_delay: float = 2.0):
        """
        :param pin:         DHT22 資料腳位 (BCM 編號)
        :param retries:     讀取失敗時的最大重試次數
        :param retry_delay: 每次重試之間的等待秒數 (DHT22 兩次讀取需間隔)
        """
        self.pin = pin
        self.retries = retries
        self.retry_delay = retry_delay

        if config.MOCK_MODE:
            self._dht = None
        else:
            # board.D4 之類的腳位物件，依設定的 pin 動態取得
            pin_obj = getattr(board, f"D{pin}")
            # use_pulseio=False 在部分 Pi 上較穩定，可視情況調整
            self._dht = adafruit_dht.DHT22(pin_obj)

    def read(self):
        """
        讀取溫濕度。

        :return: (temperature, humidity) tuple，單位為 (攝氏度, %)。
                 若重試後仍失敗，回傳 (None, None)。
        """
        # ---- 模擬模式：直接回傳假資料 ----
        if config.MOCK_MODE:
            fake_temp, fake_humidity = 24.5, 55.0
            print(f"[Mock] 讀取溫濕度成功 → {fake_temp}°C, {fake_humidity}%")
            return fake_temp, fake_humidity

        # ---- 實機模式：Try-Catch + Retry ----
        for attempt in range(1, self.retries + 1):
            try:
                temperature = self._dht.temperature
                humidity = self._dht.humidity

                # 有時會回傳 None，需一併視為失敗
                if temperature is not None and humidity is not None:
                    return temperature, humidity

                print(f"DHT 讀取到 None (第 {attempt}/{self.retries} 次)，重試中…")

            except RuntimeError as err:
                # RuntimeError 是 DHT22 偶發的讀取錯誤，屬正常現象，重試即可
                print(f"DHT 讀取失敗 (第 {attempt}/{self.retries} 次): {err}")

            except Exception as err:
                # 其他非預期錯誤 (例如裝置被拔除)，記錄後中止重試
                print(f"DHT 發生非預期錯誤，停止重試: {err}")
                break

            # 重試前先等待 (最後一次不需等)
            if attempt < self.retries:
                time.sleep(self.retry_delay)

        # 全部重試皆失敗
        print("DHT 多次重試後仍讀取失敗，回傳 (None, None)")
        return None, None

    def cleanup(self):
        """釋放感測器資源。"""
        if config.MOCK_MODE:
            print("[Mock] 釋放 DHT 感測器資源")
            return
        if self._dht is not None:
            self._dht.exit()
