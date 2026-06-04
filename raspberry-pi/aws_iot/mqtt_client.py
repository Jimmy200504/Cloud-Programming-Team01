# -*- coding: utf-8 -*-
"""
AWS IoT Core MQTT 連線模組 (mqtt_client.py)
============================================================
提供 `MQTTClient` 類別，使用 awsiotsdk (awscrt + awsiot) 透過
mTLS 連線至 AWS IoT Core，並提供「發布溫濕度資料」的方法。

此處建立的 MQTT 連線也會分享給 shadow_manager 使用，
避免重複建立連線。
"""

import json
import time
import config

# 只有在實機模式才匯入 awsiotsdk，避免一般電腦缺套件而崩潰。
if not config.MOCK_MODE:
    from awscrt import mqtt
    from awsiot import mqtt_connection_builder


class MQTTClient:
    """AWS IoT Core MQTT 用戶端。"""

    def __init__(self):
        # 底層 MQTT 連線物件 (連線後才會有值)
        self._connection = None

    @property
    def connection(self):
        """取得底層 MQTT 連線物件 (供 ShadowManager 共用)。"""
        return self._connection

    def connect(self):
        """連線至 AWS IoT Core。"""
        # ---- 模擬模式：不真的連線 ----
        if config.MOCK_MODE:
            print("[Mock] 已連線至 AWS IoT Core")
            return

        # ---- 實機模式：以 mTLS 憑證建立連線 ----
        self._connection = mqtt_connection_builder.mtls_from_path(
            endpoint=config.AWS_ENDPOINT,
            cert_filepath=config.AWS_CERT_PATH,
            pri_key_filepath=config.AWS_PRIVATE_KEY_PATH,
            ca_filepath=config.AWS_ROOT_CA_PATH,
            client_id=config.AWS_CLIENT_ID,
            clean_session=False,
            keep_alive_secs=30,
        )

        print(f"連線中… (endpoint={config.AWS_ENDPOINT})")
        connect_future = self._connection.connect()
        connect_future.result()  # 阻塞等待連線完成
        print("已連線至 AWS IoT Core")

    def publish_telemetry(self, temperature, humidity):
        """
        發布溫濕度資料到 telemetry 主題。

        :param temperature: 溫度 (攝氏)，可能為 None (讀取失敗)
        :param humidity:    濕度 (%)，可能為 None
        """
        # 組成 JSON payload
        payload = {
            "device_id": config.AWS_CLIENT_ID,
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": int(time.time()),
        }

        # ---- 模擬模式：只印出要發布的內容 ----
        if config.MOCK_MODE:
            print(f"[Mock] 發布溫濕度到 '{config.TOPIC_TELEMETRY}': {payload}")
            return

        # ---- 實機模式：實際發布 ----
        self._connection.publish(
            topic=config.TOPIC_TELEMETRY,
            payload=json.dumps(payload),
            qos=mqtt.QoS.AT_LEAST_ONCE,
        )
        print(f"已發布溫濕度: {payload}")

    def disconnect(self):
        """中斷與 AWS IoT Core 的連線。"""
        if config.MOCK_MODE:
            print("[Mock] 已中斷 AWS IoT Core 連線")
            return
        if self._connection is not None:
            disconnect_future = self._connection.disconnect()
            disconnect_future.result()
            print("已中斷 AWS IoT Core 連線")
