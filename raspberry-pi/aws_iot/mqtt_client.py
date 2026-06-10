# -*- coding: utf-8 -*-
"""
AWS IoT Core MQTT 連線模組 (mqtt_client.py)
============================================================
使用 awsiotsdk (awscrt + awsiot) 透過 mTLS 連線至 AWS IoT Core,
只負責「建立並管理 MQTT 連線」。

連線建立後,連線物件會分享給 shadow_manager 使用(Device Shadow 也走
同一條 MQTT 連線)。

注意:依雲端整合契約,溫濕度等裝置狀態一律寫入 Device Shadow 的 reported,
      不另外發布到自訂的 telemetry topic。因此本模組不含 publish 業務資料的方法,
      溫濕度回報請用 shadow_manager.report_climate()。
"""

import config

# 只有在實機模式才匯入 awsiotsdk,避免一般電腦缺套件而崩潰。
if not config.MOCK_MODE:
    from awsiot import mqtt_connection_builder


class MQTTClient:
    """AWS IoT Core MQTT 連線管理者。"""

    def __init__(self):
        self._connection = None  # 底層 MQTT 連線(連線後才有值)

    @property
    def connection(self):
        """取得底層 MQTT 連線物件(供 ShadowManager 共用)。"""
        return self._connection

    def connect(self):
        """以 mTLS 憑證連線至 AWS IoT Core。"""
        # ---- 模擬模式:不真的連線 ----
        if config.MOCK_MODE:
            print("[Mock] 已連線至 AWS IoT Core")
            return

        # ---- 實機模式:以裝置憑證建立連線 ----
        self._connection = mqtt_connection_builder.mtls_from_path(
            endpoint=config.AWS_ENDPOINT,
            cert_filepath=config.AWS_CERT_PATH,
            pri_key_filepath=config.AWS_PRIVATE_KEY_PATH,
            ca_filepath=config.AWS_ROOT_CA_PATH,
            client_id=config.AWS_CLIENT_ID,
            clean_session=False,
            keep_alive_secs=30,
        )

        print(f"連線中… (endpoint={config.AWS_ENDPOINT}, client_id={config.AWS_CLIENT_ID})")
        connect_future = self._connection.connect()
        connect_future.result()  # 阻塞等待連線完成
        print("已連線至 AWS IoT Core")

    def disconnect(self):
        """中斷與 AWS IoT Core 的連線。"""
        if config.MOCK_MODE:
            print("[Mock] 已中斷 AWS IoT Core 連線")
            return
        if self._connection is not None:
            self._connection.disconnect().result()
            print("已中斷 AWS IoT Core 連線")
