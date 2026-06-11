# -*- coding: utf-8 -*-
"""
雲端 REST API 用戶端 (cloud_api.py)
============================================================
依據 aws-backend/docs/hardware-embedded-integration-guide.md 的契約,
封裝對 API Gateway 的呼叫:
  - 人臉認證       POST /auth/face
  - 放食物         POST /foods/put
  - 取食物         POST /foods/retrieve
  - 解析到期日語音  POST /expiration/parse

⚠️ 兩條雲端管道要分清楚:
   - 「業務事件」(影像/音訊/食物紀錄) → 走本檔的 API Gateway(HTTPS+JSON)
   - 「裝置狀態/硬體指令」(鎖、LED、溫濕度) → 走 IoT Device Shadow,見 aws_iot/

影像與音訊一律轉成「純 base64 字串」放進 JSON,不能有 data URL 前綴。
這些測試路由不需要 AWS 憑證,所以憑證還沒到位前就能先測。
"""

import base64
from datetime import datetime, timezone, timedelta
import config

# 只有在實機模式才匯入 requests,Mock 模式不需要(也不會真的發出請求)。
if not config.MOCK_MODE:
    import requests


# 台北時區 (+08:00),用於組 capturedAt 時間戳
_TZ = timezone(timedelta(hours=8))


def _now_iso() -> str:
    """回傳含時區的 ISO8601 時間字串,例如 2026-06-05T03:30:00+08:00。"""
    return datetime.now(_TZ).isoformat(timespec="seconds")


class CloudAPIClient:
    """API Gateway 用戶端。"""

    def __init__(self, base_url: str = config.API_BASE_URL,
                 device_id: str = config.DEVICE_ID,
                 timezone_name: str = config.TIMEZONE,
                 timeout: int = config.API_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.device_id = device_id
        self.timezone_name = timezone_name
        self.timeout = timeout

    # ------------------------------------------------------------
    #  共用工具
    # ------------------------------------------------------------
    @staticmethod
    def file_to_base64(path: str) -> str:
        """把檔案讀成純 base64 字串(無 data URL 前綴)。"""
        if config.MOCK_MODE:
            # Mock 模式:相機/麥克風沒真的存檔,回傳假字串避免開檔失敗
            return "MOCK_BASE64_DATA"
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _post(self, route: str, payload: dict) -> dict:
        """對指定路由發 POST,回傳解析後的 JSON。"""
        url = f"{self.base_url}{route}"

        # ---- 模擬模式:不真的發請求,回傳與契約一致的假資料 ----
        if config.MOCK_MODE:
            print(f"[Mock] POST {url}  (payload keys={list(payload.keys())})")
            return self._mock_response(route)

        # ---- 實機模式:實際呼叫 API Gateway ----
        resp = requests.post(
            url, json=payload, timeout=self.timeout,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _mock_response(route: str) -> dict:
        """Mock 模式回傳的假回應,結構比照契約,方便無雲端時測整段流程。"""
        if route == "/auth/face":
            return {"authenticated": True,
                    "user": {"userId": "mock-user-id",
                             "email": "owner@example.com",
                             "displayName": "Mock Owner"},
                    "confidence": 99.0}
        if route == "/foods/put":
            return {"success": True, "foodId": "mock-food-id"}
        if route == "/foods/retrieve":
            return {"success": True, "authorized": True,
                    "deletedFoodId": "mock-food-id",
                    "message": "Mock Owner took mock food"}
        if route == "/expiration/parse":
            return {"success": True,
                    "expiration": {"expirationDate": "2026-09-04",
                                   "expirationDuration": "P3M",
                                   "transcript": "三個月後"}}
        if route.endswith("/climate-alert"):
            return {"success": True, "alertSent": True, "mock": True}
        return {"success": True}

    # ------------------------------------------------------------
    #  契約端點
    # ------------------------------------------------------------
    def auth_face(self, face_image_path: str, action: str,
                  image_content_type: str = "image/jpeg") -> dict:
        """
        人臉認證。

        :param action: "put"(放食物流程)或 "retrieve"(取食物流程)
        :return: {"authenticated": bool, "user": {...}, "confidence": float}
        """
        payload = {
            "action": action,
            "deviceId": self.device_id,
            "imageContentType": image_content_type,
            "faceImageBase64": self.file_to_base64(face_image_path),
        }
        return self._post("/auth/face", payload)

    def put_food(self, food_image_path: str, user_id: str, owner_email: str,
                 owner_user_id: str = None, audio_path: str = None,
                 expiration_transcript: str = None,
                 image_content_type: str = "image/jpeg",
                 audio_content_type: str = "audio/wav") -> dict:
        """
        放食物:送食物照片(必填)+ 到期日語音或文字(擇一)。
        後端會辨識食物、轉錄+解析到期日、寫入 DynamoDB、存圖到 S3。
        """
        payload = {
            "deviceId": self.device_id,
            "userId": user_id,
            "ownerUserId": owner_user_id or user_id,
            "ownerEmail": owner_email,
            "foodImageContentType": image_content_type,
            "foodImageBase64": self.file_to_base64(food_image_path),
            "capturedAt": _now_iso(),
            "timezone": self.timezone_name,
            "recordType": "put-flow",
        }
        # 到期日:若有文字轉錄,後端優先採用文字;否則送音訊
        if expiration_transcript:
            payload["expirationTranscript"] = expiration_transcript
        if audio_path:
            payload["audioContentType"] = audio_content_type
            payload["expirationAudioBase64"] = self.file_to_base64(audio_path)
        return self._post("/foods/put", payload)

    def retrieve_food(self, food_image_path: str, actor_user_id: str,
                      actor_email: str, actor_display_name: str = None,
                      image_content_type: str = "image/jpeg") -> dict:
        """
        取食物:送取用者與食物照片。
        :return: 內含 "authorized" 布林;為 True 才可開鎖。
                 為 False 時後端會在 hardwareActions 要求警示(並透過 Shadow 下 led=alert)。
        """
        payload = {
            "deviceId": self.device_id,
            "actorUserId": actor_user_id,
            "actorEmail": actor_email,
            "userId": actor_user_id,
            "actorDisplayName": actor_display_name or "",
            "foodImageContentType": image_content_type,
            "foodImageBase64": self.file_to_base64(food_image_path),
        }
        return self._post("/foods/retrieve", payload)

    def parse_expiration(self, audio_path: str,
                         audio_content_type: str = "audio/wav") -> dict:
        """
        單獨解析到期日語音(例如「三個月後」→ 2026-09-04)。
        :return: {"success": bool, "expiration": {"expirationDate": "...", ...}}
        """
        payload = {
            "audioContentType": audio_content_type,
            "expirationAudioBase64": self.file_to_base64(audio_path),
            "capturedAt": _now_iso(),
            "timezone": self.timezone_name,
        }
        return self._post("/expiration/parse", payload)

    def send_climate_alert(self, temperature, humidity, captured_at: str = None) -> dict:
        """
        溫濕度超標警報:通知後端寄信給所有已知 user。
        實際是否寄出由後端根據門檻與 SES 狀態判斷。
        """
        payload = {
            "deviceId": self.device_id,
            "temperature": temperature,
            "humidity": humidity,
            "capturedAt": captured_at or _now_iso(),
            "timezone": self.timezone_name,
        }
        return self._post(f"/device/{self.device_id}/climate-alert", payload)
