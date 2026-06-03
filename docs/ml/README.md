# ML Integration

ML owns the smart refrigerator AI bridge:

- Face image -> authenticated user via Rekognition.
- Food image -> catalog food item via Rekognition labels + Bedrock vision classification.
- Expiration audio -> transcript via Transcribe, then ISO duration via Bedrock.

## AWS Resources

```text
AWS profile: default
AWS account: 491919374787
AWS region: ap-northeast-1
S3 bucket: ml-smart-fridge-media-491919374787-ap-northeast-1-an
Rekognition collection: ml-smart-fridge-faces
Bedrock model: jp.anthropic.claude-haiku-4-5-20251001-v1:0
Registered test user id: roger
```

## Setup

```bash
cd ml
uv sync

export AWS_PROFILE=default
export ML_AWS_REGION=ap-northeast-1
export ML_S3_BUCKET=ml-smart-fridge-media-491919374787-ap-northeast-1-an
export ML_REKOGNITION_FACE_COLLECTION_ID=ml-smart-fridge-faces
export ML_BEDROCK_MODEL_ID=jp.anthropic.claude-haiku-4-5-20251001-v1:0
export ML_TRANSCRIBE_LANGUAGE_CODE=zh-TW
export ML_TRANSCRIBE_IDENTIFY_LANGUAGE=true
export ML_TRANSCRIBE_LANGUAGE_OPTIONS=zh-TW,en-US
export ML_TIMEZONE=Asia/Taipei
```

Required AWS permissions:

```text
rekognition:CreateCollection
rekognition:DescribeCollection
rekognition:IndexFaces
rekognition:SearchFacesByImage
rekognition:DetectLabels
transcribe:StartTranscriptionJob
transcribe:GetTranscriptionJob
transcribe:ListTranscriptionJobs
s3:PutObject
s3:GetObject
s3:DeleteObject
s3:ListBucket
bedrock:InvokeModel
sts:GetCallerIdentity
```

## Commands

Check AWS:

```bash
uv run python scripts/ml_check_aws.py
```

Register a face:

```bash
uv run python scripts/ml_register_face.py \
  --user-id roger \
  --image tests/fixtures/images/register_face.jpg
```

Run full smoke test:

```bash
uv run python scripts/ml_pi_smoke_test.py \
  --face-image tests/fixtures/images/test_face.jpg \
  --food-image tests/fixtures/images/soy_milk.jpg \
  --expiration-audio tests/fixtures/audio/2-month-later.m4a \
  --expected-user-id roger \
  --captured-at 2026-06-03T10:30:00+08:00
```

The smoke test prints each stage as it starts and finishes, then includes `_timing_seconds` in the final JSON.

Run local tests:

```bash
uv run python -m unittest discover -s tests/unit
```

## Food Catalog

Supported food items are defined in:

```text
ml/src/ml/config_data/food_catalog.json
```

Add food ids, display names, Chinese names, aliases, parent, and category there. Bedrock must return one catalog `id`; otherwise ML returns an error.

Catalog matching process:

1. Rekognition extracts visual labels from the image.
2. Bedrock receives the original image, Rekognition labels, and the full food catalog.
3. Bedrock chooses the best catalog `id`, using aliases and names as semantic hints rather than direct string matching.
4. Code validates that the returned `food_id` exists in the catalog and that confidence passes the threshold.

## Integration

Use [CONTRACTS.md](CONTRACTS.md) for input/output JSON. See [TEST_RESULTS.md](TEST_RESULTS.md) for the latest verified AWS run and [IMPLEMENTATION_RECORD.md](IMPLEMENTATION_RECORD.md) for the end-to-end build record.

ML returns JSON only. It does not open locks, control LEDs, write DynamoDB, or send email.
