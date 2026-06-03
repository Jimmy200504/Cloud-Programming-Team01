# ML Implementation Record

This records how the empty ML branch became the working AWS ML integration.

Date: 2026-06-03

## 1. Scope

ML owns three outputs:

- Face image -> authenticated user.
- Food image -> canonical food catalog item.
- Expiration audio -> transcript, ISO duration, expiration date.

ML returns JSON only. It does not control lock/LED, write DynamoDB, or send email.

## 2. Python Project

Created `ml/` as a uv-managed Python package:

```bash
cd ml
uv sync
```

Important files:

```text
ml/src/ml/api.py
ml/src/ml/aws_service.py
ml/src/ml/bedrock_interpreter.py
ml/src/ml/config.py
ml/src/ml/config_data/food_catalog.json
ml/scripts/ml_check_aws.py
ml/scripts/ml_create_bucket.py
ml/scripts/ml_register_face.py
ml/scripts/ml_pi_smoke_test.py
```

## 3. AWS Resources

Configured and tested:

```text
AWS profile: default
AWS account: 491919374787
Region: ap-northeast-1
S3 bucket: ml-smart-fridge-media-491919374787-ap-northeast-1-an
Rekognition collection: ml-smart-fridge-faces
Bedrock model: jp.anthropic.claude-haiku-4-5-20251001-v1:0
Registered user id: roger
```

## 4. S3 Setup

The requested bucket name ended with `-491919374787-ap-northeast-1-an`, which AWS treats as an account-regional namespace bucket. The installed AWS CLI did not expose the needed namespace option, so `ml_create_bucket.py` was added and used through boto3.

Command used:

```bash
cd ml
env AWS_PROFILE=default \
  ML_AWS_REGION=ap-northeast-1 \
  ML_S3_BUCKET=ml-smart-fridge-media-491919374787-ap-northeast-1-an \
  uv run python scripts/ml_create_bucket.py --account-regional
```

Result:

```text
bucket created
public access block enabled
```

The bucket stores temporary audio files and Transcribe output JSON.

## 5. Rekognition Setup

Created/checked the face collection with:

```bash
cd ml
env AWS_PROFILE=default \
  ML_AWS_REGION=ap-northeast-1 \
  ML_S3_BUCKET=ml-smart-fridge-media-491919374787-ap-northeast-1-an \
  ML_REKOGNITION_FACE_COLLECTION_ID=ml-smart-fridge-faces \
  uv run python scripts/ml_check_aws.py --create-collection
```

Registered the user face:

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
```

## 6. Bedrock Setup

Claude 3 Haiku was not used because it is legacy for this project. Claude Haiku 4.5 required an inference profile rather than the base model id.

Final model id:

```text
jp.anthropic.claude-haiku-4-5-20251001-v1:0
```

Verified Bedrock with:

```bash
cd ml
env AWS_PROFILE=default \
  ML_AWS_REGION=ap-northeast-1 \
  ML_S3_BUCKET=ml-smart-fridge-media-491919374787-ap-northeast-1-an \
  ML_REKOGNITION_FACE_COLLECTION_ID=ml-smart-fridge-faces \
  ML_BEDROCK_MODEL_ID=jp.anthropic.claude-haiku-4-5-20251001-v1:0 \
  uv run python scripts/ml_check_aws.py
```

Result:

```text
s3_bucket_ok: true
transcribe_ok: true
bedrock_ok: true
```

## 7. Food Classification

Initial Rekognition-only classification was not sufficient because labels such as `person` or `box` can outrank the actual food.

Final design:

```text
image
-> Rekognition DetectLabels for visual signals
-> Bedrock sees original image + Rekognition labels + food catalog
-> Bedrock returns strict JSON with catalog food_id
-> code validates food_id exists in food_catalog.json
```

Food catalog:

```text
ml/src/ml/config_data/food_catalog.json
```

For the soy milk image, Bedrock returned:

```text
food_id: soy_milk
display_name: Soy milk
confidence: 0.92
```

## 8. Expiration Parsing

Rule-based duration parsing was removed. Final design:

```text
audio
-> upload to S3
-> Transcribe job
-> transcript JSON from S3
-> Bedrock converts transcript to strict duration JSON
-> code validates ISO duration
-> captured_at + duration = expiration_date
```

For the test audio:

```text
transcript: 兩個月後
duration: P2M
expiration_date: 2026-08-03
confidence: 0.95
```

Expiration currently takes around 10 seconds because Amazon Transcribe is job-based and must be polled until completion.

## 9. Final Smoke Test

Command:

```bash
cd ml
env AWS_PROFILE=default \
  ML_AWS_REGION=ap-northeast-1 \
  ML_S3_BUCKET=ml-smart-fridge-media-491919374787-ap-northeast-1-an \
  ML_REKOGNITION_FACE_COLLECTION_ID=ml-smart-fridge-faces \
  ML_BEDROCK_MODEL_ID=jp.anthropic.claude-haiku-4-5-20251001-v1:0 \
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

Observed timing:

```text
face auth: 0.959s
food classification: 2.613s
expiration transcription + duration: 10.181s
total: 13.754s
```

Final result:

```text
face.authenticated: true
face.user_id: roger
food.food_id: soy_milk
expiration.transcript: 兩個月後
expiration.expiration_duration: P2M
expiration.expiration_date: 2026-08-03
```

## 10. Private Test Assets

Private fixtures are kept locally and ignored by git:

```text
ml/tests/fixtures/images/*
ml/tests/fixtures/audio/*
```

This prevents face images, food photos, and audio recordings from being committed.

