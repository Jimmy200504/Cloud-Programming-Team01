from __future__ import annotations

import unittest

from ml.config import load_config
from ml.duration_math import expiration_date_from_duration, parse_iso_date_duration
from ml.errors import MLError, MLErrorCode, error_response, success_response
from ml.food_catalog import load_food_catalog


class ConfigErrorsDateTest(unittest.TestCase):
    def test_config_reads_ml_environment(self) -> None:
        config = load_config(
            {
                "ML_AWS_REGION": "ap-northeast-1",
                "ML_REKOGNITION_LABEL_MIN_CONFIDENCE": "55",
                "ML_BEDROCK_FOOD_MIN_CONFIDENCE": "0.6",
                "ML_BEDROCK_DURATION_MIN_CONFIDENCE": "0.75",
                "ML_BEDROCK_MODEL_ID": "jp.anthropic.claude-haiku-4-5-20251001-v1:0",
                "ML_TRANSCRIBE_IDENTIFY_LANGUAGE": "true",
                "ML_TRANSCRIBE_LANGUAGE_OPTIONS": "zh-TW,en-US",
                "ML_TIMEZONE": "Asia/Taipei",
            }
        )

        self.assertEqual(config.aws_region, "ap-northeast-1")
        self.assertEqual(config.rekognition_label_min_confidence, 55)
        self.assertEqual(config.bedrock_food_min_confidence, 0.6)
        self.assertEqual(config.bedrock_duration_min_confidence, 0.75)
        self.assertEqual(config.bedrock_model_id, "jp.anthropic.claude-haiku-4-5-20251001-v1:0")
        self.assertTrue(config.transcribe_identify_language)
        self.assertEqual(config.transcribe_language_options, "zh-TW,en-US")
        self.assertEqual(config.timezone, "Asia/Taipei")

    def test_success_response_shape(self) -> None:
        response = success_response("ml-req-test", {"ok": True})

        self.assertEqual(
            response,
            {
                "request_id": "ml-req-test",
                "status": "success",
                "result": {"ok": True},
            },
        )

    def test_error_response_shape(self) -> None:
        response = error_response(
            "ml-req-test",
            MLErrorCode.INVALID_INPUT,
            "Invalid input.",
            {"field": "image"},
        )

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"]["code"], "ML_INVALID_INPUT")
        self.assertEqual(response["error"]["details"], {"field": "image"})

    def test_iso_duration_date_math(self) -> None:
        captured_at = "2026-06-03T10:30:00+08:00"

        self.assertEqual(
            expiration_date_from_duration(
                "P1D",
                captured_at=captured_at,
                timezone="Asia/Taipei",
            ),
            "2026-06-04",
        )
        self.assertEqual(
            expiration_date_from_duration(
                "P2W",
                captured_at=captured_at,
                timezone="Asia/Taipei",
            ),
            "2026-06-17",
        )
        self.assertEqual(
            expiration_date_from_duration(
                "P2M",
                captured_at=captured_at,
                timezone="Asia/Taipei",
            ),
            "2026-08-03",
        )

    def test_iso_duration_validation(self) -> None:
        duration = parse_iso_date_duration("P3W")

        self.assertEqual(duration.amount, 3)
        self.assertEqual(duration.unit, "weeks")
        self.assertEqual(duration.iso_duration, "P3W")

    def test_invalid_iso_duration_raises_ml_error(self) -> None:
        with self.assertRaises(MLError) as ctx:
            parse_iso_date_duration("next week")

        self.assertEqual(ctx.exception.code, MLErrorCode.AMBIGUOUS_DATE)

    def test_default_food_catalog_loads(self) -> None:
        catalog = load_food_catalog()

        self.assertTrue(any(item["id"] == "soy_milk" for item in catalog))
        self.assertTrue(any(item["id"] == "milk" for item in catalog))


if __name__ == "__main__":
    unittest.main()
