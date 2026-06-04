# -*- coding: utf-8 -*-
"""
硬體外觀 API (hardware_api.py) — Facade 外觀模式
============================================================
給 UI/HMI 同事(Member 2)使用的唯一入口。把底層硬體(鎖、LED、DHT)、
影音(人臉/食物相機、麥克風)、雲端(API Gateway + IoT Device Shadow)
包裝成乾淨的高階 API。

對應雲端整合契約 (hardware-embedded-integration-guide.md):
  - 業務事件(人臉認證、放/取食物、解析到期日)→ 走 CloudAPIClient (API Gateway)
  - 裝置狀態/硬體指令(鎖、LED、溫濕度)         → 走 ShadowManager (Device Shadow)

UI 用法範例:
    from hardware_api import SmartFridgeHardware
    fridge = SmartFridgeHardware()
    fridge.connect_cloud()                          # 連 MQTT、監聽 lock/led 指令
    fridge.start_put_food_flow(on_complete=cb)      # 放食物完整流程(非阻塞)
    fridge.start_retrieve_food_flow(on_complete=cb) # 取食物完整流程(非阻塞)
    fridge.start_telemetry_loop()                   # 背景定時回報溫濕度

設計重點:
  1. 非阻塞:耗時動作都在背景執行緒,完成後以 on_complete callback 回傳結果。
  2. 資源調度:相機/麥克風一次只給一個流程用,以 _resource_lock 序列化。
  3. 雲端開鎖/警示:雲端透過 Shadow desired 下指令,Pi 收到 delta 後操作硬體並回報 reported。
"""

import os
import sys
import time
import threading
from datetime import datetime

# ------------------------------------------------------------
# 確保能 import 同目錄下的 config 與各子套件(即使從別的目錄被 import)
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
from cloud_api import CloudAPIClient


