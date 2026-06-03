"""Contract-compatible public functions."""

from __future__ import annotations

from typing import Any

from ml.config import load_config
from ml.aws_service import AWSMLService
from ml.errors import MLError, MLErrorCode, error_response, success_response
from ml.media import (
    SUPPORTED_AUDIO_TYPES,
    SUPPORTED_IMAGE_TYPES,
    request_id,
    validate_media,
)


def ml_authenticate_face(request: dict[str, Any]) -> dict[str, Any]:
    req_id = _safe_request_id(request)
    try:
        req_id = request_id(request)
        config = load_config()
        service = _service(config)
        image = validate_media(
            request.get("image"),
            field_name="image",
            supported_types=SUPPORTED_IMAGE_TYPES,
        )
        expected_user_id = request.get("expected_user_id")
        if expected_user_id is not None and not isinstance(expected_user_id, str):
            raise MLError(MLErrorCode.INVALID_INPUT, "`expected_user_id` must be null or string.")
        return success_response(
            req_id,
            service.authenticate_face(image, expected_user_id=expected_user_id),
        )
    except MLError as exc:
        return error_response(req_id, exc.code, exc.message, exc.details)


def ml_detect_food(request: dict[str, Any]) -> dict[str, Any]:
    req_id = _safe_request_id(request)
    try:
        req_id = request_id(request)
        config = load_config()
        service = _service(config)
        image = validate_media(
            request.get("image"),
            field_name="image",
            supported_types=SUPPORTED_IMAGE_TYPES,
        )
        min_confidence = request.get("min_confidence")
        if min_confidence is not None and not isinstance(min_confidence, int | float):
            raise MLError(MLErrorCode.INVALID_INPUT, "`min_confidence` must be numeric.")
        return success_response(
            req_id,
            service.detect_food(image, min_confidence=min_confidence),
        )
    except MLError as exc:
        return error_response(req_id, exc.code, exc.message, exc.details)


def ml_parse_expiration_date(request: dict[str, Any]) -> dict[str, Any]:
    req_id = _safe_request_id(request)
    try:
        req_id = request_id(request)
        config = load_config()
        service = _service(config)
        timezone = request.get("timezone") or config.timezone
        if not isinstance(timezone, str):
            raise MLError(MLErrorCode.INVALID_INPUT, "`timezone` must be a string.")
        captured_at = request.get("captured_at")
        if captured_at is not None and not isinstance(captured_at, str):
            raise MLError(MLErrorCode.INVALID_INPUT, "`captured_at` must be null or string.")
        audio = validate_media(
            request.get("audio"),
            field_name="audio",
            supported_types=SUPPORTED_AUDIO_TYPES,
        )
        return success_response(
            req_id,
            service.parse_expiration_date(
                audio,
                captured_at=captured_at,
                timezone=timezone,
            ),
        )
    except MLError as exc:
        return error_response(req_id, exc.code, exc.message, exc.details)


def ml_process_put_food(request: dict[str, Any]) -> dict[str, Any]:
    req_id = _safe_request_id(request)
    try:
        req_id = request_id(request)
        user_id = request.get("user_id")
        if not isinstance(user_id, str) or not user_id:
            raise MLError(MLErrorCode.INVALID_INPUT, "`user_id` must be a non-empty string.")

        food_response = ml_detect_food(
            {
                "request_id": req_id,
                "device_id": request.get("device_id"),
                "image": request.get("food_image"),
                "min_confidence": request.get("min_confidence"),
            }
        )
        if food_response["status"] != "success":
            return food_response

        expiration_response = ml_parse_expiration_date(
            {
                "request_id": req_id,
                "device_id": request.get("device_id"),
                "timezone": request.get("timezone"),
                "captured_at": request.get("captured_at"),
                "audio": request.get("expiration_audio"),
            }
        )
        if expiration_response["status"] != "success":
            return expiration_response

        food = food_response["result"]
        expiration = expiration_response["result"]
        return success_response(
            req_id,
            {
                "user_id": user_id,
                "food_name": food["food_name"],
                "food_confidence": food["confidence"],
                "expiration_date": expiration["expiration_date"],
                "expiration_duration": expiration["expiration_duration"],
                "expiration_transcript": expiration["transcript"],
            },
        )
    except MLError as exc:
        return error_response(req_id, exc.code, exc.message, exc.details)


def ml_process_retrieve_food(request: dict[str, Any]) -> dict[str, Any]:
    req_id = _safe_request_id(request)
    try:
        req_id = request_id(request)
        user_id = request.get("user_id")
        if not isinstance(user_id, str) or not user_id:
            raise MLError(MLErrorCode.INVALID_INPUT, "`user_id` must be a non-empty string.")

        food_response = ml_detect_food(
            {
                "request_id": req_id,
                "device_id": request.get("device_id"),
                "image": request.get("food_image"),
                "min_confidence": request.get("min_confidence"),
            }
        )
        if food_response["status"] != "success":
            return food_response

        food = food_response["result"]
        return success_response(
            req_id,
            {
                "user_id": user_id,
                "food_name": food["food_name"],
                "food_confidence": food["confidence"],
            },
        )
    except MLError as exc:
        return error_response(req_id, exc.code, exc.message, exc.details)


def _service(config: Any) -> AWSMLService:
    return AWSMLService(config)


def _safe_request_id(request: dict[str, Any]) -> str | None:
    if isinstance(request, dict) and isinstance(request.get("request_id"), str):
        return request["request_id"]
    return None
