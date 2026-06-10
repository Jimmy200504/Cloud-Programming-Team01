# -*- coding: utf-8 -*-
"""
智慧冰箱 Pi 端進入點 (main.py)
============================================================
這是 Raspberry Pi 上的「單一進入點」。一個 process 同時負責:

  [背景 device agent]  (開機就掛著跑)
    - connect_cloud()        連 AWS IoT Core、訂閱 Shadow,聽遠端開鎖 / LED 警示指令
    - start_telemetry_loop() 定時讀 DHT 上報溫濕度到 Shadow reported

  [前景 HMI]           (使用者操作)
    - 存食物 / 取食物 兩條流程
    - HMI 還沒接,先用 CLI 模擬:顯示=印文字、按鈕=按 Enter

關鍵:全程只建立「一個」SmartFridgeHardware,鎖 / LED / 相機 / 麥克風 / 雲端
都由它統一擁有,背景 agent 和前景 HMI 共用同一個物件,不會搶硬體。

執行:
    cd raspberry-pi
    venv/bin/python main.py            # 真實模式(真硬體 + 真雲端)
    SF_MOCK=1 venv/bin/python main.py  # 模擬乾跑(無硬體 / 無雲端)
"""

import os
import time

import config
# 預設真實模式;SF_MOCK=1 則整套走模擬(可無硬體乾跑流程)
config.MOCK_MODE = (os.environ.get("SF_MOCK") == "1")

from hardware_api import SmartFridgeHardware


# ============================================================
#  HMI 模擬小工具(實機會換成觸控螢幕的顯示 / 按鈕)
# ============================================================
def hmi_show(msg):
    print(f"\n🖥️  [HMI 顯示] {msg}")


def hmi_button(name):
    input(f"⏵ [模擬按鈕] 按 Enter = 使用者按了「{name}」")


def _paths(prefix):
    ts = time.strftime("%Y%m%d_%H%M%S")
    return (
        os.path.join(config.CAPTURE_DIR, f"{prefix}_face_{ts}.jpg"),
        os.path.join(config.CAPTURE_DIR, f"{prefix}_food_{ts}.jpg"),
        os.path.join(config.AUDIO_DIR, f"{prefix}_audio_{ts}.wav"),
    )


def _report_lock(fridge, value):
    """若已連雲,順便把鎖的實際狀態回報到 Shadow reported。"""
    if fridge.shadow_manager is not None:
        fridge.shadow_manager.report_lock(value)


# ============================================================
#  存食物流程(前景 HMI,呼叫共用的 fridge)
# ============================================================
def put_flow(fridge):
    print("\n========== 存食物 ==========")
    face_path, food_path, audio_path = _paths("put")

    # 1. 請看鏡頭 → 相機0 拍人(狀態燈轉處理中藍)
    hmi_show("請看鏡頭")
    fridge.status_light.processing()
    time.sleep(2)
    fridge.face_camera.capture(face_path)

    # 2. 人臉認證
    auth = fridge.cloud.auth_face(face_path, action="put")
    if not auth.get("authenticated"):
        fridge.status_light.error()
        fridge.buzzer.beep_error()          # 認證失敗:簡短提示聲
        hmi_show(f"認證失敗,無法存食物。({auth.get('message', '')})")
        fridge.status_light.idle()
        return
    user = auth.get("user", {})
    hmi_show(f"歡迎 {user.get('displayName') or user.get('email')}")

    # 3. 開鎖(亮開鎖燈)+ 回報鎖狀態
    fridge.lock.unlock()
    fridge.door_led.on()
    _report_lock(fridge, config.SHADOW_LOCK_UNLOCKED)

    # 3b. 等磁簧開關偵測到門被打開
    hmi_show("已解鎖,請打開冰箱門")
    fridge.door_sensor.wait_for_open()

    # 4. 放食物 → 確認 → 預覽 → 拍好了 → 拍最清楚一張
    hmi_show("請把食物放到拍攝區,完成後按確認")
    hmi_button("確認")
    hmi_show("相機 1 即時預覽中(HMI 會顯示畫面),調整好後按「拍好了」")
    hmi_button("拍好了")
    fridge.food_camera.capture_sharpest(food_path, num_frames=5)

    # 5. 說到期日 → 錄音(亮錄音燈提示說話)→ 錄好了
    hmi_show("請說出到期日(例如:三個月後),說完按「錄好了」")
    fridge.record_led.on()
    fridge.microphone.start()
    hmi_button("錄好了")
    fridge.microphone.stop(audio_path)
    fridge.record_led.off()

    # 6. 上傳 /foods/put
    hmi_show("上傳中,請稍候…")
    resp = fridge.cloud.put_food(
        food_image_path=food_path,
        user_id=user.get("userId"),
        owner_email=user.get("email"),
        owner_user_id=user.get("userId"),
        audio_path=audio_path,
    )
    if resp.get("success", True) and not resp.get("errorCode"):
        fridge.status_light.success()
        hmi_show("存食物完成!")
    else:
        fridge.status_light.error()
        hmi_show(f"存食物失敗:{resp.get('message', resp)}")
    print("    後端回應:", resp)

    # 7. 等門關上 → 上鎖、熄開鎖燈 + 回報,狀態燈回待機
    hmi_show("請關上冰箱門")
    fridge.door_sensor.wait_for_close()
    fridge.lock.lock()
    fridge.door_led.off()
    _report_lock(fridge, config.SHADOW_LOCK_LOCKED)
    fridge.status_light.idle()


