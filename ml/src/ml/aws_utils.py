"""Small AWS utility helpers used by scripts."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from ml.errors import MLError, MLErrorCode


def image_arg_from_path(path: str) -> dict[str, Any]:
    value = Path(path)
    if not value.exists():
        raise MLError(
            MLErrorCode.FILE_NOT_FOUND,
            "Image file does not exist.",
            {"path": path},
        )
    return {"Bytes": value.read_bytes()}


def image_arg_from_media(media: dict[str, str]) -> dict[str, Any]:
    if media["type"] == "local_path":
        return image_arg_from_path(media["value"])
    if media["type"] == "bytes_base64":
        return {"Bytes": base64.b64decode(media["value"])}
    if media["type"] == "s3_uri":
        bucket, key = parse_s3_uri(media["value"])
        return {"S3Object": {"Bucket": bucket, "Name": key}}
    raise MLError(
        MLErrorCode.UNSUPPORTED_MEDIA_TYPE,
        f"Image type `{media['type']}` cannot be sent to Rekognition.",
    )


def parse_s3_uri(value: str) -> tuple[str, str]:
    if not value.startswith("s3://"):
        raise MLError(MLErrorCode.INVALID_INPUT, "S3 URI must start with `s3://`.")
    bucket_and_key = value[5:]
    bucket, _, key = bucket_and_key.partition("/")
    if not bucket or not key:
        raise MLError(MLErrorCode.INVALID_INPUT, "S3 URI must include bucket and key.")
    return bucket, key

