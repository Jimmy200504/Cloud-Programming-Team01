# -*- coding: utf-8 -*-
"""
HMI 流程模擬器 (cli_flow.py) —— 用 CLI 模擬觸控螢幕 HMI
============================================================
HMI(Member 2 的觸控介面)還沒接,先用文字介面模擬「存 / 取」兩條 flow:
  - 「HMI 顯示」→ 用印文字模擬(實機會在螢幕顯示文字/圖片)
  - 「使用者按鈕」→ 用按 Enter 模擬

底層是真的去做:
  相機0 拍人 → /auth/face → 開鎖 → 相機1 拍食物(挑最清楚)
  → 麥克風錄音 → /foods/put(存) 或 /foods/retrieve(取)

開鎖:gpiozero 可用就驅動 GPIO(腳位未接線也無害),否則以文字模擬。

用法(要互動,請在終端機自己跑):
    cd raspberry-pi
    venv/bin/python cli_flow.py
"""

import os
import time

import config
# 預設用真相機/真麥克風/真 API;若設環境變數 SF_MOCK=1 則走模擬(可無硬體乾跑流程)
config.MOCK_MODE = (os.environ.get("SF_MOCK") == "1")

from media.face_camera import FaceCamera
from media.food_camera import FoodCamera
from media.microphone import Microphone
from cloud_api import CloudAPIClient

# --- 開鎖/上鎖:盡量用真 GPIO,失敗就模擬(GPIO 尚未接線時) ---
try:
    from hardware.lock import Lock
    _lock = Lock()

    def do_unlock():
        _lock.unlock()
        print("🔓 [硬體] 已開鎖")

    def do_lock():
        _lock.lock()
        print("🔒 [硬體] 已上鎖")
except Exception as _e:                      # 沒有 gpiozero / pin factory 時
    print(f"(GPIO 鎖無法使用,改用模擬:{_e})")

    def do_unlock():
        print("🔓 [模擬] 已開鎖(GPIO 未接線)")

    def do_lock():
        print("🔒 [模擬] 已上鎖(GPIO 未接線)")


# ============================================================
#  HMI 模擬小工具
# ============================================================
def hmi_show(msg):
    """模擬 HMI 螢幕顯示(實機是文字/圖片)。"""
    print(f"\n🖥️  [HMI 顯示] {msg}")


def hmi_button(name):
    """模擬使用者在 HMI 上按某個按鈕(用 Enter 代替)。"""
    input(f"⏵ [模擬按鈕] 按 Enter = 使用者按了「{name}」")


def _paths(prefix):
    ts = time.strftime("%Y%m%d_%H%M%S")
    return (
        os.path.join(config.CAPTURE_DIR, f"{prefix}_face_{ts}.jpg"),
        os.path.join(config.CAPTURE_DIR, f"{prefix}_food_{ts}.jpg"),
        os.path.join(config.AUDIO_DIR, f"{prefix}_audio_{ts}.wav"),
    )


