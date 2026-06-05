# -*- coding: utf-8 -*-
"""
真實 flow 測試腳本 (flow_test.py)  —— 開發/驗證用
============================================================
用「真相機 + 真麥克風 + 真實 API Gateway」跑一遍放/取食物的雲端流程,
驗證 Pi 端程式(face_camera / food_camera / microphone / cloud_api)
能正確擷取並與雲端對接。

不依賴 GPIO 與 IoT 憑證(不碰 lock/led/Shadow),所以相機接好就能跑。

用法:
    cd raspberry-pi
    venv/bin/python flow_test.py
"""

import time

# ⚠️ 一定要在 import 相機/雲端模組「之前」切成實機模式,
#    因為那些模組是在 import 當下才決定要不要載入 cv2/picamera2/requests。
import config
config.MOCK_MODE = False

from media.face_camera import FaceCamera
from media.food_camera import FoodCamera
from media.microphone import Microphone
from cloud_api import CloudAPIClient


def show(title, resp):
    """印出某一步的回應重點。"""
    print(f"\n----- {title} -----")
    print(resp)


def main():
    face_cam = FaceCamera()
    food_cam = FoodCamera()
    mic = Microphone()
    cloud = CloudAPIClient()

    print("=== 真實放食物流程 (action=put) ===")

    # 1. 拍人臉(請看著 USB 相機)
    print("\n[1] 3 秒後拍人臉,請正對 USB 相機…")
    time.sleep(3)
    face_path = face_cam.capture("flow_face.jpg")
    print("    人臉照:", face_path)

    # 2. 人臉認證
    auth = cloud.auth_face(face_path, action="put")
    show("/auth/face 回應", auth)
    if not auth.get("authenticated"):
        print("\n⚠️ 認證未通過(authenticated=false)。")
        print("   代表相機→API 這條通,但雲端不認得這張臉。")
        print("   請先到前端測試頁用你的臉註冊 (/users/me/face) 再跑一次。")
        return
    user = auth.get("user", {})
    print(f"\n✅ 認證成功:{user.get('displayName')} <{user.get('email')}>")

    # 3. 拍食物(請把食物放到 CSI 相機前)
    print("\n[3] 3 秒後拍食物,請把食物對準 CSI 相機…")
    time.sleep(3)
    food_path = food_cam.capture("flow_food.jpg")
    print("    食物照:", food_path)

    # 4. 錄到期日語音(例如清楚說「三個月後」)
    print("\n[4] 開始錄音 4 秒,請清楚說出到期日(例如:三個月後)…")
    audio_path = mic.record("flow_expire.wav")
    print("    語音檔:", audio_path)

    # 5. 上傳放食物
    put_resp = cloud.put_food(
        food_image_path=food_path,
        user_id=user.get("userId"),
        owner_email=user.get("email"),
        owner_user_id=user.get("userId"),
        audio_path=audio_path,
    )
    show("/foods/put 回應", put_resp)
    print("\n✅ 放食物流程完成。可到前端 My Fridge → Refresh 看是否出現、到期日是否正確。")


if __name__ == "__main__":
    main()
