# -*- coding: utf-8 -*-
"""
全域設定檔 (config.py)
============================================================
集中管理整個智慧冰箱專案會用到的所有常數：
  - GPIO 腳位定義
  - 攝影機 / 麥克風 等設備索引
  - 音訊錄製參數
  - 檔案輸出路徑
  - AWS IoT Core 憑證路徑與 MQTT 設定

⚠️ 只要修改硬體接線或雲端設定，原則上「只需要動這個檔案」。
"""

# ============================================================
#  模擬模式 (Mock Mode)
# ============================================================
# True  : 在「一般電腦」上執行。所有底層硬體 / 影音操作都會被
#         攔截，改為「印出訊息」或「回傳假資料」，不會真的去驅動
#         GPIO / OpenCV / 錄音裝置，因此在沒有硬體的環境也能正常跑。
# False : 在「Raspberry Pi 實機」上執行，會真正驅動硬體。
MOCK_MODE = True

# ============================================================
#  GPIO 腳位定義 (採用 BCM 編號)
# ============================================================
LOCK_PIN = 17   # 電子鎖控制腳位 (高電位 → 解鎖)
LED_PIN = 27    # 狀態指示 LED 腳位
DHT_PIN = 4     # DHT22 溫濕度感測器 資料腳位

# ============================================================
#  影音設備
# ============================================================
# 人臉相機:USB 視訊裝置 (Logitech)，走 OpenCV V4L2，以 index 指定
FACE_CAM_INDEX = 0

# 食物相機:Raspberry Pi CSI 相機 (IMX219 / Camera v2.1)，走 libcamera，
# 使用 Picamera2 函式庫 (不是 OpenCV)。以下為 libcamera 列舉的相機編號，
# 只接一顆 CSI 相機時固定為 0。
FOOD_CSI_CAM_NUM = 0
FOOD_CSI_RESOLUTION = (1640, 1232)   # CSI 相機拍照解析度 (寬, 高)
FOOD_CSI_WARMUP_SECONDS = 1.0        # 啟動後等待自動曝光/白平衡穩定的秒數

# ============================================================
#  音訊錄製參數
# ============================================================
AUDIO_DURATION_SECONDS = 4      # 預設錄音秒數 (4 秒)
AUDIO_SAMPLE_RATE = 44100       # 取樣率 (Hz)
AUDIO_CHANNELS = 1              # 聲道數 (1 = 單聲道)

# ============================================================
#  檔案輸出路徑
# ============================================================
CAPTURE_DIR = "captures"        # 照片輸出資料夾
AUDIO_DIR = "recordings"        # 錄音輸出資料夾

# ============================================================
#  AWS IoT Core 設定
# ============================================================
# 你的 AWS IoT ATS Endpoint，可於 AWS IoT Console → 設定 取得
AWS_ENDPOINT = "xxxxxxxxxxxxx-ats.iot.ap-northeast-1.amazonaws.com"

# 憑證檔案路徑 (請將下載的憑證放到 certs/ 資料夾)
AWS_CERT_PATH = "certs/certificate.pem.crt"     # 裝置憑證
AWS_PRIVATE_KEY_PATH = "certs/private.pem.key"  # 裝置私鑰
AWS_ROOT_CA_PATH = "certs/AmazonRootCA1.pem"    # Amazon Root CA

# MQTT 連線識別
AWS_CLIENT_ID = "smart-fridge-pi"   # MQTT Client ID
AWS_THING_NAME = "smart-fridge"     # IoT Thing 名稱 (用於 Device Shadow)

# MQTT Topic
TOPIC_TELEMETRY = "smartfridge/telemetry"   # 上傳溫濕度資料的主題

# Device Shadow 中，代表「門鎖」的欄位名稱與「解鎖」指令值
SHADOW_DOOR_KEY = "door"        # desired 狀態裡的鍵
SHADOW_DOOR_UNLOCK = "unlock"   # 代表「請解鎖」的值
SHADOW_DOOR_LOCK = "lock"       # 代表「請上鎖」的值
