# ML Implementation Plan

## Phase 0: Branch and Repo Setup

Goal: create a clean ML-owned workspace without blocking other teams.

Actions:

1. Work directly on the dedicated `ML` branch if you are the only ML branch owner.
2. Keep all ML files under `ml/` and `docs/ml/`.
3. Commit specs before implementation.
4. Add `.gitignore` rules before creating credentials, media captures, or temporary AWS outputs.

Recommended initial commit:

```bash
git add docs/ml
git commit -m "Add ML integration specs"
```

## Phase 1: Local Package Skeleton

Goal: create importable ML package with no AWS calls yet.

Deliverables:

- `ml/pyproject.toml`
- `ml/src/ml/models.py`
- `ml/src/ml/errors.py`
- `ml/src/ml/config.py`
- `ml/tests/unit/`

Acceptance:

- Package imports locally.
- Config reads `ML_` environment variables.
- Error helpers produce the contract format in `CONTRACTS.md`.

## Phase 2: Contract Models and Mock Services

Goal: let HMI/Cloud teams integrate before real AWS calls are ready.

Deliverables:

- Request/response dataclasses or Pydantic models.
- Mock face authentication service.
- Mock food detection service.
- Mock expiration parser service.
- Contract tests that compare outputs with examples in `CONTRACTS.md`.

Acceptance:

- `face_authenticate()` returns known-user and unknown-user examples.
- `detect_food()` returns success and low-confidence examples.
- `parse_expiration_date()` returns success and ambiguous-date examples.

## Phase 3: Rekognition Face Authentication

Goal: authenticate users from face camera images.

AWS setup needed from Cloud Architect:

- Rekognition collection id.
- Mapping from Rekognition face id or external image id to Cognito/user id.
- IAM permission for:
  - `rekognition:SearchFacesByImage`
  - `rekognition:DetectFaces`

Deliverables:

- `aws_clients/rekognition_client.py`
- `face_auth.py`
- Integration test using a dev face collection.

Acceptance:

- Known face returns `authenticated: true`.
- Unknown face returns `authenticated: false` or `ML_UNKNOWN_FACE`.
- Multiple visible faces return `ML_MULTIPLE_FACES_DETECTED`.

## Phase 4: Rekognition Food Detection

Goal: classify food images into normalized labels.

AWS setup options:

- Simple path: Rekognition `DetectLabels`.
- Better path: Rekognition Custom Labels if the team has trained food classes.

Deliverables:

- `food_detect.py`
- Supported food label mapping.
- Confidence threshold config.

Acceptance:

- Food image returns normalized `food_name`.
- Non-food image returns `ML_NO_FOOD_DETECTED` or `ML_LOW_CONFIDENCE`.
- Response includes raw candidates for debugging.

## Phase 5: Transcribe and Date Parser

Goal: convert spoken expiration date into `YYYY-MM-DD`.

AWS setup needed:

- S3 bucket for temporary audio upload if Transcribe requires it.
- IAM permission for:
  - `transcribe:StartTranscriptionJob`
  - `transcribe:GetTranscriptionJob`
  - `s3:PutObject`
  - `s3:GetObject`
  - `s3:DeleteObject`

Deliverables:

- `aws_clients/transcribe_client.py`
- `aws_clients/s3_client.py`
- `expiration_parse.py`
- Deterministic parser tests for relative dates.

Acceptance:

- `tomorrow` resolves using `captured_at` and `timezone`.
- Clear absolute dates return `YYYY-MM-DD`.
- Ambiguous phrases return `ML_AMBIGUOUS_DATE`.

## Phase 6: Public API Adapter

Goal: expose stable functions for HMI and Lambda wrappers.

Suggested public functions:

```python
ml_authenticate_face(request: dict) -> dict
ml_detect_food(request: dict) -> dict
ml_parse_expiration_date(request: dict) -> dict
ml_process_put_food(request: dict) -> dict
ml_process_retrieve_food(request: dict) -> dict
```

Acceptance:

- Every function accepts and returns contract-compatible dictionaries.
- No function directly controls lock, LED, DynamoDB, SES, or frontend state.

## Phase 7: Raspberry Pi Smoke Test

Goal: prove the ML package can run on the Pi without taking over hardware responsibilities.

Deliverables:

- `scripts/ml_pi_smoke_test.py`

Smoke test behavior:

- Reads pre-captured local image/audio paths.
- Calls ML public functions.
- Prints JSON responses.
- Does not open lock.
- Does not flash LED.
- Does not write DynamoDB.

Acceptance:

- Pi can run the script with `AWS_PROFILE` or role-based credentials.
- Output can be pasted into HMI/Cloud issue threads for debugging.

## Phase 8: Integration Handoff

Goal: make it easy for others to connect to ML.

Deliverables:

- Updated `README.md` with install/run commands.
- `CONTRACTS.md` finalized.
- Test results documented.
- Required IAM policy documented.
- Known limitations documented.

Handoff message should include:

- Function names.
- Input examples.
- Output examples.
- Required environment variables.
- Failure behavior.
- Confidence thresholds.
