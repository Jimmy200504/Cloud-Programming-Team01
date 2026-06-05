# -*- coding: utf-8 -*-
"""
人臉註冊工具 (register_face.py) —— 開發用,用 Pi 鏡頭現場拍照註冊
============================================================
契約上「人臉註冊」原本是前端/測試頁的工作,但前端只支援『上傳檔案』。
這支工具讓你直接用 Pi 的 USB 鏡頭「現場拍照」完成註冊:

  1. 用 email/密碼向 Cognito 登入 (USER_PASSWORD_AUTH) 取得 IdToken
  2. 用 USB 人臉相機拍一張
  3. 帶 Bearer IdToken 打 POST /users/me/face 註冊人臉

前置條件:帳號要先存在(signup + email 驗證,在前端測試頁做過一次即可)。

⚠️ 密碼用環境變數帶,不要寫進檔案、也不要貼到對話:
    export SF_EMAIL='you@example.com'
    export SF_PASSWORD='your-password'
    cd raspberry-pi
    venv/bin/python register_face.py
"""

import os
import sys
import base64

import config
config.MOCK_MODE = False           # 要真的拍照、真的打 API

from media.face_camera import FaceCamera
import requests

# --- 這兩個值來自前端 frontend/test/app.js 的設定(共用同一個 dev 後端)---
AWS_REGION = "ap-northeast-1"
COGNITO_CLIENT_ID = "58u2jdcqh3l2r7or7uctogai9n"
COGNITO_URL = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/"


def cognito_login(email: str, password: str) -> str:
    """以 USER_PASSWORD_AUTH 登入,回傳 IdToken。"""
    resp = requests.post(
        COGNITO_URL,
        headers={
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Content-Type": "application/x-amz-json-1.1",
        },
        json={
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": COGNITO_CLIENT_ID,
            "AuthParameters": {"USERNAME": email, "PASSWORD": password},
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Cognito 登入失敗 ({resp.status_code}): {resp.text}")
    return resp.json()["AuthenticationResult"]["IdToken"]


def main():
    email = os.environ.get("SF_EMAIL")
    password = os.environ.get("SF_PASSWORD")
    if not email or not password:
        print("請先設定環境變數 SF_EMAIL 與 SF_PASSWORD,再執行本程式。")
        sys.exit(1)

    # 1. 登入
    print(f"[1] 以 {email} 登入 Cognito…")
    id_token = cognito_login(email, password)
    print("    ✅ 取得 IdToken")

    # 2. 現場拍照
    print("[2] 3 秒後拍照,請正對 USB 相機…")
    import time
    time.sleep(3)
    face_path = FaceCamera().capture("register_face.jpg")
    if not face_path:
        print("    ❌ 拍照失敗(相機沒接好?)")
        sys.exit(1)
    with open(face_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    print(f"    ✅ 拍照完成({len(b64)} bytes base64)")

    # 3. 註冊人臉
    print("[3] 上傳註冊 /users/me/face…")
    resp = requests.post(
        f"{config.API_BASE_URL}/users/me/face",
        headers={
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json",
        },
        json={"imageContentType": "image/jpeg", "faceImageBase64": b64},
        timeout=30,
    )
    print(f"    HTTP {resp.status_code}")
    print("    回應:", resp.text[:500])
    if resp.status_code < 300:
        print("\n✅ 人臉註冊成功!現在可以跑 flow_test.py,/auth/face 應該會認得你。")
    else:
        print("\n⚠️ 註冊未成功,請看上面回應訊息。")


if __name__ == "__main__":
    main()
