# -*- coding: utf-8 -*-
"""
Device Shadow 管理模組 (shadow_manager.py)
============================================================
提供 `ShadowManager` 類別，訂閱 AWS IoT Device Shadow 的
`desired` 狀態變化 (透過 delta 事件)。當雲端下達「開鎖指令」
(desired.door = "unlock") 時，會觸發由上層註冊的 callback。

運作流程：
  UI/App 更新 Shadow 的 desired.door = "unlock"
    → AWS 比對 reported 與 desired，產生 delta
    → 本裝置收到 delta 事件 → 呼叫 unlock callback (實際開鎖)
    → 開鎖後回報 reported.door = "unlock"，清掉 delta
"""

import config

# 只有在實機模式才匯入 awsiotsdk 的 shadow 相關模組。
if not config.MOCK_MODE:
    from awscrt import mqtt
    from awsiot import iotshadow


class ShadowManager:
    """Device Shadow 管理者：監聽 desired 狀態並觸發開鎖 callback。"""

    def __init__(self, mqtt_connection, thing_name: str = config.AWS_THING_NAME):
        """
        :param mqtt_connection: 由 MQTTClient 建立並共用的 MQTT 連線物件
                                (模擬模式時可為 None)
        :param thing_name:      AWS IoT Thing 名稱
        """
        self.thing_name = thing_name
        self._mqtt_connection = mqtt_connection
        self._unlock_callback = None   # 收到開鎖指令時要呼叫的函式

        if config.MOCK_MODE:
            self._shadow_client = None
        else:
            # IotShadowClient 包裝既有的 MQTT 連線
            self._shadow_client = iotshadow.IotShadowClient(mqtt_connection)

    def set_unlock_callback(self, callback):
        """
        註冊「收到開鎖指令時」要執行的函式。

        :param callback: 不帶參數的函式，例如 hardware_api.unlock_door
        """
        self._unlock_callback = callback

    def start(self):
        """開始訂閱 Device Shadow 的 desired 狀態變化 (delta 事件)。"""
        # ---- 模擬模式：不真的訂閱 ----
        if config.MOCK_MODE:
            print(f"[Mock] 已訂閱 Device Shadow '{self.thing_name}' 的 desired 狀態")
            return

        # ---- 實機模式：訂閱 delta 事件 ----
        delta_subscribed_future, _ = \
            self._shadow_client.subscribe_to_shadow_delta_updated_events(
                request=iotshadow.ShadowDeltaUpdatedSubscriptionRequest(
                    thing_name=self.thing_name
                ),
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=self._on_shadow_delta_updated,
            )
        # 等待訂閱完成
        delta_subscribed_future.result()
        print(f"已訂閱 Device Shadow '{self.thing_name}' 的 delta 事件")

    def _on_shadow_delta_updated(self, delta):
        """
        delta 事件的回呼：當 desired 與 reported 不一致時被呼叫。

        :param delta: iotshadow.ShadowDeltaUpdatedEvent，.state 為 dict
        """
        if not delta.state:
            return

        door_state = delta.state.get(config.SHADOW_DOOR_KEY)
        print(f"收到 Shadow delta：{config.SHADOW_DOOR_KEY} = {door_state}")

        # 只在收到「解鎖」指令時觸發 callback
        if door_state == config.SHADOW_DOOR_UNLOCK:
            if self._unlock_callback is not None:
                self._unlock_callback()
            # 開鎖完成後，回報 reported 狀態以清除 delta
            self._report_door_state(config.SHADOW_DOOR_UNLOCK)

    def _report_door_state(self, state_value: str):
        """
        回報門鎖目前狀態到 Shadow 的 reported 欄位。

        :param state_value: 例如 "unlock" 或 "lock"
        """
        if config.MOCK_MODE:
            print(f"[Mock] 回報 reported.{config.SHADOW_DOOR_KEY} = {state_value}")
            return

        request = iotshadow.UpdateShadowRequest(
            thing_name=self.thing_name,
            state=iotshadow.ShadowState(
                reported={config.SHADOW_DOOR_KEY: state_value},
            ),
        )
        self._shadow_client.publish_update_shadow(
            request, qos=mqtt.QoS.AT_LEAST_ONCE
        )
        print(f"已回報 reported.{config.SHADOW_DOOR_KEY} = {state_value}")
