# Smart Fridge Current Cloud Design

Last updated: 2026-06-04

This document summarizes the current deployed cloud design and the parts that can still be changed safely.

## Current Deployment

Region:

```text
ap-northeast-1
```

API base URL:

```text
https://v6ylyjtxga.execute-api.ap-northeast-1.amazonaws.com/dev
```

Cognito:

```text
UserPoolId: ap-northeast-1_HIySrbd1y
UserPoolClientId: 58u2jdcqh3l2r7or7uctogai9n
```

DynamoDB:

```text
Food table: SmartFridgeFoods-dev
User face mapping table: SmartFridgeUserFaces-dev
```

S3:

```text
Face image bucket: smart-fridge-user-faces-dev-491919374787
```

Rekognition:

```text
CollectionId: ml-smart-fridge-faces
Face match threshold: 85
```

IoT Core:

```text
ThingName: smart-fridge-001
DevicePolicyName: smart-fridge-dev-device-policy
```

## Implemented Scope

The backend currently provides:

- Cognito signup through `POST /auth/signup`.
- Cognito login support from the frontend through Cognito `InitiateAuth`.
- Cognito account confirmation from the frontend through Cognito `ConfirmSignUp`.
- Authenticated face upload through `POST /users/me/face`.
- User face image storage in S3.
- Rekognition `IndexFaces` when a user uploads a face image.
- DynamoDB mapping from Cognito user to Rekognition `FaceId`.
- Rekognition `SearchFacesByImage` for face authentication and owner check.
- Food item creation in DynamoDB through `POST /foods/put`.
- Test owner check through `POST /test/owner-check`.
- Basic food retrieval API shape through `POST /foods/retrieve`.
- Authenticated inventory listing through `GET /foods/me`.
- IoT Device Shadow read through `GET /device/{deviceId}/state`.
- IoT Device Shadow desired lock update through `POST /device/{deviceId}/lock`.
- CORS enabled for frontend local testing.

## Main Data Flow

### User Registration

1. Frontend calls `POST /auth/signup`.
2. Backend calls Cognito `SignUp`.
3. User confirms the account with the code sent by Cognito.
4. Frontend logs in through Cognito and stores the returned ID token.

### Face Registration

1. User logs in.
2. Frontend sends the ID token and a base64 JPEG or PNG image to `POST /users/me/face`.
3. Backend reads the Cognito user from the token claims.
4. Backend calls Rekognition `IndexFaces`.
5. Backend stores the uploaded image in S3.
6. Backend stores the Cognito user and Rekognition `FaceId` mapping in DynamoDB.

### Owner Check Test

1. Frontend creates a food item with `POST /foods/put`.
2. Backend stores the food owner, food name, expiration date, and device id in DynamoDB.
3. Frontend sends the created `foodId` and a face image to `POST /test/owner-check`.
4. Backend loads the food item from DynamoDB.
5. Backend calls Rekognition `SearchFacesByImage`.
6. Backend checks the top Rekognition matches and uses the first match that has a Cognito mapping in DynamoDB.
7. Backend compares the recognized Cognito user with the food owner.
8. Backend returns `success` if the recognized user is the owner, otherwise `fail`.

## DynamoDB Tables

### Food Table

Table:

```text
SmartFridgeFoods-dev
```

Primary key:

```text
foodId
```

Important attributes:

```text
foodId
ownerUserId
ownerEmail
foodName
expirationDate
deviceId
createdAt
updatedAt
recordType
```

GSI:

```text
OwnerExpirationIndex
Partition key: ownerUserId
Sort key: expirationDate
```

Notes:

- `ownerEmail` is normalized to lowercase.
- If only `ownerEmail` is provided, `ownerUserId` is stored as `email#<ownerEmail>`.
- For a stronger production flow, the frontend should eventually use the owner's Cognito `sub` as `ownerUserId`.

### User Face Mapping Table

Table:

```text
SmartFridgeUserFaces-dev
```

Primary key:

```text
userId
```

GSI:

```text
FaceIdIndex
Partition key: rekognitionFaceId
```

Important attributes:

```text
userId
username
email
displayName
faceImageBucket
faceImageS3Key
rekognitionCollectionId
rekognitionFaceId
imageContentType
createdAt
updatedAt
```

## Rekognition Behavior

The current collection is:

```text
ml-smart-fridge-faces
```

The current threshold is:

```text
85
```

When a new face image is uploaded, the backend uses:

```text
IndexFaces
ExternalImageId = Cognito user sub
MaxFaces = 1
QualityFilter = AUTO
```

When checking a face image, the backend uses:

```text
SearchFacesByImage
FaceMatchThreshold = 85
MaxFaces = 5
```

The backend intentionally checks multiple Rekognition matches. If a matched `FaceId` exists in Rekognition but has no DynamoDB Cognito mapping, the backend skips it and checks the next match. This prevents old or test faces in the collection from blocking a valid mapped user.

If no match is above the threshold, the API returns `FACE_NOT_RECOGNIZED`.

## IoT Device Shadow Design

Device Shadow is used only for device state. Images, audio, and food records do not go into Device Shadow.

Thing:

```text
smart-fridge-001
```

Expected shadow shape:

```json
{
  "state": {
    "desired": {
      "lock": "locked",
      "led": "off"
    },
    "reported": {
      "lock": "locked",
      "led": "off",
      "temperature": 4.2,
      "humidity": 55,
      "lastSeenAt": "2026-06-04T00:00:00Z"
    }
  }
}
```

Allowed `lock` values:

```text
locked
unlocked
```

Allowed `led` values:

```text
off
alert
```

## Current Limitations

- Face images are sent as base64 in JSON for MVP simplicity.
- Owner check is currently a test API, not the final refrigerator retrieval flow.
- Food recognition from a food image is not implemented by this backend.
- Expiration extraction from audio is not implemented by this backend.
- SES notification logic exists as a backend hook, but real sending requires a verified `SesFromEmail`.
- Cognito signup is handled by backend, but confirmation and login are called directly from frontend to Cognito.
- If a user uploads a new face multiple times, the DynamoDB user mapping points to the latest uploaded face. Older Rekognition faces may still remain in the collection.

## Configurable Items

These can be changed in `aws-backend/template.yaml` or deployment parameters:

```text
StageName
DeviceId
SesFromEmail
LambdaExecutionRoleArn
FACE_MATCH_THRESHOLD
REKOGNITION_COLLECTION_ID
MOCK_MODE
```

Recommended changes:

- Increase `FACE_MATCH_THRESHOLD` to `90` or `95` for a stricter demo.
- Change `DeviceId` if the Raspberry Pi team uses a different IoT Thing name.
- Set `SesFromEmail` only after the email address is verified in SES.
- Keep `REKOGNITION_COLLECTION_ID` aligned with the Rekognition team's collection.

Riskier changes:

- Changing DynamoDB table names after deployment can create new tables and split data.
- Changing Cognito User Pool can invalidate existing test users.
- Changing S3 bucket name can separate old face images from new uploads.

## Local Frontend Test Page

The current simple API test frontend is in:

```text
frontend/test/
```

Run it with:

```bash
cd frontend/test
python3 -m http.server 5173
```

Open:

```text
http://localhost:5173
```

The page supports signup, account confirmation, login, face upload, and owner check testing.
