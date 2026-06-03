# ML Test Plan

## 1. Test Categories

### Unit Tests

Purpose: validate local logic without AWS.

Must cover:

- Config loading.
- Request validation.
- Error payload conversion.
- Date parsing.
- Food label normalization.
- Face match result normalization.

### Contract Tests

Purpose: guarantee other teams can rely on JSON shapes.

Must cover:

- Face authentication success.
- Unknown face.
- Food detection success.
- Low-confidence food.
- Expiration date success.
- Ambiguous date.
- Combined put food response.
- Combined retrieve food response.

### AWS Integration Tests

Purpose: validate real AWS calls with dev resources.

Must cover:

- Rekognition face search.
- Rekognition food label detection.
- Transcribe job execution.
- S3 temporary audio upload/delete if used.

These tests should be skipped unless an explicit environment flag is set:

```text
ML_RUN_AWS_TESTS=1
```

### Raspberry Pi Smoke Tests

Purpose: validate runtime compatibility on the device.

Must cover:

- Python environment works.
- AWS credentials resolve.
- Local fixture paths are readable.
- ML functions return JSON.

The smoke test must not control physical lock or LED.

## 2. Fixture Policy

Use small test fixtures only:

```text
ml/tests/fixtures/images/
ml/tests/fixtures/audio/
```

Do not commit:

- Real user face images without consent.
- Large camera captures.
- Raw production audio.
- AWS-generated temporary files.
- Credentials.

## 3. Suggested Test Commands

Local tests:

```bash
cd ml
python -m pytest tests/unit tests/contract
```

AWS integration tests:

```bash
cd ml
AWS_PROFILE=your-profile ML_RUN_AWS_TESTS=1 python -m pytest tests/integration
```

Pi smoke test:

```bash
cd ml
AWS_PROFILE=your-profile python scripts/ml_pi_smoke_test.py \
  --face-image ./tests/fixtures/images/face_known_user.jpg \
  --food-image ./tests/fixtures/images/food_apple.jpg \
  --expiration-audio ./tests/fixtures/audio/expiration_next_friday.wav
```

## 4. Minimum Acceptance Before Integration

Before asking other teams to integrate:

- Local unit tests pass.
- Contract tests pass.
- At least one AWS face test passes.
- At least one AWS food test passes.
- At least one expiration parser test passes.
- Pi smoke test prints valid JSON.

## 5. Manual Verification Checklist

- No access keys committed.
- No `.env` with secrets committed.
- No real private face/audio data committed.
- All ML files are under `ml/` or `docs/ml/`.
- Contracts still match implementation responses.
- Error codes are documented.
