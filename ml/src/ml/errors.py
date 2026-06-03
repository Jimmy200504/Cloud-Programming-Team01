"""Shared ML error handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class MLErrorCode(StrEnum):
    INVALID_INPUT = "ML_INVALID_INPUT"
    FILE_NOT_FOUND = "ML_FILE_NOT_FOUND"
    UNSUPPORTED_MEDIA_TYPE = "ML_UNSUPPORTED_MEDIA_TYPE"
    AWS_PERMISSION_DENIED = "ML_AWS_PERMISSION_DENIED"
    AWS_NETWORK_ERROR = "ML_AWS_NETWORK_ERROR"
    AWS_SERVICE_ERROR = "ML_AWS_SERVICE_ERROR"
    LOW_CONFIDENCE = "ML_LOW_CONFIDENCE"
    NO_FACE_DETECTED = "ML_NO_FACE_DETECTED"
    MULTIPLE_FACES_DETECTED = "ML_MULTIPLE_FACES_DETECTED"
    UNKNOWN_FACE = "ML_UNKNOWN_FACE"
    NO_FOOD_DETECTED = "ML_NO_FOOD_DETECTED"
    TRANSCRIBE_FAILED = "ML_TRANSCRIBE_FAILED"
    AMBIGUOUS_DATE = "ML_AMBIGUOUS_DATE"
    INTERNAL_ERROR = "ML_INTERNAL_ERROR"


@dataclass(frozen=True)
class MLError(Exception):
    code: MLErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)


def error_response(
    request_id: str | None,
    code: MLErrorCode,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "status": "error",
        "error": {
            "code": code.value,
            "message": message,
            "details": details or {},
        },
    }


def success_response(request_id: str | None, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "status": "success",
        "result": result,
    }

