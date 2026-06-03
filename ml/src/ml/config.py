"""Configuration helpers for ML integration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MLConfig:
    aws_region: str = "ap-northeast-1"
    face_collection_id: str = "ml-smart-fridge-faces"
    face_min_confidence: float = 85.0
    rekognition_label_min_confidence: float = 50.0
    transcribe_language_code: str = "zh-TW"
    transcribe_identify_language: bool = True
    transcribe_language_options: str = "zh-TW,en-US"
    s3_bucket: str = "ml-smart-fridge-media-491919374787-ap-northeast-1-an"
    timezone: str = "Asia/Taipei"
    bedrock_model_id: str = "jp.anthropic.claude-haiku-4-5-20251001-v1:0"
    bedrock_duration_min_confidence: float = 0.7
    bedrock_food_min_confidence: float = 0.55
    food_catalog_path: str | None = None
    transcribe_poll_seconds: float = 2.0
    transcribe_timeout_seconds: float = 180.0
    face_user_map_json: str | None = None


def load_config(env: dict[str, str] | None = None) -> MLConfig:
    source = env if env is not None else os.environ
    return MLConfig(
        aws_region=source.get("ML_AWS_REGION", MLConfig.aws_region),
        face_collection_id=source.get(
            "ML_REKOGNITION_FACE_COLLECTION_ID",
            MLConfig.face_collection_id,
        ),
        face_min_confidence=float(
            source.get("ML_FACE_MIN_CONFIDENCE", MLConfig.face_min_confidence)
        ),
        rekognition_label_min_confidence=float(
            source.get(
                "ML_REKOGNITION_LABEL_MIN_CONFIDENCE",
                MLConfig.rekognition_label_min_confidence,
            )
        ),
        transcribe_language_code=source.get(
            "ML_TRANSCRIBE_LANGUAGE_CODE",
            MLConfig.transcribe_language_code,
        ),
        transcribe_identify_language=_bool_env(
            source.get("ML_TRANSCRIBE_IDENTIFY_LANGUAGE"),
            MLConfig.transcribe_identify_language,
        ),
        transcribe_language_options=source.get(
            "ML_TRANSCRIBE_LANGUAGE_OPTIONS",
            MLConfig.transcribe_language_options,
        ),
        s3_bucket=source.get("ML_S3_BUCKET", MLConfig.s3_bucket),
        timezone=source.get("ML_TIMEZONE", MLConfig.timezone),
        bedrock_model_id=source.get("ML_BEDROCK_MODEL_ID", MLConfig.bedrock_model_id),
        bedrock_duration_min_confidence=float(
            source.get(
                "ML_BEDROCK_DURATION_MIN_CONFIDENCE",
                MLConfig.bedrock_duration_min_confidence,
            )
        ),
        bedrock_food_min_confidence=float(
            source.get(
                "ML_BEDROCK_FOOD_MIN_CONFIDENCE",
                MLConfig.bedrock_food_min_confidence,
            )
        ),
        food_catalog_path=source.get("ML_FOOD_CATALOG_PATH"),
        transcribe_poll_seconds=float(
            source.get("ML_TRANSCRIBE_POLL_SECONDS", MLConfig.transcribe_poll_seconds)
        ),
        transcribe_timeout_seconds=float(
            source.get(
                "ML_TRANSCRIBE_TIMEOUT_SECONDS",
                MLConfig.transcribe_timeout_seconds,
            )
        ),
        face_user_map_json=source.get("ML_FACE_USER_MAP_JSON"),
    )


def _bool_env(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