# ============================================================
#  存食物 flow
# ============================================================
def put_flow(face_cam, food_cam, mic, cloud):
    print("\n========== 存食物 flow ==========")
    face_path, food_path, audio_path = _paths("put")

    # 1. 請看鏡頭 → 相機0 拍人
    hmi_show("請看鏡頭")
    time.sleep(2)
    face_cam.capture(face_path)

    # 2. 人臉認證 (action=put)
    auth = cloud.auth_face(face_path, action="put")
    if not auth.get("authenticated"):
        hmi_show(f"認證失敗,無法存食物。({auth.get('message', '')})")
        return
    user = auth.get("user", {})
    hmi_show(f"歡迎 {user.get('displayName') or user.get('email')}")

    # 3. 開鎖
    do_unlock()

    # 4. 放食物 → 確認 → 即時預覽 → 拍好了 → 相機1 拍最清楚一張
    hmi_show("請把食物放到拍攝區,完成後按確認")
    hmi_button("確認")
    hmi_show("相機 1 即時預覽中(HMI 會顯示畫面),調整好後按「拍好了」")
    hmi_button("拍好了")
    food_cam.capture_sharpest(food_path, num_frames=5)

    # 5. 說到期日 → 麥克風錄音 → 錄好了
    hmi_show("請說出到期日(例如:三個月後),說完按「錄好了」")
    mic.start()
    hmi_button("錄好了")
    mic.stop(audio_path)

    # 6. 上傳 /foods/put(食物照 + 錄音 + 使用者資訊)
    hmi_show("上傳中,請稍候…")
    resp = cloud.put_food(
        food_image_path=food_path,
        user_id=user.get("userId"),
        owner_email=user.get("email"),
        owner_user_id=user.get("userId"),
        audio_path=audio_path,
    )
    if resp.get("success", True) and not resp.get("errorCode"):
        hmi_show("存食物完成!")
    else:
        hmi_show(f"存食物失敗:{resp.get('message', resp)}")
    print("    後端回應:", resp)

    # 7. 流程結束上鎖(實機是使用者關門後上鎖)
    do_lock()


# ============================================================
#  取食物 flow
# ============================================================
def retrieve_flow(face_cam, food_cam, mic, cloud):
    print("\n========== 取食物 flow ==========")
    face_path, food_path, _ = _paths("get")

    # 1. 請看鏡頭 → 相機0 拍人
    hmi_show("請看鏡頭")
    time.sleep(2)
    face_cam.capture(face_path)

    # 2. 人臉認證 (action=retrieve)
    auth = cloud.auth_face(face_path, action="retrieve")
    if not auth.get("authenticated"):
        hmi_show(f"認證失敗,無法取食物。({auth.get('message', '')})")
        return
    user = auth.get("user", {})
    hmi_show(f"歡迎 {user.get('displayName') or user.get('email')}")

    # 3. 開鎖
    do_unlock()

    # 4. 放要取出的食物 → 確認 → 預覽 → 拍好了 → 相機1 拍一張
    hmi_show("請把要取出的食物放到拍攝區,完成後按確認")
    hmi_button("確認")
    hmi_show("相機 1 即時預覽中(HMI 會顯示畫面),調整好後按「拍好了」")
    hmi_button("拍好了")
    food_cam.capture(food_path)

    # 5. 上傳 /foods/retrieve(食物照 + 使用者資訊)
    hmi_show("辨識中,請稍候…")
    resp = cloud.retrieve_food(
        food_image_path=food_path,
        actor_user_id=user.get("userId"),
        actor_email=user.get("email"),
        actor_display_name=user.get("displayName"),
    )

    # 6. authorized=true 才允許取出
    if resp.get("authorized"):
        hmi_show(f"允許取出:{resp.get('message', '')}")
    else:
        hmi_show(f"不允許取出:{resp.get('message', '')}")
        hmi_show("(若非物主,雲端會透過 Device Shadow 下 led=alert,Pi 收到後閃燈警示)")
    print("    後端回應:", resp)

    # 7. 流程結束上鎖
    do_lock()


# ============================================================
#  主選單
# ============================================================
def main():
    # 確保輸出資料夾存在
    os.makedirs(config.CAPTURE_DIR, exist_ok=True)
    os.makedirs(config.AUDIO_DIR, exist_ok=True)

    face_cam = FaceCamera()
    food_cam = FoodCamera()
    mic = Microphone()
    cloud = CloudAPIClient()

    while True:
        print("\n==================================")
        print("   智慧冰箱 HMI 模擬器")
        print("   [1] 存食物    [2] 取食物    [q] 離開")
        print("==================================")
        choice = input("請選擇:").strip().lower()
        if choice == "1":
            put_flow(face_cam, food_cam, mic, cloud)
        elif choice == "2":
            retrieve_flow(face_cam, food_cam, mic, cloud)
        elif choice == "q":
            print("結束。")
            break
        else:
            print("請輸入 1 / 2 / q")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中斷,結束。")
