"""Bedrock-backed interpretation for durations and food classification."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from ml.aws_utils import parse_s3_uri
from ml.duration_math import parse_iso_date_duration
from ml.errors import MLError, MLErrorCode
from ml.food_catalog import catalog_ids


class BedrockInterpreter:
    def __init__(
        self,
        *,
        client: Any,
        model_id: str,
        food_catalog: list[dict[str, Any]],
        duration_min_confidence: float,
        food_min_confidence: float,
    ) -> None:
        self._client = client
        self._model_id = model_id
        self._food_catalog = food_catalog
        self._duration_min_confidence = duration_min_confidence
        self._food_min_confidence = food_min_confidence

    def normalize_duration(self, transcript: str) -> dict[str, Any]:
        response = self._converse_text(
            system=(
                "You convert spoken expiration duration text into strict JSON. "
                "The user may speak Traditional Chinese, Simplified Chinese, or English. "
                "Return one JSON object only. No markdown. No extra text. "
                "Only accept relative duration expressions, not calendar dates. "
                "Supported units are days, weeks, and months. "
                "The `duration` field must be ISO-8601 date duration: PnD, PnW, or PnM. "
                "If the text is not a clear duration, return duration null and confidence 0."
            ),
            user_text=(
                "Transcript:\n"
                f"{transcript}\n\n"
                "Return JSON with this schema:\n"
                "{"
                "\"duration\": string|null, "
                "\"amount\": integer|null, "
                "\"unit\": \"days\"|\"weeks\"|\"months\"|null, "
                "\"confidence\": number, "
                "\"reason\": string"
                "}"
            ),
        )
        data = _json_object(response)
        duration = data.get("duration")
        confidence = _confidence(data)
        if not isinstance(duration, str):
            raise MLError(
                MLErrorCode.AMBIGUOUS_DATE,
                "Bedrock could not normalize the spoken expiration duration.",
                {"transcript": transcript, "bedrock": data},
            )
        parsed = parse_iso_date_duration(duration)
        if confidence < self._duration_min_confidence:
            raise MLError(
                MLErrorCode.LOW_CONFIDENCE,
                "Bedrock duration confidence is below threshold.",
                {"threshold": self._duration_min_confidence, "bedrock": data},
            )
        unit = data.get("unit")
        amount = data.get("amount")
        if unit != parsed.unit or int(amount) != parsed.amount:
            raise MLError(
                MLErrorCode.AMBIGUOUS_DATE,
                "Bedrock duration fields are internally inconsistent.",
                {"duration": duration, "amount": amount, "unit": unit},
            )
        return {
            "duration": parsed.iso_duration,
            "amount": parsed.amount,
            "unit": parsed.unit,
            "confidence": confidence,
            "reason": str(data.get("reason", "")),
        }

    def classify_food(
        self,
        *,
        image: dict[str, str],
        rekognition_labels: list[dict[str, Any]],
    ) -> dict[str, Any]:
        catalog_json = json.dumps(self._food_catalog, ensure_ascii=False)
        labels_json = json.dumps(rekognition_labels, ensure_ascii=False)
        response = self._converse_with_image(
            image=image,
            system=(
                "You classify the main food item being stored in a smart refrigerator. "
                "Use the image as primary evidence. Use Rekognition labels as supporting evidence. "
                "Ignore people, hands, background, fridge parts, table, and generic container-only labels "
                "unless they help identify the food. Choose exactly one item from the food catalog. "
                "If no catalog item is plausible, return food_id null and confidence 0. "
                "Return one JSON object only. No markdown. No extra text."
            ),
            user_text=(
                "Food catalog JSON:\n"
                f"{catalog_json}\n\n"
                "Rekognition labels JSON:\n"
                f"{labels_json}\n\n"
                "Return JSON with this schema:\n"
                "{"
                "\"food_id\": string|null, "
                "\"display_name\": string|null, "
                "\"confidence\": number, "
                "\"reason\": string"
                "}"
            ),
        )
        data = _json_object(response)
        food_id = data.get("food_id")
        confidence = _confidence(data)
        if not isinstance(food_id, str) or food_id not in catalog_ids(self._food_catalog):
            raise MLError(
                MLErrorCode.NO_FOOD_DETECTED,
                "Bedrock did not classify the image into a catalog food item.",
                {"bedrock": data, "rekognition_labels": rekognition_labels},
            )
        if confidence < self._food_min_confidence:
            raise MLError(
                MLErrorCode.LOW_CONFIDENCE,
                "Bedrock food classification confidence is below threshold.",
                {"threshold": self._food_min_confidence, "bedrock": data},
            )
        catalog_item = next(item for item in self._food_catalog if item["id"] == food_id)
        return {
            "food_id": food_id,
            "food_name": food_id,
            "display_name": str(data.get("display_name") or catalog_item.get("display_name") or food_id),
            "confidence": confidence,
            "matched_catalog_id": food_id,
            "reason": str(data.get("reason", "")),
        }

    def _converse_text(self, *, system: str, user_text: str) -> str:
        try:
            response = self._client.converse(
                modelId=self._model_id,
                system=[{"text": system}],
                messages=[{"role": "user", "content": [{"text": user_text}]}],
                inferenceConfig={"maxTokens": 512, "temperature": 0},
            )
        except Exception as exc:
            raise _bedrock_error(exc) from exc
        return _response_text(response)

    def _converse_with_image(self, *, image: dict[str, str], system: str, user_text: str) -> str:
        try:
            response = self._client.converse(
                modelId=self._model_id,
                system=[{"text": system}],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            _image_content_block(image),
                            {"text": user_text},
                        ],
                    }
                ],
                inferenceConfig={"maxTokens": 768, "temperature": 0},
            )
        except Exception as exc:
            raise _bedrock_error(exc) from exc
        return _response_text(response)


def _response_text(response: dict[str, Any]) -> str:
    content = response.get("output", {}).get("message", {}).get("content", [])
    texts = [block.get("text", "") for block in content if isinstance(block, dict)]
    return "\n".join(text for text in texts if text)


def _json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise MLError(MLErrorCode.AWS_SERVICE_ERROR, "Bedrock returned an empty response.")
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if not match:
            raise MLError(
                MLErrorCode.AWS_SERVICE_ERROR,
                "Bedrock response did not contain a JSON object.",
                {"response": text},
            )
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise MLError(MLErrorCode.AWS_SERVICE_ERROR, "Bedrock response JSON must be an object.")
    return value


def _confidence(data: dict[str, Any]) -> float:
    value = data.get("confidence")
    if not isinstance(value, int | float):
        raise MLError(
            MLErrorCode.AWS_SERVICE_ERROR,
            "Bedrock response must include numeric confidence.",
            {"bedrock": data},
        )
    confidence = float(value)
    if not 0 <= confidence <= 1:
        raise MLError(
            MLErrorCode.AWS_SERVICE_ERROR,
            "Bedrock confidence must be between 0 and 1.",
            {"confidence": confidence},
        )
    return confidence


def _image_content_block(image: dict[str, str]) -> dict[str, Any]:
    if image["type"] == "local_path":
        path = Path(image["value"])
        return {
            "image": {
                "format": _image_format(path.suffix),
                "source": {"bytes": path.read_bytes()},
            }
        }
    if image["type"] == "bytes_base64":
        import base64

        return {
            "image": {
                "format": "jpeg",
                "source": {"bytes": base64.b64decode(image["value"])},
            }
        }
    if image["type"] == "s3_uri":
        parse_s3_uri(image["value"])
        return {
            "image": {
                "format": _image_format(Path(image["value"]).suffix),
                "source": {"s3Location": {"uri": image["value"]}},
            }
        }
    raise MLError(
        MLErrorCode.UNSUPPORTED_MEDIA_TYPE,
        f"Image type `{image['type']}` cannot be sent to Bedrock.",
    )


def _image_format(suffix: str) -> str:
    value = suffix.lower().lstrip(".")
    if value == "jpg":
        return "jpeg"
    if value in {"jpeg", "png", "gif", "webp"}:
        return value
    raise MLError(
        MLErrorCode.UNSUPPORTED_MEDIA_TYPE,
        "Bedrock image classification requires jpeg, png, gif, or webp.",
        {"suffix": suffix},
    )


def _bedrock_error(exc: Exception) -> MLError:
    response = getattr(exc, "response", {})
    error = response.get("Error", {}) if isinstance(response, dict) else {}
    code = error.get("Code", "")
    message = error.get("Message", str(exc))
    if code in {"AccessDeniedException", "AccessDenied", "UnauthorizedOperation"}:
        return MLError(
            MLErrorCode.AWS_PERMISSION_DENIED,
            "Bedrock permission denied or model access is not enabled.",
            {"aws_code": code, "aws_message": message},
        )
    return MLError(
        MLErrorCode.AWS_SERVICE_ERROR,
        "Bedrock service error.",
        {"aws_code": code, "aws_message": message},
    )
