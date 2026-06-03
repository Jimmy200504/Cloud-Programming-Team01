# ML Contracts

All public functions accept and return dictionaries. Dates use `YYYY-MM-DD`; timestamps use ISO-8601.

Supported media refs:

```json
{"type": "local_path", "value": "/path/to/file"}
```

Also supported: `s3_uri`, `bytes_base64`. Expiration audio also accepts `transcript_text` for direct transcript testing.

## Face Auth

Function: `ml_authenticate_face(request)`

Request:

```json
{
  "request_id": "ml-face-001",
  "device_id": "smart-fridge-pi-001",
  "image": {"type": "local_path", "value": "/path/to/face.jpg"},
  "expected_user_id": "roger"
}
```

Success:

```json
{
  "request_id": "ml-face-001",
  "status": "success",
  "result": {
    "authenticated": true,
    "user_id": "roger",
    "confidence": 99.99,
    "matched_face_id": "rekognition-face-id",
    "collection_id": "ml-smart-fridge-faces"
  }
}
```

## Food Classification

Function: `ml_detect_food(request)`

The implementation uses Rekognition labels plus Bedrock vision classification against `ml/src/ml/config_data/food_catalog.json`.

Request:

```json
{
  "request_id": "ml-food-001",
  "device_id": "smart-fridge-pi-001",
  "image": {"type": "local_path", "value": "/path/to/food.jpg"}
}
```

Success:

```json
{
  "request_id": "ml-food-001",
  "status": "success",
  "result": {
    "food_id": "soy_milk",
    "food_name": "soy_milk",
    "display_name": "Soy milk",
    "confidence": 0.92,
    "matched_catalog_id": "soy_milk",
    "model": "jp.anthropic.claude-haiku-4-5-20251001-v1:0",
    "reason": "Bedrock explanation.",
    "rekognition_candidates": [
      {"label": "beverage", "confidence": 89.27},
      {"label": "milk", "confidence": 85.45}
    ]
  }
}
```

## Expiration Duration

Function: `ml_parse_expiration_date(request)`

The implementation uses Transcribe for audio-to-text and Bedrock for transcript-to-duration JSON.

Request:

```json
{
  "request_id": "ml-exp-001",
  "device_id": "smart-fridge-pi-001",
  "timezone": "Asia/Taipei",
  "captured_at": "2026-06-03T10:30:00+08:00",
  "audio": {"type": "local_path", "value": "/path/to/expiration.m4a"}
}
```

Success:

```json
{
  "request_id": "ml-exp-001",
  "status": "success",
  "result": {
    "expiration_date": "2026-08-03",
    "expiration_duration": "P2M",
    "expiration_duration_unit": "months",
    "expiration_duration_amount": 2,
    "transcript": "兩個月後",
    "confidence": 0.95,
    "reason": "Bedrock explanation.",
    "timezone": "Asia/Taipei"
  }
}
```

## Combined Put

Function: `ml_process_put_food(request)`

```json
{
  "request_id": "ml-put-001",
  "device_id": "smart-fridge-pi-001",
  "user_id": "roger",
  "food_image": {"type": "local_path", "value": "/path/to/food.jpg"},
  "expiration_audio": {"type": "local_path", "value": "/path/to/expiration.m4a"},
  "captured_at": "2026-06-03T10:30:00+08:00",
  "timezone": "Asia/Taipei"
}
```

Success:

```json
{
  "request_id": "ml-put-001",
  "status": "success",
  "result": {
    "user_id": "roger",
    "food_name": "soy_milk",
    "food_confidence": 0.92,
    "expiration_date": "2026-08-03",
    "expiration_duration": "P2M",
    "expiration_transcript": "兩個月後"
  }
}
```

## Combined Retrieve

Function: `ml_process_retrieve_food(request)`

```json
{
  "request_id": "ml-ret-001",
  "device_id": "smart-fridge-pi-001",
  "user_id": "roger",
  "food_image": {"type": "local_path", "value": "/path/to/removed_food.jpg"}
}
```

Success:

```json
{
  "request_id": "ml-ret-001",
  "status": "success",
  "result": {
    "user_id": "roger",
    "food_name": "soy_milk",
    "food_confidence": 0.92
  }
}
```

## Errors

```json
{
  "request_id": "ml-req",
  "status": "error",
  "error": {
    "code": "ML_LOW_CONFIDENCE",
    "message": "Human-readable message.",
    "details": {}
  }
}
```

Common codes: `ML_INVALID_INPUT`, `ML_FILE_NOT_FOUND`, `ML_UNSUPPORTED_MEDIA_TYPE`, `ML_AWS_PERMISSION_DENIED`, `ML_AWS_SERVICE_ERROR`, `ML_LOW_CONFIDENCE`, `ML_NO_FOOD_DETECTED`, `ML_TRANSCRIBE_FAILED`, `ML_AMBIGUOUS_DATE`, `ML_INTERNAL_ERROR`.
