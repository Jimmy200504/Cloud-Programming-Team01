# -*- coding: utf-8 -*-
"""
Device Shadow 管理模組 (shadow_manager.py)
============================================================
依據雲端整合契約 (hardware-embedded-integration-guide.md) 處理 Device Shadow。

裝置狀態/硬體指令一律走 Shadow,欄位:
  - lock:  locked / unlocked   (門鎖)
  - led:   off / alert         (LED 警示)
  - temperature / humidity / lastSeenAt  (環境與心跳,只寫 reported)

運作流程:
  雲端(Lambda/前端)更新 Shadow 的 desired
    → AWS 比對 reported 與 desired,在 delta 主題發出差異
    → 本裝置收到 delta → 觸發 lock / led 回呼(由 hardware_api 實際操作硬體)
    → 硬體動作完成後,回報 reported 清掉 delta

訂閱主題:$aws/things/<thing>/shadow/update/delta
回報主題:$aws/things/<thing>/shadow/update
"""

from datetime import datetime, timezone, timedelta
import config

# 只有在實機模式才匯入 awsiotsdk 的 shadow 模組。
if not config.MOCK_MODE:
    from awscrt import mqtt
    from awsiot import iotshadow


# 台北時區 (+08:00),用於 lastSeenAt
_TZ = timezone(timedelta(hours=8))


def _now_iso() -> str:
    """回傳含時區的 ISO8601 時間字串。"""
    return datetime.now(_TZ).isoformat(timespec="seconds")


class ShadowManager:
    """Device Shadow 管理者:監聽 lock/led 指令並回報 reported 狀態。"""

    def __init__(self, mqtt_connection, thing_name: str = config.AWS_THING_NAME):
        """
        :param mqtt_connection: 由 MQTTClient 建立並共用的 MQTT 連線(Mock 時為 None)
        :param thing_name:      AWS IoT Thing 名稱
        """
        self.thing_name = thing_name
        self._mqtt_connection = mqtt_connection
        self._lock_callback = None   # 收到 lock 指令時呼叫:callback(value)
        self._led_callback = None    # 收到 led 指令時呼叫:callback(value)

        if config.MOCK_MODE:
            self._shadow_client = None
        else:
            self._shadow_client = iotshadow.IotShadowClient(mqtt_connection)

    # ------------------------------------------------------------
    #  回呼註冊
    # ------------------------------------------------------------
    def set_lock_callback(self, callback):
        """註冊收到 lock 指令時要執行的函式,callback 會收到 'locked'/'unlocked'。"""
        self._lock_callback = callback

    def set_led_callback(self, callback):
        """註冊收到 led 指令時要執行的函式,callback 會收到 'off'/'alert'。"""
        self._led_callback = callback

    # ------------------------------------------------------------
    #  訂閱 delta
    # ------------------------------------------------------------
    def start(self):
        """開始訂閱 Device Shadow 的 delta(desired 與 reported 的差異)。"""
        if config.MOCK_MODE:
            print(f"[Mock] 已訂閱 Device Shadow '{self.thing_name}' 的 delta(lock/led)")
            return

        delta_future, _ = self._shadow_client.subscribe_to_shadow_delta_updated_events(
            request=iotshadow.ShadowDeltaUpdatedSubscriptionRequest(
                thing_name=self.thing_name
            ),
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=self._on_shadow_delta_updated,
        )
        delta_future.result()  # 等待訂閱完成
        print(f"已訂閱 Device Shadow '{self.thing_name}' 的 delta 事件")

    def _on_shadow_delta_updated(self, delta):
        """delta 回呼:desired 與 reported 不一致時被呼叫。delta.state 為 dict。"""
        state = getattr(delta, "state", None)
        if not state:
            return
        print(f"收到 Shadow delta:{state}")

        # 門鎖指令
        if config.SHADOW_LOCK_KEY in state and self._lock_callback is not None:
            self._lock_callback(state[config.SHADOW_LOCK_KEY])

        # LED 指令
        if config.SHADOW_LED_KEY in state and self._led_callback is not None:
            self._led_callback(state[config.SHADOW_LED_KEY])

    # ------------------------------------------------------------
    #  回報 reported 狀態
    # ------------------------------------------------------------
    def report(self, reported: dict, desired: dict = None):
        """
        回報狀態到 Shadow。一律附上 lastSeenAt(心跳時間)。

        :param reported: 要寫入 reported 的欄位 dict
        :param desired:  (選填)要一併寫入 desired 的欄位,例如警示結束後清掉 desired.led
        """
        reported = dict(reported)
        reported.setdefault("lastSeenAt", _now_iso())

        if config.MOCK_MODE:
            msg = f"[Mock] 回報 reported={reported}"
            if desired:
                msg += f", desired={desired}"
            print(msg)
            return

        state = iotshadow.ShadowState(reported=reported, desired=desired)
        request = iotshadow.UpdateShadowRequest(
            thing_name=self.thing_name, state=state
        )
        self._shadow_client.publish_update_shadow(request, qos=mqtt.QoS.AT_LEAST_ONCE)
        print(f"已回報 Shadow reported={reported}" + (f", desired={desired}" if desired else ""))

    # --- 便利方法 ---
    def report_lock(self, value: str):
        """回報門鎖狀態(locked / unlocked)。"""
        self.report({config.SHADOW_LOCK_KEY: value})

    def report_led(self, value: str, clear_desired: bool = False):
        """
        回報 LED 狀態(off / alert)。

        :param clear_desired: 警示結束關燈時設 True,會一併把 desired.led 設為該值以清除 delta。
        """
        desired = {config.SHADOW_LED_KEY: value} if clear_desired else None
        self.report({config.SHADOW_LED_KEY: value}, desired=desired)

    def report_climate(self, temperature, humidity):
        """回報溫濕度到 reported(契約規定走 Shadow,不另開 telemetry topic)。"""
        self.report({"temperature": temperature, "humidity": humidity})
