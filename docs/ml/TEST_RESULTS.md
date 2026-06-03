# ML Test Results

Test date: 2026-06-03

## AWS Resources

```text
AWS profile: default
AWS account: 491919374787
AWS region: ap-northeast-1
S3 bucket: ml-smart-fridge-media-491919374787-ap-northeast-1-an
Bedrock model: jp.anthropic.claude-haiku-4-5-20251001-v1:0
Rekognition collection: ml-smart-fridge-faces
Registered user id: roger
```

## Unit Tests

Command:

```bash
cd ml
uv run python -m unittest discover -s tests/unit
```

Result:

```text
Ran 9 tests
OK
```

## Face Registration

Command:

```bash
cd ml
env AWS_PROFILE=default \
  ML_AWS_REGION=ap-northeast-1 \
  ML_S3_BUCKET=ml-smart-fridge-media-491919374787-ap-northeast-1-an \
  ML_REKOGNITION_FACE_COLLECTION_ID=ml-smart-fridge-faces \
  uv run python scripts/ml_register_face.py \
    --user-id roger \
    --image tests/fixtures/images/register_face.jpg
```

Result:

```text
ExternalImageId: roger
FaceId: 31825a37-ca3a-47df-b346-c250a54bb458
Face confidence: 99.99995422363281
UnindexedFaces: []
```

## AWS Smoke Test

Command:

```bash
cd ml
env AWS_PROFILE=default \
  ML_AWS_REGION=ap-northeast-1 \
  ML_S3_BUCKET=ml-smart-fridge-media-491919374787-ap-northeast-1-an \
  ML_REKOGNITION_FACE_COLLECTION_ID=ml-smart-fridge-faces \
  ML_TRANSCRIBE_LANGUAGE_CODE=zh-TW \
  ML_TRANSCRIBE_IDENTIFY_LANGUAGE=true \
  ML_TRANSCRIBE_LANGUAGE_OPTIONS=zh-TW,en-US \
  ML_TIMEZONE=Asia/Taipei \
  uv run python scripts/ml_pi_smoke_test.py \
    --face-image tests/fixtures/images/test_face.jpg \
    --food-image tests/fixtures/images/soy_milk.jpg \
    --expiration-audio tests/fixtures/audio/2-month-later.m4a \
    --expected-user-id roger \
    --captured-at 2026-06-03T10:30:00+08:00
```

Result:

```text
face.status: success
face.result.authenticated: true
face.result.user_id: roger
face.result.confidence: 99.99971008300781

food.status: success
food.result.food_id: soy_milk
food.result.food_name: soy_milk
food.result.display_name: Soy milk
food.result.confidence: 0.92
food.result.model: jp.anthropic.claude-haiku-4-5-20251001-v1:0

expiration.status: success
expiration.result.transcript: 兩個月後
expiration.result.confidence: 0.95
expiration.result.expiration_duration: P2M
expiration.result.expiration_date: 2026-08-03
```

## Notes

- AWS Transcribe converts audio to text.
- Bedrock converts Chinese/English duration text into ISO-8601 duration, such as `P2M`.
- Bedrock classifies food into `ml/src/ml/config_data/food_catalog.json` ids using the image plus Rekognition labels.
- The HMI should prompt users to speak duration phrases such as `五天後`, `三週後`, or `兩個月後`.
- Private face/audio/image fixtures are ignored by git.
