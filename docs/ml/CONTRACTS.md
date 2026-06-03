# ML Contracts

These contracts are stable integration points for HMI, Cloud, Hardware, and Frontend teams.

All timestamps should use ISO-8601 strings. All dates should use `YYYY-MM-DD`.

## 1. Common Request Metadata

```json
{
  "request_id": "ml-req-20260603-000001",
  "source": "raspberry-pi-hmi",
  "device_id": "smart-fridge-pi-001",
  "timezone": "Asia/Taipei"
}
```

Fields:

- `request_id`: caller-generated id for tracing.
- `source`: caller name, such as `raspberry-pi-hmi`, `lambda`, or `local-test`.
- `device_id`: refrigerator device id.
- `timezone`: timezone used for relative date parsing.

## 2. Face Authentication

### Request

```json
{
  "request_id": "ml-req-20260603-000001",
  "device_id": "smart-fridge-pi-001",
  "image": {
    "type": "local_path",
    "value": "./fixtures/images/face_known_user.jpg"
  },
  "expected_user_id": null
}
```

Supported image types:

- `local_path`
- `s3_uri`
- `bytes_base64`

### Success Response

```json
{
  "request_id": "ml-req-20260603-000001",
  "status": "success",
  "result": {
    "authenticated": true,
    "user_id": "cognito-user-sub-or-team-user-id",
    "confidence": 98.42,
    "matched_face_id": "rekognition-face-id",
    "collection_id": "ml-smart-fridge-faces-dev"
  }
}
```

### Unknown Face Response

```json
{
  "request_id": "ml-req-20260603-000001",
  "status": "success",
  "result": {
    "authenticated": false,
    "user_id": null,
    "confidence": 0,
    "matched_face_id": null,
    "collection_id": "ml-smart-fridge-faces-dev"
  }
}
```

## 3. Food Detection

### Request

```json
{
  "request_id": "ml-req-20260603-000002",
  "device_id": "smart-fridge-pi-001",
  "image": {
    "type": "local_path",
    "value": "./fixtures/images/food_apple.jpg"
  },
  "min_confidence": 70
}
```

### Success Response

```json
{
  "request_id": "ml-req-20260603-000002",
  "status": "success",
  "result": {
    "food_name": "apple",
    "confidence": 94.12,
    "model": "rekognition-detect-labels",
    "candidates": [
      {
        "label": "apple",
        "confidence": 94.12
      },
      {
        "label": "fruit",
        "confidence": 91.87
      }
    ]
  }
}
```

### Low Confidence Response

```json
{
  "request_id": "ml-req-20260603-000002",
  "status": "error",
  "error": {
    "code": "ML_LOW_CONFIDENCE",
    "message": "No supported food label reached the configured confidence threshold.",
    "details": {
      "threshold": 70,
      "best_candidate": {
        "label": "object",
        "confidence": 42.5
      }
    }
  }
}
```

## 4. Expiration Date Parsing

### Request

```json
{
  "request_id": "ml-req-20260603-000003",
  "device_id": "smart-fridge-pi-001",
  "timezone": "Asia/Taipei",
  "audio": {
    "type": "local_path",
    "value": "./fixtures/audio/expiration_next_friday.wav"
  },
  "captured_at": "2026-06-03T10:30:00+08:00"
}
```

Supported audio types:

- `local_path`
- `s3_uri`
- `bytes_base64`
- `transcript_text` for local tests only

### Success Response

```json
{
  "request_id": "ml-req-20260603-000003",
  "status": "success",
  "result": {
    "expiration_date": "2026-06-05",
    "transcript": "next Friday",
    "confidence": null,
    "timezone": "Asia/Taipei"
  }
}
```

### Ambiguous Date Response

```json
{
  "request_id": "ml-req-20260603-000003",
  "status": "error",
  "error": {
    "code": "ML_AMBIGUOUS_DATE",
    "message": "The spoken expiration date could not be normalized into one date.",
    "details": {
      "transcript": "sometime next week"
    }
  }
}
```

## 5. Combined Put Food ML Result

This is optional. It is useful when HMI wants one ML response after both food image and audio are captured.

### Request

```json
{
  "request_id": "ml-req-20260603-000004",
  "device_id": "smart-fridge-pi-001",
  "user_id": "cognito-user-sub-or-team-user-id",
  "food_image": {
    "type": "local_path",
    "value": "./fixtures/images/food_apple.jpg"
  },
  "expiration_audio": {
    "type": "local_path",
    "value": "./fixtures/audio/expiration_next_friday.wav"
  },
  "captured_at": "2026-06-03T10:30:00+08:00",
  "timezone": "Asia/Taipei"
}
```

### Success Response

```json
{
  "request_id": "ml-req-20260603-000004",
  "status": "success",
  "result": {
    "user_id": "cognito-user-sub-or-team-user-id",
    "food_name": "apple",
    "food_confidence": 94.12,
    "expiration_date": "2026-06-05",
    "expiration_transcript": "next Friday"
  }
}
```

Cloud team should write this result to DynamoDB. ML should not own inventory persistence.

## 6. Combined Retrieve Food ML Result

ML identifies what was removed. Cloud decides whether the current user owns it.

### Request

```json
{
  "request_id": "ml-req-20260603-000005",
  "device_id": "smart-fridge-pi-001",
  "user_id": "cognito-user-sub-or-team-user-id",
  "food_image": {
    "type": "local_path",
    "value": "./fixtures/images/removed_food_apple.jpg"
  }
}
```

### Success Response

```json
{
  "request_id": "ml-req-20260603-000005",
  "status": "success",
  "result": {
    "user_id": "cognito-user-sub-or-team-user-id",
    "food_name": "apple",
    "food_confidence": 92.8
  }
}
```

## 7. Common Error Codes

```text
ML_INVALID_INPUT
ML_FILE_NOT_FOUND
ML_UNSUPPORTED_MEDIA_TYPE
ML_AWS_PERMISSION_DENIED
ML_AWS_NETWORK_ERROR
ML_AWS_SERVICE_ERROR
ML_LOW_CONFIDENCE
ML_NO_FACE_DETECTED
ML_MULTIPLE_FACES_DETECTED
ML_UNKNOWN_FACE
ML_NO_FOOD_DETECTED
ML_TRANSCRIBE_FAILED
ML_AMBIGUOUS_DATE
ML_INTERNAL_ERROR
```

Common error payload:

```json
{
  "request_id": "ml-req-20260603-000099",
  "status": "error",
  "error": {
    "code": "ML_INVALID_INPUT",
    "message": "Human-readable error message.",
    "details": {}
  }
}
```
