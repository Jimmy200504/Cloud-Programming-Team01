# -*- coding: utf-8 -*-
"""
食物相機模組 (food_camera.py)
============================================================
提供 `FoodCamera` 類別。食物相機為 Raspberry Pi CSI 相機
(IMX219 / Camera v2.1)，走 libcamera 架構，因此使用官方的
Picamera2 函式庫拍照，而非 OpenCV 的 VideoCapture。

⚠️ 兩支相機的擷取方式不同:
     人臉相機 (USB)  → OpenCV cv2.VideoCapture(index)   見 face_camera.py
     食物相機 (CSI)  → Picamera2 (libcamera)            本檔

拍完一樣會 stop()/close() 立即釋放相機資源。
"""

import time
import config

# 只有在實機模式才匯入 Picamera2 (需 Raspberry Pi + libcamera 環境)，
# 一般電腦跑模擬模式時不會因缺套件而崩潰。
if not config.MOCK_MODE:
    from picamera2 import Picamera2


class FoodCamera:
    """食物辨識用相機 (Raspberry Pi CSI 相機，使用 Picamera2)。"""

    def __init__(self, camera_num: int = config.FOOD_CSI_CAM_NUM,
                 resolution=config.FOOD_CSI_RESOLUTION,
                 warmup_seconds: float = config.FOOD_CSI_WARMUP_SECONDS):
        """
        :param camera_num:     libcamera 相機編號 (單顆 CSI 相機時為 0)
        :param resolution:     拍照解析度 (寬, 高)
        :param warmup_seconds: 啟動後等待自動曝光/白平衡穩定的秒數
        """
        self.camera_num = camera_num
        self.resolution = resolution
        self.warmup_seconds = warmup_seconds

    def capture(self, save_path: str) -> str:
        """
        拍一張照片並存檔。

        :param save_path: 照片儲存路徑 (例如 captures/food_xxx.jpg)
        :return: 實際存檔路徑;失敗則回傳 None
        """
        # ---- 模擬模式:不真的開相機，只印出訊息 ----
        if config.MOCK_MODE:
            print(f"[Mock] 食物相機 (CSI cam {self.camera_num}) 拍照成功 → {save_path}")
            return save_path

        # ---- 實機模式:用 Picamera2 拍照 ----
        # 每次拍照才建立 Picamera2 物件，拍完即 close()，確保相機被釋放。
        picam2 = Picamera2(camera_num=self.camera_num)
        try:
            # 建立「靜態拍照」組態並指定輸出解析度
            still_config = picam2.create_still_configuration(
                main={"size": tuple(self.resolution)}
            )
            picam2.configure(still_config)

            picam2.start()
            # 等待自動曝光/白平衡穩定，否則首張可能偏暗或偏綠
            time.sleep(self.warmup_seconds)

            picam2.capture_file(save_path)
            print(f"食物相機 (CSI) 拍照成功 → {save_path}")
            return save_path

        except Exception as err:
            print(f"食物相機 (CSI) 拍照失敗: {err}")
            return None

        finally:
            # 不論成功與否，務必停止並關閉相機以釋放資源
            try:
                picam2.stop()
            except Exception:
                pass
            picam2.close()
