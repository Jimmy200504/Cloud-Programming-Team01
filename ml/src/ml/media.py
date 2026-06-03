"""Media request normalization and validation."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from ml.errors import MLError, MLErrorCode

SUPPORTED_IMAGE_TYPES = {"local_path", "s3_uri", "bytes_base64"}
SUPPORTED_AUDIO_TYPES = {"local_path", "s3_uri", "bytes_base64", "transcript_text"}


def request_id(request: dict[str, Any]) -> str | None:
    value = request.get("request_id")
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise MLError(MLErrorCode.INVALID_INPUT, "`request_id` must be a non-empty string.")
    return value


def validate_media(
    media: dict[str, Any] | None,
    *,
    field_name: str,
    supported_types: set[str],
) -> dict[str, str]:
    if not isinstance(media, dict):
        raise MLError(MLErrorCode.INVALID_INPUT, f"`{field_name}` must be an object.")

    media_type = media.get("type")
    value = media.get("value")
    if not isinstance(media_type, str) or not isinstance(value, str) or not value:
        raise MLError(
            MLErrorCode.INVALID_INPUT,
            f"`{field_name}.type` and `{field_name}.value` are required strings.",
        )

    if media_type not in supported_types:
        raise MLError(
            MLErrorCode.UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported {field_name} type `{media_type}`.",
            {"supported_types": sorted(supported_types)},
        )

    if media_type == "local_path" and not Path(value).exists():
        raise MLError(
            MLErrorCode.FILE_NOT_FOUND,
            f"{field_name} file does not exist.",
            {"path": value},
        )

    if media_type == "bytes_base64":
        try:
            base64.b64decode(value, validate=True)
        except Exception as exc:
            raise MLError(
                MLErrorCode.INVALID_INPUT,
                f"`{field_name}.value` is not valid base64.",
            ) from exc

    return {"type": media_type, "value": value}

