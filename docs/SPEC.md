# 系統架構與合作模式
我負責硬體控制與 AWS IoT Core 連線。
最後你需要提供一個 `hardware_api.py` 作為 Facade (外觀模式)，將底層所有的硬體與影音操作包裝成乾淨的 API（例如 `unlock_door()`, `start_put_food_flow()`），以便負責 UI 的同事可以直接 import 這個檔案。

# 目錄結構與檔案實作需求
請建立以下結構與內容：

1. `raspberry-pi/config.py`
   - 集中管理所有常數：
   - 腳位定義：LOCK_PIN = 17, LED_PIN = 27, DHT_PIN = 4
   - 設備路徑：FACE_CAM_INDEX = 0, FOOD_CAM_INDEX = 1
   - AWS 憑證路徑與音訊預設秒數（4秒）。
   - 加入一個全域常數 `MOCK_MODE = True`。

2. `raspberry-pi/hardware/` (GPIO 控制，請使用 gpiozero 等現代套件)
   - `lock.py`：`Lock` 類別，高電位觸發解鎖。
   - `led.py`：`LEDControl` 類別，提供開、關、閃爍功能。
   - `dht_sensor.py`：`DHTSensor` 類別，使用 adafruit-circuitpython-dht。必須實作 Try-Catch 與 Retry 機制，因 DHT22 常有讀取失敗的問題。

3. `raspberry-pi/media/` (多媒體擷取)
   - `face_camera.py`：使用 OpenCV 啟動相機 0 拍照並存檔，拍完立即釋放 (`cap.release()`)。
   - `food_camera.py`：使用 OpenCV 啟動相機 1 拍照並存檔，拍完立即釋放。
   - `microphone.py`：使用 sounddevice 或 pyaudio 錄製指定秒數的 .wav 音訊檔。

4. `raspberry-pi/aws_iot/` (雲端通訊)
   - `mqtt_client.py`：使用 awsiotsdk，負責連線並提供 Publish 溫濕度資料的方法。
   - `shadow_manager.py`：訂閱 Device Shadow 的 `desired` 狀態，當接收到開鎖指令時觸發 callback。

5. `raspberry-pi/hardware_api.py`
   - 建立 `SmartFridgeHardware` 核心類別，初始化上述所有模組。
   - 實作非阻塞式的高階方法供 UI 呼叫，並處理好各模組間的資源調度。

# 核心開發守則 (CRUCIAL)
- **Mock Mode (模擬模式) 實作：** 請在每個硬體與影音操作的最底層加入 `if config.MOCK_MODE:` 的判斷。開啟時，僅印出動作（如 "Mock: 鎖已開啟", "Mock: 拍照成功"）或回傳假資料（如 24.5度），不執行實際 GPIO/OpenCV 操作，確保程式在一般電腦上不會 Crash。
- **詳細註解：** 請加上詳細的繁體中文註解。
- 請一步步建立資料夾與檔案，完成後請向我報告。