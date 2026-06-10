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
from hardware.hmi import get_default_hmi, hmi_button, hmi_show


def debug(msg):
    print(f"[{time.strftime('%H:%M:%S')}] [main] {msg}", flush=True)


def wait_hmi_button(name):
    debug(f"等待 HMI 按鈕: {name}")
    hmi_button(name)
    debug(f"收到 HMI 按鈕: {name}")


def return_hmi_to_page0():
    debug("HMI 回到 page0")
    get_default_hmi().send_command("page page0")


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
        debug(f"回報 Shadow lock={value}")
        fridge.shadow_manager.report_lock(value)
    else:
        debug(f"未連雲,略過 Shadow lock={value} 回報")


# ============================================================
#  存食物流程(前景 HMI,呼叫共用的 fridge)
# ============================================================
def put_flow(fridge):
    print("\n========== 存食物 ==========")
    face_path, food_path, audio_path = _paths("put")
    debug(f"存食物流程開始 face={face_path}, food={food_path}, audio={audio_path}")

    # 1. 請看鏡頭 → 相機0 拍人(狀態燈轉處理中藍)
    debug("HMI 顯示: 請看鏡頭")
    hmi_show("請看鏡頭")
    debug("狀態燈: processing")
    fridge.status_light.processing()
    time.sleep(2)
    debug("人臉相機拍照開始")
    fridge.face_camera.capture(face_path)
    debug(f"人臉相機拍照完成: {face_path}")

    # 2. 人臉認證
    debug("呼叫雲端人臉認證 action=put")
    auth = fridge.cloud.auth_face(face_path, action="put")
    debug(f"人臉認證回應: {auth}")
    if not auth.get("authenticated"):
        debug("人臉認證失敗,中止存食物流程")
        fridge.status_light.error()
        fridge.buzzer.beep_error()          # 認證失敗:簡短提示聲
        hmi_show(f"認證失敗,無法存食物。({auth.get('message', '')})")
        fridge.status_light.idle()
        return
    user = auth.get("user", {})
    debug(f"人臉認證成功 user={user}")
    hmi_show(f"歡迎 {user.get('displayName') or user.get('email')}")

    wait_hmi_button("b_confirm")

    # 3. 開鎖(亮開鎖燈)+ 回報鎖狀態
    debug("開鎖並打開門燈")
    fridge.lock.unlock()
    fridge.door_led.on()
    _report_lock(fridge, config.SHADOW_LOCK_UNLOCKED)

    # 3b. 等磁簧開關偵測到門被打開
    hmi_show("已解鎖,請打開冰箱門")
    debug("等待門打開")
    fridge.door_sensor.wait_for_open()
    debug("門已打開")

    # 4. 放食物 → 確認 → 預覽 → 確認 → 拍最清楚一張
    hmi_show("請把食物放到拍攝區,完成後按確認")
    wait_hmi_button("b_confirm")
    fridge.food_camera.capture_sharpest(food_path, num_frames=5)
    debug(f"食物相機拍照完成: {food_path}")

    # 5. 說到期日 → 錄音(亮錄音燈提示說話)→ 確認
    hmi_show("請說出到期日(例如:三個月後),說完按確認")
    debug("錄音燈開啟,開始錄音")
    fridge.record_led.on()
    fridge.microphone.start()
    wait_hmi_button("b_confirm")
    debug("停止錄音")
    fridge.microphone.stop(audio_path)
    fridge.record_led.off()
    debug(f"錄音完成: {audio_path}")

    # 6. 上傳 /foods/put
    hmi_show("上傳中,請稍候…")
    debug("呼叫雲端 /foods/put")
    resp = fridge.cloud.put_food(
        food_image_path=food_path,
        user_id=user.get("userId"),
        owner_email=user.get("email"),
        owner_user_id=user.get("userId"),
        audio_path=audio_path,
    )
    debug(f"/foods/put 回應: {resp}")
    if resp.get("success", True) and not resp.get("errorCode"):
        debug("存食物成功")
        fridge.status_light.success()
        hmi_show("存食物完成!")
    else:
        debug("存食物失敗")
        fridge.status_light.error()
        hmi_show(f"存食物失敗:{resp.get('message', resp)}")
    print("    後端回應:", resp)

    # 7. 等門關上 → 上鎖、熄開鎖燈 + 回報,狀態燈回待機
    hmi_show("請關上冰箱門")
    debug("等待門關上")
    fridge.door_sensor.wait_for_close()
    debug("門已關上,上鎖並關閉門燈")
    fridge.lock.lock()
    fridge.door_led.off()
    _report_lock(fridge, config.SHADOW_LOCK_LOCKED)
    fridge.status_light.idle()
    debug("存食物流程結束")


