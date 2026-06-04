# -*- coding: utf-8 -*-
"""
硬體外觀 API (hardware_api.py) — Facade 外觀模式
============================================================
這是「給 UI 同事使用的唯一入口」。它把底層所有硬體 (電子鎖、LED、
溫濕度感測器) 與影音 (人臉相機、食物相機、麥克風) 及雲端 (MQTT、
Device Shadow) 操作，包裝成乾淨、好懂的高階 API。

UI 同事只要：
    from hardware_api import SmartFridgeHardware

    fridge = SmartFridgeHardware()
    fridge.connect_cloud()                 # 連線雲端、開始監聽遠端開鎖
    fridge.unlock_door()                   # 開門 (非阻塞)
    fridge.start_put_food_flow(on_complete=cb)   # 放食物完整流程 (非阻塞)
    temp, humidity = fridge.read_climate() # 讀取溫濕度
    fridge.start_telemetry_loop()          # 背景定時上傳溫濕度

設計重點：
  1. 非阻塞 (Non-blocking)：耗時的動作 (開門等待、拍照、錄音) 都在
     背景執行緒執行，不會卡住 UI。完成後透過 on_complete callback 通知。
  2. 資源調度：相機 / 麥克風一次只允許一個流程使用，以 _resource_lock
     (threading.Lock) 序列化，避免裝置衝突。
"""

import os
import sys
import time
import threading
from datetime import datetime

# ------------------------------------------------------------
# 確保能 import 同目錄下的 config 與各子套件
# (即使 UI 同事從別的目錄 import 本檔，也能正確找到模組)
# ------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import config
from hardware.lock import Lock
from hardware.led import LEDControl
from hardware.dht_sensor import DHTSensor
from media.face_camera import FaceCamera
from media.food_camera import FoodCamera
from media.microphone import Microphone
from aws_iot.mqtt_client import MQTTClient
from aws_iot.shadow_manager import ShadowManager


