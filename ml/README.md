# ML Package

This package implements the ML-owned smart refrigerator integration.

Current status:

- Contract-compatible public functions backed by AWS.
- Rekognition face auth.
- Rekognition food labels.
- S3 + Transcribe expiration-duration audio processing.
- Unit tests for pure Python logic.
- uv-managed Python environment.

## Install

```bash
cd ml
uv sync
```

## Configure

```bash
export AWS_PROFILE=default
export ML_AWS_REGION=ap-northeast-1
export ML_S3_BUCKET=ml-smart-fridge-media-491919374787-ap-northeast-1-an
export ML_REKOGNITION_FACE_COLLECTION_ID=ml-smart-fridge-faces
export ML_FACE_MIN_CONFIDENCE=85
export ML_REKOGNITION_LABEL_MIN_CONFIDENCE=50
export ML_BEDROCK_MODEL_ID=jp.anthropic.claude-haiku-4-5-20251001-v1:0
export ML_BEDROCK_DURATION_MIN_CONFIDENCE=0.7
export ML_BEDROCK_FOOD_MIN_CONFIDENCE=0.55
export ML_TRANSCRIBE_LANGUAGE_CODE=zh-TW
export ML_TRANSCRIBE_IDENTIFY_LANGUAGE=true
export ML_TRANSCRIBE_LANGUAGE_OPTIONS=zh-TW,en-US
export ML_TIMEZONE=Asia/Taipei
```

## Run Local Logic Tests

```bash
cd ml
uv run python -m unittest discover -s tests/unit
```

## Check AWS

```bash
cd ml
uv run python scripts/ml_check_aws.py --create-collection
```

## Register Face

```bash
cd ml
uv run python scripts/ml_register_face.py \
  --user-id roger \
  --image tests/fixtures/images/register_face.jpg
```

## Run AWS Smoke Test

```bash
cd ml
uv run python scripts/ml_pi_smoke_test.py \
  --face-image tests/fixtures/images/test_face.jpg \
  --food-image tests/fixtures/images/soy_milk.jpg \
  --expiration-audio tests/fixtures/audio/2-month-later.m4a \
  --expected-user-id roger \
  --captured-at 2026-06-03T10:30:00+08:00
```

The smoke test prints `[START]` / `[DONE]` lines and includes `_timing_seconds` in the final JSON. Use `--quiet` to print only JSON.

## Food Catalog

Supported food ids live in:

```text
src/ml/config_data/food_catalog.json
```

Bedrock classifies against this catalog using the image and Rekognition labels. Aliases are semantic hints, not simple string matching.

## Public Functions

```python
from ml import (
    ml_authenticate_face,
    ml_detect_food,
    ml_parse_expiration_date,
    ml_process_put_food,
    ml_process_retrieve_food,
)
```

All public functions accept and return dictionaries matching `docs/ml/CONTRACTS.md`.
