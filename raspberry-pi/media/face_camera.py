# -*- coding: utf-8 -*-
"""
人臉相機模組 (face_camera.py)
============================================================
提供 `FaceCamera` 類別，使用 OpenCV 啟動「相機 0」拍照並存檔。

⚠️ 重要：拍完照後務必立即呼叫 cap.release() 釋放相機，
   否則其他模組 (例如食物相機若共用裝置) 會無法存取。
"""

import config

# 只有在實機模式才匯入 OpenCV，避免一般電腦缺套件而崩潰。
if not config.MOCK_MODE:
    import cv2


class FaceCamera:
    """人臉辨識用相機 (相機 0)。"""

    def __init__(self, cam_index: int = config.FACE_CAM_INDEX):
        """
        :param cam_index: OpenCV 相機索引 (預設 0)
        """
        self.cam_index = cam_index

    def capture(self, save_path: str) -> str:
        """
        拍一張照片並存檔。

        :param save_path: 照片儲存路徑 (例如 captures/face_xxx.jpg)
        :return: 實際存檔路徑；失敗則回傳 None
        """
        # ---- 模擬模式：不真的開相機，只印出訊息 ----
        if config.MOCK_MODE:
            print(f"[Mock] 人臉相機 (index={self.cam_index}) 拍照成功 → {save_path}")
            return save_path

        # ---- 實機模式：用 OpenCV 拍照 ----
        cap = cv2.VideoCapture(self.cam_index)
        try:
            if not cap.isOpened():
                print(f"無法開啟人臉相機 (index={self.cam_index})")
                return None

            ret, frame = cap.read()
            if not ret:
                print("人臉相機讀取畫面失敗")
                return None

            cv2.imwrite(save_path, frame)
            print(f"人臉相機拍照成功 → {save_path}")
            return save_path
        finally:
            # 不論成功與否，務必釋放相機資源
            cap.release()