# ============================================================
#  取食物流程
# ============================================================
def retrieve_flow(fridge):
    print("\n========== 取食物 ==========")
    face_path, food_path, _ = _paths("get")
    debug(f"取食物流程開始 face={face_path}, food={food_path}")

    # 1. 請看鏡頭 → 相機0 拍人(狀態燈轉處理中藍)
    debug("HMI 顯示: 請看鏡頭")
    hmi_show("請看鏡頭")
    debug("狀態燈: processing")
    fridge.status_light.processing()
    time.sleep(2)
    debug("人臉相機拍照開始")
    fridge.face_camera.capture(face_path)
    debug(f"人臉相機拍照完成: {face_path}")

    # 2. 人臉認證
    debug("呼叫雲端人臉認證 action=retrieve")
    auth = fridge.cloud.auth_face(face_path, action="retrieve")
    debug(f"人臉認證回應: {auth}")
    if not auth.get("authenticated"):
        debug("人臉認證失敗,中止取食物流程")
        fridge.status_light.error()
        fridge.buzzer.beep_error()          # 認證失敗:簡短提示聲
        hmi_show(f"認證失敗,無法取食物。({auth.get('message', '')})")
        fridge.status_light.idle()
        return
    user = auth.get("user", {})
    debug(f"人臉認證成功 user={user}")
    hmi_show(f"歡迎 {user.get('displayName') or user.get('email')}")

    # 3. 開鎖(亮開鎖燈)+ 回報
    debug("開鎖並打開門燈")
    fridge.lock.unlock()
    fridge.door_led.on()
    _report_lock(fridge, config.SHADOW_LOCK_UNLOCKED)

    # 3b. 等磁簧開關偵測到門被打開
    hmi_show("已解鎖,請打開冰箱門")
    debug("等待門打開")
    fridge.door_sensor.wait_for_open()
    debug("門已打開")

    # 4. 放要取的食物 → 確認 → 預覽 → 確認 → 拍一張
    hmi_show("請把要取出的食物放到拍攝區,完成後按確認")
    wait_hmi_button("b_confirm")
    hmi_show("相機 1 即時預覽中(HMI 會顯示畫面),調整好後按確認")
    wait_hmi_button("b_confirm")
    debug("食物相機拍照開始")
    fridge.food_camera.capture(food_path)
    debug(f"食物相機拍照完成: {food_path}")

    # 5. 上傳 /foods/retrieve
    hmi_show("辨識中,請稍候…")
    debug("呼叫雲端 /foods/retrieve")
    resp = fridge.cloud.retrieve_food(
        food_image_path=food_path,
        actor_user_id=user.get("userId"),
        actor_email=user.get("email"),
        actor_display_name=user.get("displayName"),
    )
    debug(f"/foods/retrieve 回應: {resp}")

    # 6. authorized=true 才允許取出
    if resp.get("authorized"):
        debug("取食物授權成功")
        fridge.status_light.success()
        hmi_show(f"允許取出:{resp.get('message', '')}")
    else:
        debug("取食物授權失敗")
        fridge.status_light.error()
        fridge.buzzer.beep_warning()        # 偷拿別人食物:警告聲
        hmi_show(f"不允許取出:{resp.get('message', '')}")
        hmi_show("(若非物主,雲端會透過 Shadow 下 led=alert,背景 agent 會自動閃燈警示)")
    print("    後端回應:", resp)

    # 7. 等門關上 → 上鎖、熄開鎖燈 + 回報,狀態燈回待機
    hmi_show("請關上冰箱門")
    debug("等待門關上")
    fridge.door_sensor.wait_for_close()
    debug("門已關上,上鎖並關閉門燈")
    fridge.lock.lock()
    fridge.door_led.off()
    _report_lock(fridge, config.SHADOW_LOCK_LOCKED)
    fridge.status_light.idle()
    debug("取食物流程結束")


# ============================================================
#  前景 HMI 主選單
# ============================================================
def run_hmi(fridge):
    hmi = get_default_hmi()
    debug("HMI 主迴圈啟動")
    while True:
        debug("顯示主選單")
        hmi_show("請選擇: 存食物 / 取食物")
        debug("等待 HMI 主選單按鈕: Put / Get")
        choice = hmi.wait_menu_choice()
        debug(f"HMI 主選單收到: {choice}")
        if choice == "put":
            try:
                put_flow(fridge)
            finally:
                return_hmi_to_page0()
        elif choice == "get":
            try:
                retrieve_flow(fridge)
            finally:
                return_hmi_to_page0()
        elif choice is None and config.MOCK_MODE:
            break
        else:
            print("等待 HMI 按鈕: Put / Get")


# ============================================================
#  進入點:啟動背景 agent + 跑前景 HMI
# ============================================================
def main():
    print(f"=== 智慧冰箱啟動 (MOCK_MODE={config.MOCK_MODE}) ===")
    debug(f"設定 CAPTURE_DIR={config.CAPTURE_DIR}, AUDIO_DIR={config.AUDIO_DIR}")
    os.makedirs(config.CAPTURE_DIR, exist_ok=True)
    os.makedirs(config.AUDIO_DIR, exist_ok=True)

    # 唯一的硬體門面,所有東西共用它
    debug("初始化 SmartFridgeHardware")
    fridge = SmartFridgeHardware()
    debug("SmartFridgeHardware 初始化完成")

    # ---- 背景 device agent ----
    # 連雲失敗(沒網路 / 沒憑證)時不擋住 HMI,改用離線模式繼續跑流程
    try:
        debug("開始連線雲端 / AWS IoT Shadow")
        fridge.connect_cloud()                 # 訂閱 Shadow:聽遠端開鎖 / LED 警示
        debug("啟動溫濕度回報迴圈")
        fridge.start_telemetry_loop(interval=30)  # 定時上報溫濕度
        print("雲端背景服務已啟動(上報 + 監聽指令)")
    except Exception as err:
        debug(f"雲端連線失敗,進入離線 HMI 模式: {err}")
        print(f"⚠️ 雲端連線失敗,改用離線模式(只跑本地 HMI):{err}")

    # ---- 前景 HMI ----
    try:
        debug("啟動前景 HMI")
        run_hmi(fridge)
    except KeyboardInterrupt:
        print("\n收到中斷…")
    finally:
        debug("關閉 HMI 與硬體資源")
        get_default_hmi().close()
        fridge.shutdown()
        print("已安全關閉。")


if __name__ == "__main__":
    main()
