# -*- coding: utf-8 -*-
"""
人臉相機模組 (face_camera.py)
============================================================
提供 `FaceCamera` 類別，使用 OpenCV 啟動 USB 人臉相機拍照並存檔。

⚠️ 重要：拍完照後務必立即呼叫 cap.release() 釋放相機，
   否則其他模組 (例如食物相機若共用裝置) 會無法存取。
"""

import time
import config

# 只有在實機模式才匯入 OpenCV，避免一般電腦缺套件而崩潰。
if not config.MOCK_MODE:
    import cv2


class FaceCamera:
    """人臉辨識用 USB 相機。"""

    def __init__(self, cam_index: int = config.FACE_CAM_INDEX,
                 resolution=config.FACE_CAM_RESOLUTION):
        """
        :param cam_index: OpenCV 相機索引
        :param resolution: 擷取解析度 (寬, 高)
        """
        self.cam_index = cam_index
        self.resolution = resolution

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
        cap = cv2.VideoCapture(self.cam_index, cv2.CAP_V4L2)
        try:
            if not cap.isOpened():
                print(f"無法開啟人臉相機 (index={self.cam_index})")
                return None

            width, height = self.resolution
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

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

    def capture_when_face(self, save_path: str,
                          timeout: float = config.FACE_DETECT_TIMEOUT,
                          stable_frames: int = config.FACE_DETECT_STABLE_FRAMES,
                          should_cancel=None) -> str:
        """
        開相機持續偵測,連續 stable_frames 幀都偵測到「有人臉」才拍那一幀存檔。
        timeout 秒內都沒偵測到臉則回傳 None(讓上層提示重試)。

        ⚠️ 這裡只做「有沒有臉」的本地偵測,不辨識是誰(辨識交給雲端 Rekognition)。
        """
        if config.MOCK_MODE:
            print(f"[Mock] 偵測到人臉 → 拍照成功 → {save_path}")
            return save_path

        # 載入 Haar cascade 人臉偵測模型
        cascade = cv2.CascadeClassifier(config.FACE_CASCADE_PATH)
        if cascade.empty():
            print(f"無法載入人臉偵測模型({config.FACE_CASCADE_PATH}),改用一般拍照")
            return self.capture(save_path)

        cap = cv2.VideoCapture(self.cam_index)
        try:
            if not cap.isOpened():
                print(f"無法開啟人臉相機 (index={self.cam_index})")
                return None
            # 偵測用較低解析度,加快每幀偵測速度(對雲端辨識仍足夠)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FACE_DETECT_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FACE_DETECT_HEIGHT)

            deadline = time.time() + timeout
            hit = 0   # 連續偵測到臉的幀數
            while time.time() < deadline:
                if should_cancel is not None and should_cancel():
                    print("人臉偵測已取消")
                    return None
                ret, frame = cap.read()
                if not ret:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
                if len(faces) > 0:
                    hit += 1
                    if hit >= stable_frames:
                        cv2.imwrite(save_path, frame)
                        print(f"偵測到人臉({len(faces)} 張),拍照成功 → {save_path}")
                        return save_path
                else:
                    hit = 0   # 中斷就重新計數
            print("逾時未偵測到人臉")
            return None
        finally:
            cap.release()
