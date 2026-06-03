# ML Specification

## 1. Purpose

The ML owner handles the machine-learning bridge for the smart refrigerator project.

This work converts camera/audio inputs into stable structured results that other teammates can consume:

- Face image -> authenticated refrigerator user.
- Food image -> detected food label.
- Spoken expiration date audio -> normalized expiration date.
- ML service failures -> predictable error payloads.

The branch is currently empty and dedicated to ML work. Even so, all ML-owned names must be namespaced to avoid collisions when merged into the shared project.

## 2. Namespace Convention

Use these prefixes consistently:

- Python package/module prefix: `ml_` or package name `ml`
- Folder prefix: `ml`
- AWS logical alias prefix: `ml`
- Environment variable prefix: `ML_`
- JSON field prefix only when needed: avoid global prefixes inside request/response bodies unless the field is ML-specific.

Recommended future source layout:

```text
ml/
  README.md
  pyproject.toml
  src/
    ml/
      __init__.py
      config.py
      errors.py
      models.py
      face_auth.py
      food_detect.py
      expiration_parse.py
      aws_clients/
        rekognition_client.py
        transcribe_client.py
        s3_client.py
      adapters/
        hmi_adapter.py
        lambda_adapter.py
  tests/
    fixtures/
      images/
      audio/
    unit/
    contract/
    integration/
```

## 3. Ownership Boundary

ML-owned:

- Rekognition face matching integration.
- Rekognition food label detection integration.
- Transcribe integration for spoken expiration date.
- Date parsing from transcript text.
- Shared ML response schema and error schema.
- Mockable local interfaces for development on Mac.
- Test fixtures and contract tests for ML outputs.

Not ML-owned:

- GPIO lock control.
- LED behavior.
- HMI screen implementation.
- DynamoDB inventory ownership decision.
- Cognito sign-up/login.
- SES email formatting/sending.
- Web frontend.
- IoT Device Shadow implementation.

ML may expose helper functions for these teams, but should not own their side effects.

## 4. Service Architecture

The ML module should be written as a pure Python package first. Other teams can call it from:

- Raspberry Pi HMI/state machine.
- AWS Lambda wrapper.
- Local developer scripts.

Recommended call direction:

```text
HMI / Lambda / Test Script
  -> ml public function
  -> AWS client wrapper
  -> AWS Rekognition / Transcribe / S3
  -> normalized ML response JSON
```

Do not hard-code AWS credentials. Use AWS SDK credential resolution:

- Local Mac: `AWS_PROFILE`
- Raspberry Pi: configured AWS profile, environment role, or IoT-authorized temporary credentials
- Lambda: execution role

## 5. Core Features

### ML-AI-001 Face Authentication

Input:

- One face image from the face camera.
- Optional expected user context if the caller already knows the Cognito user.

Processing:

- Validate image file exists or bytes are present.
- Call Rekognition face search against a configured collection.
- Map matched face metadata to `user_id`.
- Return confidence and authentication result.

Output:

- `authenticated: true/false`
- `user_id`
- `confidence`
- `matched_face_id`

Acceptance:

- Returns a valid success payload for a known fixture image.
- Returns `authenticated: false` for unknown faces.
- Never opens a lock directly.

### ML-AI-002 Food Detection

Input:

- One image from the food camera.

Processing:

- Validate image.
- Call Rekognition DetectLabels or Custom Labels, depending on project resources.
- Select the highest-confidence supported food label.
- Return all candidate labels for debugging.

Output:

- `food_name`
- `confidence`
- `candidates`

Acceptance:

- Returns deterministic normalized labels from mock fixtures.
- Handles no-food/low-confidence cases without crashing.
- Does not write to DynamoDB directly unless explicitly wrapped by Cloud-owned code.

### ML-AI-003 Expiration Date Parsing

Input:

- One audio file or audio bytes from the microphone.
- Optional timezone.

Processing:

- Send audio to Transcribe or use an injected transcript in local tests.
- Parse transcript into ISO-8601 date.
- Preserve original transcript for audit/debug.

Output:

- `expiration_date`
- `transcript`
- `confidence` if available

Acceptance:

- Parses common phrases such as `tomorrow`, `next Friday`, `June 10`, and `two weeks later`.
- Uses the caller-provided timezone when resolving relative dates.
- Returns a structured error when the date is ambiguous.

### ML-AI-004 Unified Error Handling

All public ML functions must return or raise errors that can be converted into the shared error payload in [CONTRACTS.md](CONTRACTS.md).

Acceptance:

- Missing file, AWS permission failure, network failure, low confidence, and ambiguous date each have a distinct error code.

## 6. Configuration

Use environment variables with `ML_` prefix:

```text
ML_AWS_REGION=us-east-1
ML_REKOGNITION_FACE_COLLECTION_ID=ml-smart-fridge-faces-dev
ML_FOOD_MIN_CONFIDENCE=70
ML_FACE_MIN_CONFIDENCE=85
ML_TRANSCRIBE_LANGUAGE_CODE=en-US
ML_S3_BUCKET=ml-smart-fridge-media-dev
ML_TIMEZONE=Asia/Taipei
```

Do not commit secrets, access keys, or `.env` files containing credentials.

## 7. Integration Modes

### Local Mock Mode

For local Mac development without touching AWS:

- Inject fake Rekognition results.
- Inject fake Transcribe transcripts.
- Run unit and contract tests.

### Local AWS Mode

For validating AWS integration from Mac:

- Use `AWS_PROFILE=your-profile`.
- Use sample fixtures.
- Avoid writing shared production resources.

### Raspberry Pi Smoke Mode

For final device test:

- Run one face image capture.
- Run one food image capture.
- Run one audio capture.
- Print normalized JSON responses.
- Do not control lock/LED from ML tests.

## 8. Handoff Requirements

Before other teams integrate ML, this branch must provide:

- Public function names and JSON contracts.
- Mock examples for success and failure.
- Test command.
- Required environment variables.
- AWS IAM permissions needed by ML only.
- Known limitations and confidence thresholds.

## 9. Definition of Done

The ML branch is considered ready for integration when:

- `CONTRACTS.md` has stable request/response schemas.
- Unit tests pass locally.
- Contract tests validate JSON schemas.
- AWS integration tests pass with a dedicated dev profile.
- Raspberry Pi smoke test produces valid JSON for face, food, and audio inputs.
- No credentials or generated media files are committed.
