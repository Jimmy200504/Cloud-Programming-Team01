"""AWS-backed ML service implementation."""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
import time
from typing import Any
from uuid import uuid4

from ml.config import MLConfig
from ml.aws_utils import image_arg_from_media, parse_s3_uri
from ml.bedrock_interpreter import BedrockInterpreter
from ml.duration_math import expiration_date_from_duration
from ml.errors import MLError, MLErrorCode
from ml.food_catalog import load_food_catalog


class AWSMLService:
    def __init__(self, config: MLConfig) -> None:
        self.config = config
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except Exception as exc:
            raise MLError(
                MLErrorCode.INVALID_INPUT,
                "boto3 is required. Run `uv sync` in the ml directory.",
            ) from exc

        self._boto_errors = (BotoCoreError, ClientError)
        self._rekognition = boto3.client("rekognition", region_name=config.aws_region)
        self._s3 = boto3.client("s3", region_name=config.aws_region)
        self._transcribe = boto3.client("transcribe", region_name=config.aws_region)
        self._bedrock = boto3.client("bedrock-runtime", region_name=config.aws_region)
        self._face_user_map = _load_face_user_map(config.face_user_map_json)
        self._interpreter = BedrockInterpreter(
            client=self._bedrock,
            model_id=config.bedrock_model_id,
            food_catalog=load_food_catalog(config.food_catalog_path),
            duration_min_confidence=config.bedrock_duration_min_confidence,
            food_min_confidence=config.bedrock_food_min_confidence,
        )

    def authenticate_face(
        self,
        image: dict[str, str],
        *,
        expected_user_id: str | None = None,
    ) -> dict[str, Any]:
        try:
            response = self._rekognition.search_faces_by_image(
                CollectionId=self.config.face_collection_id,
                Image=image_arg_from_media(image),
                FaceMatchThreshold=self.config.face_min_confidence,
                MaxFaces=1,
            )
        except self._boto_errors as exc:
            raise _aws_error(exc) from exc

        matches = response.get("FaceMatches", [])
        if not matches:
            return {
                "authenticated": False,
                "user_id": None,
                "confidence": 0,
                "matched_face_id": None,
                "collection_id": self.config.face_collection_id,
            }

        match = matches[0]
        face = match.get("Face", {})
        face_id = face.get("FaceId")
        external_image_id = face.get("ExternalImageId")
        user_id = self._face_user_map.get(face_id) or external_image_id or face_id
        confidence = float(match.get("Similarity", 0))

        authenticated = confidence >= self.config.face_min_confidence
        if expected_user_id is not None:
            authenticated = authenticated and user_id == expected_user_id

        return {
            "authenticated": authenticated,
            "user_id": user_id if authenticated else None,
            "confidence": confidence,
            "matched_face_id": face_id,
            "collection_id": self.config.face_collection_id,
        }

    def detect_food(self, image: dict[str, str], *, min_confidence: float | None = None) -> dict[str, Any]:
        threshold = (
            min_confidence
            if min_confidence is not None
            else self.config.rekognition_label_min_confidence
        )
        try:
            response = self._rekognition.detect_labels(
                Image=image_arg_from_media(image),
                MaxLabels=10,
                MinConfidence=threshold,
            )
        except self._boto_errors as exc:
            raise _aws_error(exc) from exc

        candidates = [
            {
                "label": _normalize_label(label["Name"]),
                "confidence": float(label["Confidence"]),
            }
            for label in response.get("Labels", [])
        ]
        classification = self._interpreter.classify_food(
            image=image,
            rekognition_labels=candidates,
        )

        return {
            **classification,
            "model": self.config.bedrock_model_id,
            "rekognition_candidates": candidates,
        }

    def parse_expiration_date(
        self,
        audio: dict[str, str],
        *,
        captured_at: str | None,
        timezone: str,
    ) -> dict[str, Any]:
        if audio["type"] == "transcript_text":
            transcript = audio["value"]
        else:
            transcript = self._transcribe_audio(audio)

        duration = self._interpreter.normalize_duration(transcript)
        expiration_date = expiration_date_from_duration(
            duration["duration"],
            captured_at=captured_at,
            timezone=timezone,
        )
        return {
            "expiration_date": expiration_date,
            "expiration_duration": duration["duration"],
            "expiration_duration_unit": duration["unit"],
            "expiration_duration_amount": duration["amount"],
            "transcript": transcript,
            "confidence": duration["confidence"],
            "reason": duration["reason"],
            "timezone": timezone,
        }

    def _transcribe_audio(self, audio: dict[str, str]) -> str:
        media_uri = self._ensure_s3_audio(audio)
        job_name = f"ml-expiration-{uuid4().hex}"
        output_key = f"transcribe/{job_name}.json"

        try:
            self._transcribe.start_transcription_job(
                **self._transcription_job_request(
                    job_name=job_name,
                    media_uri=media_uri,
                    output_key=output_key,
                )
            )
            deadline = time.monotonic() + self.config.transcribe_timeout_seconds
            while time.monotonic() < deadline:
                job = self._transcribe.get_transcription_job(
                    TranscriptionJobName=job_name
                )["TranscriptionJob"]
                status = job["TranscriptionJobStatus"]
                if status == "COMPLETED":
                    return self._read_transcript_output(output_key)
                if status == "FAILED":
                    raise MLError(
                        MLErrorCode.TRANSCRIBE_FAILED,
                        "Transcribe job failed.",
                        {"job_name": job_name, "reason": job.get("FailureReason")},
                    )
                time.sleep(self.config.transcribe_poll_seconds)
        except MLError:
            raise
        except self._boto_errors as exc:
            raise _aws_error(exc) from exc

        raise MLError(
            MLErrorCode.TRANSCRIBE_FAILED,
            "Transcribe job timed out.",
            {"job_name": job_name, "timeout_seconds": self.config.transcribe_timeout_seconds},
        )

    def _ensure_s3_audio(self, audio: dict[str, str]) -> str:
        if audio["type"] == "s3_uri":
            return audio["value"]

        key = f"audio/{uuid4().hex}"
        body: bytes
        content_type: str | None = None
        if audio["type"] == "local_path":
            path = Path(audio["value"])
            key = f"{key}{path.suffix}"
            body = path.read_bytes()
            content_type = mimetypes.guess_type(path.name)[0]
        elif audio["type"] == "bytes_base64":
            body = base64.b64decode(audio["value"])
            key = f"{key}.wav"
            content_type = "audio/wav"
        else:
            raise MLError(
                MLErrorCode.UNSUPPORTED_MEDIA_TYPE,
                f"Audio type `{audio['type']}` cannot be sent to Transcribe.",
            )

        put_args: dict[str, Any] = {
            "Bucket": self.config.s3_bucket,
            "Key": key,
            "Body": body,
        }
        if content_type:
            put_args["ContentType"] = content_type

        try:
            self._s3.put_object(**put_args)
        except self._boto_errors as exc:
            raise _aws_error(exc) from exc

        return f"s3://{self.config.s3_bucket}/{key}"

    def _transcription_job_request(
        self,
        *,
        job_name: str,
        media_uri: str,
        output_key: str,
    ) -> dict[str, Any]:
        request: dict[str, Any] = {
            "TranscriptionJobName": job_name,
            "Media": {"MediaFileUri": media_uri},
            "OutputBucketName": self.config.s3_bucket,
            "OutputKey": output_key,
        }
        media_format = _media_format_from_uri(media_uri)
        if media_format:
            request["MediaFormat"] = media_format

        if self.config.transcribe_identify_language:
            request["IdentifyLanguage"] = True
            options = [
                option.strip()
                for option in self.config.transcribe_language_options.split(",")
                if option.strip()
            ]
            if options:
                request["LanguageOptions"] = options
        else:
            request["LanguageCode"] = self.config.transcribe_language_code

        return request

    def _read_transcript_output(self, output_key: str) -> str:
        try:
            obj = self._s3.get_object(Bucket=self.config.s3_bucket, Key=output_key)
            payload = json.loads(obj["Body"].read().decode("utf-8"))
        except self._boto_errors as exc:
            raise _aws_error(exc) from exc

        transcripts = payload.get("results", {}).get("transcripts", [])
        if not transcripts:
            raise MLError(
                MLErrorCode.TRANSCRIBE_FAILED,
                "Transcribe output did not include transcript text.",
                {"output_key": output_key},
            )
        return transcripts[0].get("transcript", "")


def _normalize_label(label: str) -> str:
    return label.strip().lower().replace(" ", "_")


def _media_format_from_uri(media_uri: str) -> str | None:
    suffix = Path(media_uri).suffix.lower().lstrip(".")
    if suffix in {"mp3", "mp4", "wav", "flac", "ogg", "amr", "webm", "m4a"}:
        return suffix
    return None


def _load_face_user_map(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MLError(MLErrorCode.INVALID_INPUT, "ML_FACE_USER_MAP_JSON must point to a JSON object.")
    return {str(key): str(value) for key, value in payload.items()}


def _aws_error(exc: Exception) -> MLError:
    code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
    message = getattr(exc, "response", {}).get("Error", {}).get("Message", str(exc))
    if code in {"AccessDeniedException", "AccessDenied", "UnauthorizedOperation"}:
        return MLError(
            MLErrorCode.AWS_PERMISSION_DENIED,
            "AWS permission denied.",
            {"aws_code": code, "aws_message": message},
        )
    return MLError(
        MLErrorCode.AWS_SERVICE_ERROR,
        "AWS service error.",
        {"aws_code": code, "aws_message": message},
    )
