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
MOCK_MODE = False

# ============================================================
#  GPIO 腳位定義 (採用 BCM 編號)
# ============================================================
LOCK_PIN = 17   # SG90 伺服馬達 訊號腳位 (PWM)  實體 Pin 11
LOCK_LOCKED_ANGLE = 0      # 上鎖角度(依你的鎖機構微調)
LOCK_UNLOCKED_ANGLE = 90   # 解鎖角度(依你的鎖機構微調)
DHT_PIN = 4     # DHT22 溫濕度感測器 資料腳位

# --- RGB 主狀態燈(用顏色表達系統狀態:待機綠/處理藍/錯誤紅/警示紅閃)---
RGB_LED_R_PIN = 16   # 實體 Pin 36
RGB_LED_G_PIN = 20   # 實體 Pin 38
RGB_LED_B_PIN = 21   # 實體 Pin 40
RGB_LED_ACTIVE_HIGH = False  # 共陰極=True(拉高點亮);共陽極=False(140C05 是共陽極)

# --- 單色專用指示燈 ---
LED_POWER_PIN = 5     # 電源/連線燈(綠):已連雲、系統運作中  實體 Pin 29
LED_DOOR_PIN = 6      # 開鎖燈(藍):門鎖開啟中             實體 Pin 31
LED_RECORD_PIN = 13   # 錄音燈(紅):正在錄音,提示說話       實體 Pin 33

# --- 磁簧開關(門感測器,LM393 模組 D0)---
DOOR_SENSOR_PIN = 22            # D0 接腳  實體 Pin 15;⚠️ 模組 VCC 用 3.3V
DOOR_SENSOR_OPEN_WHEN_HIGH = True   # 門「開」時 D0 為高電位→True(接線後實測,不對就改 False)

# --- 蜂鳴器(Keyes 無源蜂鳴器,靠 PWM 送頻率發聲)---
BUZZER_PIN = 12   # 訊號腳(S)  實體 Pin 32

# ============================================================
#  HMI 觸控螢幕 UART
# ============================================================
# Raspberry Pi UART: GPIO14=TXD, GPIO15=RXD。/dev/serial0 會指向目前啟用的 UART。
HMI_SERIAL_PORT = "/dev/serial0"
HMI_BAUDRATE = 9600
HMI_MENU_PAGE_SETTLE_SECONDS = 0.25

# ============================================================
#  影音設備
# ============================================================
# 人臉相機:USB 視訊裝置 (Logitech)。
# 為避免重開機後 /dev/videoN 編號跑掉,優先用 /dev/v4l/by-id 的「穩定路徑」
# (依裝置序號,重開機不變)解析出目前的 index;找不到才退回 FACE_CAM_INDEX。
FACE_CAM_MATCH = "Webcam"   # 在 /dev/v4l/by-id/ 名稱裡比對的關鍵字(你的是 ...Webcam_C920...)
FACE_CAM_INDEX = 0          # 備援:by-id 找不到時用的固定 index
FACE_CAM_RESOLUTION = (640, 480)

# 人臉「本地偵測」(OpenCV Haar cascade:只判斷有沒有臉,不辨識是誰)
FACE_CASCADE_PATH = "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
FACE_DETECT_TIMEOUT = 10        # 等待偵測到人臉的最長秒數
FACE_DETECT_STABLE_FRAMES = 3   # 連續幾幀都偵測到臉才算數(避免一閃而過的誤判)
FACE_DETECT_WIDTH = 640         # 偵測用相機解析度(低一點偵測較快,對雲端辨識仍足夠)
FACE_DETECT_HEIGHT = 480

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
# 你的 AWS IoT ATS Endpoint (帳號 491919374787 / ap-northeast-1)
# 由 `aws iot describe-endpoint --endpoint-type iot:Data-ATS` 查得
AWS_ENDPOINT = "a2ddn1ymw51sga-ats.iot.ap-northeast-1.amazonaws.com"

# 憑證檔案路徑 (請將下載的憑證放到 certs/ 資料夾)
AWS_CERT_PATH = "certs/certificate.pem.crt"     # 裝置憑證
AWS_PRIVATE_KEY_PATH = "certs/private.pem.key"  # 裝置私鑰
AWS_ROOT_CA_PATH = "certs/AmazonRootCA1.pem"    # Amazon Root CA

# MQTT 連線識別
# 注意:IoT 政策常會要求 Client ID 必須等於 Thing 名稱,故兩者先設一致。
# 若 Member 3 的政策允許別的 Client ID，再調整 AWS_CLIENT_ID。
AWS_CLIENT_ID = "smart-fridge-001"   # MQTT Client ID
AWS_THING_NAME = "smart-fridge-001"  # IoT Thing 名稱 (用於 Device Shadow)
DEVICE_ID = "smart-fridge-001"       # 裝置 ID (API 與 Shadow 共用,= Thing 名稱)
IOT_POLICY_NAME = "smart-fridge-dev-device-policy"  # 憑證要掛的 IoT 政策(Member 3 提供)

# ============================================================
#  雲端 REST API (API Gateway) 設定
# ============================================================
# 業務事件走 HTTPS + JSON(base64 影像/音訊),不需 AWS 憑證。
# 來源:aws-backend/docs/hardware-embedded-integration-guide.md
API_BASE_URL = "https://v6ylyjtxga.execute-api.ap-northeast-1.amazonaws.com/dev"
TIMEZONE = "Asia/Taipei"        # 送出 capturedAt 時用的時區
API_TIMEOUT_SECONDS = 30        # API 呼叫逾時秒數

# ============================================================
#  Device Shadow 欄位 (依雲端整合契約)
# ============================================================
# 裝置狀態/硬體指令走 Shadow;影像/音訊/食物紀錄「不要」放進 Shadow。
# 門鎖:lock 欄位,值為 locked / unlocked
SHADOW_LOCK_KEY = "lock"
SHADOW_LOCK_LOCKED = "locked"
SHADOW_LOCK_UNLOCKED = "unlocked"
# LED 警示:led 欄位,值為 off / alert
SHADOW_LED_KEY = "led"
SHADOW_LED_OFF = "off"
SHADOW_LED_ALERT = "alert"
# 收到 led=alert 後,LED 閃爍持續秒數,逾時自動關閉並回報 off
LED_ALERT_SECONDS = 10