class SmartFridgeHardware:
    """智慧冰箱硬體核心類別 (Facade)。"""

    def __init__(self):
        # ---- 初始化所有底層硬體 / 影音模組 ----
        self.lock = Lock()
        self.led = LEDControl()
        self.dht = DHTSensor()
        self.face_camera = FaceCamera()
        self.food_camera = FoodCamera()
        self.microphone = Microphone()

        # ---- 雲端模組 ----
        self.mqtt_client = MQTTClient()
        self.shadow_manager = None   # 連線後才建立 (需共用 MQTT 連線)

        # ---- 資源調度 ----
        # 相機 / 麥克風等共享裝置，一次只允許一個流程使用
        self._resource_lock = threading.Lock()
        # 控制背景溫濕度上傳迴圈的旗標
        self._telemetry_running = False

        # 確保輸出資料夾存在 (實機模式才需要實際寫檔)
        if not config.MOCK_MODE:
            os.makedirs(config.CAPTURE_DIR, exist_ok=True)
            os.makedirs(config.AUDIO_DIR, exist_ok=True)

    # ========================================================
    #  內部小工具
    # ========================================================
    def _timestamp(self) -> str:
        """產生檔名用的時間戳字串。"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _capture_path(self, prefix: str) -> str:
        """組出照片儲存路徑。"""
        return os.path.join(config.CAPTURE_DIR, f"{prefix}_{self._timestamp()}.jpg")

    def _audio_path(self, prefix: str) -> str:
        """組出錄音儲存路徑。"""
        return os.path.join(config.AUDIO_DIR, f"{prefix}_{self._timestamp()}.wav")

    # ========================================================
    #  雲端連線管理
    # ========================================================
    def connect_cloud(self):
        """
        連線至 AWS IoT Core，並開始監聽遠端 (雲端) 的開鎖指令。
        收到開鎖指令時，會自動呼叫 self.unlock_door()。
        """
        self.mqtt_client.connect()
        # ShadowManager 共用 MQTTClient 的連線
        self.shadow_manager = ShadowManager(self.mqtt_client.connection)
        self.shadow_manager.set_unlock_callback(self.unlock_door)
        self.shadow_manager.start()
        print("雲端連線完成，已開始監聽遠端開鎖指令")

    # ========================================================
    #  高階方法 (供 UI 呼叫，皆為非阻塞)
    # ========================================================
    def unlock_door(self, auto_relock_seconds: int = 5):
        """
        解鎖開門 (非阻塞)。開門後 LED 亮起，經過指定秒數後自動上鎖。

        :param auto_relock_seconds: 幾秒後自動上鎖
        """
        def _flow():
            self.lock.unlock()
            self.led.on()
            time.sleep(auto_relock_seconds)
            self.lock.lock()
            self.led.off()
            print("門已自動上鎖")

        threading.Thread(target=_flow, daemon=True).start()

    def lock_door(self):
        """立即上鎖 (同步、瞬間完成)。"""
        self.lock.lock()
        self.led.off()

    def start_put_food_flow(self, record_audio: bool = True, on_complete=None):
        """
        「放食物」完整流程 (非阻塞)。整個流程在背景執行緒進行：
          1. 人臉相機拍照 (記錄是誰在放食物)
          2. 解鎖、LED 亮起
          3. 食物相機拍照 (記錄放入的食物)
          4. (選擇性) 錄製語音備註
          5. 上鎖、LED 熄滅
          6. 透過 on_complete 回傳結果

        :param record_audio: 是否錄製語音備註
        :param on_complete:  完成時呼叫的 callback，會收到一個 dict：
                             {"face": 路徑, "food": 路徑, "audio": 路徑}
        """
        def _flow():
            # 使用資源鎖，確保同時間只有一個流程在用相機 / 麥克風
            with self._resource_lock:
                result = {"face": None, "food": None, "audio": None}

                # 1. 拍攝人臉
                result["face"] = self.face_camera.capture(self._capture_path("face"))

                # 2. 解鎖、亮燈
                self.lock.unlock()
                self.led.on()

                # 3. 拍攝食物
                result["food"] = self.food_camera.capture(self._capture_path("food"))

                # 4. 錄製語音備註 (選擇性)
                if record_audio:
                    result["audio"] = self.microphone.record(self._audio_path("note"))

                # 5. 上鎖、熄燈
                self.lock.lock()
                self.led.off()

                print(f"放食物流程完成: {result}")

            # 6. 通知 UI (在資源鎖外呼叫，避免 callback 內又佔用資源造成死結)
            if on_complete is not None:
                on_complete(result)

        threading.Thread(target=_flow, daemon=True).start()

    def capture_face(self, on_complete=None):
        """單獨拍攝人臉照片 (非阻塞)。完成後以路徑呼叫 on_complete。"""
        def _flow():
            with self._resource_lock:
                path = self.face_camera.capture(self._capture_path("face"))
            if on_complete is not None:
                on_complete(path)
        threading.Thread(target=_flow, daemon=True).start()

    def capture_food(self, on_complete=None):
        """單獨拍攝食物照片 (非阻塞)。完成後以路徑呼叫 on_complete。"""
        def _flow():
            with self._resource_lock:
                path = self.food_camera.capture(self._capture_path("food"))
            if on_complete is not None:
                on_complete(path)
        threading.Thread(target=_flow, daemon=True).start()

    # ========================================================
    #  溫濕度相關
    # ========================================================
    def read_climate(self):
        """
        讀取目前溫濕度 (同步)。

        :return: (temperature, humidity)；讀取失敗則為 (None, None)
        """
        return self.dht.read()

    def publish_climate(self):
        """讀取一次溫濕度並上傳雲端 (同步)。回傳 (temperature, humidity)。"""
        temperature, humidity = self.dht.read()
        self.mqtt_client.publish_telemetry(temperature, humidity)
        return temperature, humidity

    def start_telemetry_loop(self, interval: int = 60):
        """
        啟動背景執行緒，每隔 interval 秒自動讀取並上傳一次溫濕度 (非阻塞)。

        :param interval: 上傳間隔秒數
        """
        if self._telemetry_running:
            print("溫濕度上傳迴圈已在執行中")
            return

        self._telemetry_running = True

        def _loop():
            while self._telemetry_running:
                self.publish_climate()
                # 以小段睡眠分次等待，讓 stop 能較快生效
                for _ in range(interval):
                    if not self._telemetry_running:
                        break
                    time.sleep(1)

        threading.Thread(target=_loop, daemon=True).start()
        print(f"已啟動溫濕度上傳迴圈 (每 {interval} 秒一次)")

    def stop_telemetry_loop(self):
        """停止背景溫濕度上傳迴圈。"""
        self._telemetry_running = False
        print("已停止溫濕度上傳迴圈")

    # ========================================================
    #  資源釋放
    # ========================================================
    def shutdown(self):
        """關閉所有資源 (程式結束前呼叫)。"""
        self.stop_telemetry_loop()
        self.lock.cleanup()
        self.led.cleanup()
        self.dht.cleanup()
        self.mqtt_client.disconnect()
        print("已關閉所有硬體與雲端資源")


# ============================================================
#  直接執行本檔時的簡單示範 (python hardware_api.py)
# ============================================================
if __name__ == "__main__":
    print("=== SmartFridgeHardware 示範 (MOCK_MODE = "
          f"{config.MOCK_MODE}) ===\n")

    fridge = SmartFridgeHardware()

    # 連線雲端
    fridge.connect_cloud()

    # 讀取溫濕度
    print("\n-- 讀取溫濕度 --")
    print("結果:", fridge.read_climate())

    # 上傳一次溫濕度
    print("\n-- 上傳溫濕度 --")
    fridge.publish_climate()

    # 開門 (非阻塞，2 秒後自動上鎖)
    print("\n-- 開門 --")
    fridge.unlock_door(auto_relock_seconds=2)

    # 放食物完整流程 (非阻塞)
    print("\n-- 放食物流程 --")
    done_event = threading.Event()

    def _on_done(result):
        print("UI 收到完成通知:", result)
        done_event.set()

    fridge.start_put_food_flow(on_complete=_on_done)

    # 等待流程跑完 (示範用；實際 UI 不需這樣等)
    done_event.wait(timeout=10)
    time.sleep(2.5)  # 等開門的自動上鎖也跑完

    print("\n=== 示範結束 ===")