# ============================================================
#  取食物流程
# ============================================================
def retrieve_flow(fridge):
    print("\n========== 取食物 ==========")
    face_path, food_path, _ = _paths("get")

    # 1. 請看鏡頭 → 相機0 拍人(狀態燈轉處理中藍)
    hmi_show("請看鏡頭")
    fridge.status_light.processing()
    time.sleep(2)
    fridge.face_camera.capture(face_path)

    # 2. 人臉認證
    auth = fridge.cloud.auth_face(face_path, action="retrieve")
    if not auth.get("authenticated"):
        fridge.status_light.error()
        fridge.buzzer.beep_error()          # 認證失敗:簡短提示聲
        hmi_show(f"認證失敗,無法取食物。({auth.get('message', '')})")
        fridge.status_light.idle()
        return
    user = auth.get("user", {})
    hmi_show(f"歡迎 {user.get('displayName') or user.get('email')}")

    # 3. 開鎖(亮開鎖燈)+ 回報
    fridge.lock.unlock()
    fridge.door_led.on()
    _report_lock(fridge, config.SHADOW_LOCK_UNLOCKED)

    # 3b. 等磁簧開關偵測到門被打開
    hmi_show("已解鎖,請打開冰箱門")
    fridge.door_sensor.wait_for_open()

    # 4. 放要取的食物 → 確認 → 預覽 → 拍好了 → 拍一張
    hmi_show("請把要取出的食物放到拍攝區,完成後按確認")
    hmi_button("確認")
    hmi_show("相機 1 即時預覽中(HMI 會顯示畫面),調整好後按「拍好了」")
    hmi_button("拍好了")
    fridge.food_camera.capture(food_path)

    # 5. 上傳 /foods/retrieve
    hmi_show("辨識中,請稍候…")
    resp = fridge.cloud.retrieve_food(
        food_image_path=food_path,
        actor_user_id=user.get("userId"),
        actor_email=user.get("email"),
        actor_display_name=user.get("displayName"),
    )

    # 6. authorized=true 才允許取出
    if resp.get("authorized"):
        fridge.status_light.success()
        hmi_show(f"允許取出:{resp.get('message', '')}")
    else:
        fridge.status_light.error()
        fridge.buzzer.beep_warning()        # 偷拿別人食物:警告聲
        hmi_show(f"不允許取出:{resp.get('message', '')}")
        hmi_show("(若非物主,雲端會透過 Shadow 下 led=alert,背景 agent 會自動閃燈警示)")
    print("    後端回應:", resp)

    # 7. 等門關上 → 上鎖、熄開鎖燈 + 回報,狀態燈回待機
    hmi_show("請關上冰箱門")
    fridge.door_sensor.wait_for_close()
    fridge.lock.lock()
    fridge.door_led.off()
    _report_lock(fridge, config.SHADOW_LOCK_LOCKED)
    fridge.status_light.idle()


# ============================================================
#  前景 HMI 主選單
# ============================================================
def run_hmi(fridge):
    while True:
        print("\n==================================")
        print("   智慧冰箱   [1] 存食物  [2] 取食物  [q] 離開")
        print("==================================")
        choice = input("請選擇:").strip().lower()
        if choice == "1":
            put_flow(fridge)
        elif choice == "2":
            retrieve_flow(fridge)
        elif choice == "q":
            break
        else:
            print("請輸入 1 / 2 / q")


# ============================================================
#  進入點:啟動背景 agent + 跑前景 HMI
# ============================================================
def main():
    print(f"=== 智慧冰箱啟動 (MOCK_MODE={config.MOCK_MODE}) ===")
    os.makedirs(config.CAPTURE_DIR, exist_ok=True)
    os.makedirs(config.AUDIO_DIR, exist_ok=True)

    # 唯一的硬體門面,所有東西共用它
    fridge = SmartFridgeHardware()

    # ---- 背景 device agent ----
    # 連雲失敗(沒網路 / 沒憑證)時不擋住 HMI,改用離線模式繼續跑流程
    try:
        fridge.connect_cloud()                 # 訂閱 Shadow:聽遠端開鎖 / LED 警示
        fridge.start_telemetry_loop(interval=30)  # 定時上報溫濕度
        print("雲端背景服務已啟動(上報 + 監聽指令)")
    except Exception as err:
        print(f"⚠️ 雲端連線失敗,改用離線模式(只跑本地 HMI):{err}")

    # ---- 前景 HMI ----
    try:
        run_hmi(fridge)
    except KeyboardInterrupt:
        print("\n收到中斷…")
    finally:
        fridge.shutdown()
        print("已安全關閉。")


if __name__ == "__main__":
    main()