class SmartFridgeHardware:
    """智慧冰箱硬體核心類別 (Facade)。"""

    def __init__(self):
        # ---- 底層硬體 / 影音模組 ----
        self.lock = Lock()
        self.led = LEDControl()
        self.dht = DHTSensor()
        self.face_camera = FaceCamera()
        self.food_camera = FoodCamera()
        self.microphone = Microphone()

        # ---- 雲端模組 ----
        self.cloud = CloudAPIClient()        # API Gateway(業務事件)
        self.mqtt_client = MQTTClient()      # MQTT 連線
        self.shadow_manager = None           # 連線後建立(需共用 MQTT 連線)

        # ---- 資源調度 ----
        self._resource_lock = threading.Lock()   # 相機/麥克風序列化
        self._telemetry_running = False           # 溫濕度迴圈旗標
        self._led_alert_active = False            # LED 警示是否進行中

        # 確保輸出資料夾存在(實機才需實際寫檔)
        if not config.MOCK_MODE:
            os.makedirs(config.CAPTURE_DIR, exist_ok=True)
            os.makedirs(config.AUDIO_DIR, exist_ok=True)

    # ========================================================
    #  內部小工具
    # ========================================================
    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _capture_path(self, prefix: str) -> str:
        return os.path.join(config.CAPTURE_DIR, f"{prefix}_{self._timestamp()}.jpg")

    def _audio_path(self, prefix: str) -> str:
        return os.path.join(config.AUDIO_DIR, f"{prefix}_{self._timestamp()}.wav")

    # ========================================================
    #  雲端連線管理
    # ========================================================
    def connect_cloud(self):
        """連線 AWS IoT Core,訂閱 Shadow,並回報初始狀態。"""
        self.mqtt_client.connect()
        self.shadow_manager = ShadowManager(self.mqtt_client.connection)
        # 註冊雲端指令回呼:lock / led
        self.shadow_manager.set_lock_callback(self._on_lock_command)
        self.shadow_manager.set_led_callback(self._on_led_command)
        self.shadow_manager.start()
        # 上線時回報目前狀態(預設上鎖、LED 關)
        self.shadow_manager.report_lock(config.SHADOW_LOCK_LOCKED)
        self.shadow_manager.report_led(config.SHADOW_LED_OFF)
        print("雲端連線完成,已開始監聽 lock / led 指令")

    # ========================================================
    #  Shadow 指令回呼(雲端 → 硬體)
    # ========================================================
    def _on_lock_command(self, value: str):
        """收到 Shadow 的 lock 指令:unlocked → 開鎖、locked → 上鎖,完成後回報 reported。"""
        if value == config.SHADOW_LOCK_UNLOCKED:
            self.lock.unlock()
            self._report_lock(config.SHADOW_LOCK_UNLOCKED)
        elif value == config.SHADOW_LOCK_LOCKED:
            self.lock.lock()
            self._report_lock(config.SHADOW_LOCK_LOCKED)

    def _on_led_command(self, value: str):
        """收到 Shadow 的 led 指令:alert → 閃爍警示、off → 關閉。"""
        if value == config.SHADOW_LED_ALERT:
            self._start_led_alert()
        elif value == config.SHADOW_LED_OFF:
            self._stop_led_alert()

    def _report_lock(self, value: str):
        if self.shadow_manager is not None:
            self.shadow_manager.report_lock(value)

    # ========================================================
    #  LED 警示(收到 led=alert 時)
    # ========================================================
    def _start_led_alert(self):
        """LED 閃爍 LED_ALERT_SECONDS 秒後自動關閉,並回報 reported.led。"""
        if self._led_alert_active:
            return
        self._led_alert_active = True

        def _flow():
            self.led.blink(on_time=0.3, off_time=0.3)   # 非阻塞閃爍
            if self.shadow_manager is not None:
                self.shadow_manager.report_led(config.SHADOW_LED_ALERT)
            # 持續警示一段時間(可被 _stop_led_alert 提早結束)
            for _ in range(config.LED_ALERT_SECONDS):
                if not self._led_alert_active:
                    break
                time.sleep(1)
            self.led.off()
            self._led_alert_active = False
            # 警示結束:回報 off,並把 desired.led 一併設 off 以清掉 delta
            if self.shadow_manager is not None:
                self.shadow_manager.report_led(config.SHADOW_LED_OFF, clear_desired=True)
            print("LED 警示結束")

        threading.Thread(target=_flow, daemon=True).start()

    def _stop_led_alert(self):
        """提早結束 LED 警示。"""
        self._led_alert_active = False
        self.led.off()
        if self.shadow_manager is not None:
            self.shadow_manager.report_led(config.SHADOW_LED_OFF, clear_desired=True)

    # ========================================================
    #  放食物流程(非阻塞)
    # ========================================================
    def start_put_food_flow(self, record_audio: bool = True, on_complete=None):
        """
        放食物完整流程(背景執行):
          1. 拍人臉 → 2. /auth/face(action=put)→ 3. 認證失敗則中止
          4. 開鎖+亮燈 → 5. 拍食物 → 6. 錄到期日語音
          7. /foods/put(食物照+語音)→ 8. 上鎖+熄燈 → 9. 回報結果

        on_complete 會收到 dict:
          {"status": "ok"/"face-auth-failed"/"error", "user":..., "food_result":..., ...}
        """
        def _flow():
            result = {"status": "error"}
            with self._resource_lock:
                try:
                    # 1~3 人臉認證
                    face_path = self.face_camera.capture(self._capture_path("face"))
                    auth = self.cloud.auth_face(face_path, action="put")
                    if not auth.get("authenticated"):
                        result = {"status": "face-auth-failed", "auth": auth}
                        return
                    user = auth.get("user", {})

                    # 4 開鎖、亮燈
                    self.lock.unlock()
                    self.led.on()
                    self._report_lock(config.SHADOW_LOCK_UNLOCKED)

                    # 5~6 拍食物、錄音
                    food_path = self.food_camera.capture(self._capture_path("food"))
                    audio_path = self.microphone.record(self._audio_path("expire")) \
                        if record_audio else None

                    # 7 上傳放食物
                    food_result = self.cloud.put_food(
                        food_image_path=food_path,
                        user_id=user.get("userId"),
                        owner_email=user.get("email"),
                        owner_user_id=user.get("userId"),
                        audio_path=audio_path,
                    )

                    # 8 上鎖、熄燈
                    self.lock.lock()
                    self.led.off()
                    self._report_lock(config.SHADOW_LOCK_LOCKED)

                    result = {"status": "ok", "user": user, "food_result": food_result}
                except Exception as err:
                    print(f"放食物流程發生錯誤: {err}")
                    # 發生例外仍確保上鎖、熄燈
                    self.lock.lock()
                    self.led.off()
                    result = {"status": "error", "error": str(err)}
                finally:
                    print(f"放食物流程結束: {result}")

            if on_complete is not None:
                on_complete(result)

        threading.Thread(target=_flow, daemon=True).start()

    # ========================================================
    #  取食物流程(非阻塞)
    # ========================================================
    def start_retrieve_food_flow(self, on_complete=None):
        """
        取食物完整流程(背景執行):
          1. 拍人臉 → 2. /auth/face(action=retrieve)→ 3. 認證失敗則中止(不開鎖)
          4. 拍食物 → 5. /foods/retrieve
          6. authorized=True → 開鎖讓使用者取走,再上鎖
             authorized=False → 不開鎖(雲端會透過 Shadow 下 led=alert 警示)
          7. 回報結果
        """
        def _flow():
            result = {"status": "error"}
            with self._resource_lock:
                try:
                    # 1~3 人臉認證
                    face_path = self.face_camera.capture(self._capture_path("face"))
                    auth = self.cloud.auth_face(face_path, action="retrieve")
                    if not auth.get("authenticated"):
                        result = {"status": "face-auth-failed", "auth": auth}
                        return
                    user = auth.get("user", {})

                    # 4 拍食物
                    food_path = self.food_camera.capture(self._capture_path("food"))

                    # 5 上傳取食物
                    retrieve_result = self.cloud.retrieve_food(
                        food_image_path=food_path,
                        actor_user_id=user.get("userId"),
                        actor_email=user.get("email"),
                        actor_display_name=user.get("displayName"),
                    )

                    # 6 只有 authorized 才開鎖
                    if retrieve_result.get("authorized"):
                        self.lock.unlock()
                        self._report_lock(config.SHADOW_LOCK_UNLOCKED)
                        # 給使用者一段時間取走後上鎖
                        time.sleep(5)
                        self.lock.lock()
                        self._report_lock(config.SHADOW_LOCK_LOCKED)
                        result = {"status": "ok", "authorized": True,
                                  "user": user, "retrieve_result": retrieve_result}
                    else:
                        # 不開鎖;警示由雲端透過 Shadow 下 led=alert 驅動
                        result = {"status": "unauthorized", "authorized": False,
                                  "user": user, "retrieve_result": retrieve_result}
                except Exception as err:
                    print(f"取食物流程發生錯誤: {err}")
                    self.lock.lock()
                    result = {"status": "error", "error": str(err)}
                finally:
                    print(f"取食物流程結束: {result}")

            if on_complete is not None:
                on_complete(result)

        threading.Thread(target=_flow, daemon=True).start()

    # ========================================================
    #  溫濕度(回報到 Shadow reported)
    # ========================================================
    def read_climate(self):
        """讀取目前溫濕度(同步)。回傳 (temperature, humidity)。"""
        return self.dht.read()

    def report_climate(self):
        """讀取一次溫濕度並回報到 Shadow reported。回傳 (temperature, humidity)。"""
        temperature, humidity = self.dht.read()
        if self.shadow_manager is not None:
            self.shadow_manager.report_climate(temperature, humidity)
        return temperature, humidity

    def start_telemetry_loop(self, interval: int = 60):
        """背景每 interval 秒回報一次溫濕度到 Shadow(非阻塞)。"""
        if self._telemetry_running:
            print("溫濕度回報迴圈已在執行中")
            return
        self._telemetry_running = True

        def _loop():
            while self._telemetry_running:
                self.report_climate()
                for _ in range(interval):
                    if not self._telemetry_running:
                        break
                    time.sleep(1)

        threading.Thread(target=_loop, daemon=True).start()
        print(f"已啟動溫濕度回報迴圈(每 {interval} 秒)")

    def stop_telemetry_loop(self):
        self._telemetry_running = False
        print("已停止溫濕度回報迴圈")

    # ========================================================
    #  資源釋放
    # ========================================================
    def shutdown(self):
        """關閉所有資源(程式結束前呼叫)。"""
        self.stop_telemetry_loop()
        self._led_alert_active = False
        self.lock.cleanup()
        self.led.cleanup()
        self.dht.cleanup()
        self.mqtt_client.disconnect()
        print("已關閉所有硬體與雲端資源")


# ============================================================
#  直接執行本檔時的簡單示範 (python hardware_api.py)
# ============================================================
if __name__ == "__main__":
    print(f"=== SmartFridgeHardware 示範 (MOCK_MODE = {config.MOCK_MODE}) ===\n")

    fridge = SmartFridgeHardware()
    fridge.connect_cloud()

    print("\n-- 讀取/回報溫濕度 --")
    fridge.report_climate()

    print("\n-- 模擬雲端下達 led=alert(Shadow delta)--")
    fridge._on_led_command(config.SHADOW_LED_ALERT)

    print("\n-- 模擬雲端下達 lock=unlocked(Shadow delta)--")
    fridge._on_lock_command(config.SHADOW_LOCK_UNLOCKED)

    print("\n-- 放食物流程 --")
    done = threading.Event()
    fridge.start_put_food_flow(on_complete=lambda r: (print("UI 收到:", r), done.set()))
    done.wait(timeout=10)

    print("\n-- 取食物流程 --")
    done2 = threading.Event()
    fridge.start_retrieve_food_flow(on_complete=lambda r: (print("UI 收到:", r), done2.set()))
    done2.wait(timeout=15)

    time.sleep(2)
    print("\n=== 示範結束 ===")
