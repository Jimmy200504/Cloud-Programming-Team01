# Smart Fridge Interface Contract

Status: legacy MVP contract.

For the current deployed design, use `final-design.md`.
For the frontend API contract, use `frontend-api-contract.md`.

This document defines the MVP interface contract for the smart refrigerator project.

Cloud Architect scope:

- Cognito user identity
- DynamoDB food inventory schema
- API Gateway and Lambda contracts
- AWS IoT Core Device Shadow contract
- SES notification trigger

Other teams can build against this document without waiting for the final AWS implementation.

## System Boundary

Use API Gateway and Lambda for business events:

- Face authentication
- Put food
- Retrieve food
- Inventory query
- Email notification
- Reading or updating device state through backend APIs

Use AWS IoT Core Device Shadow for device state only:

- Lock state
- LED state
- Temperature
- Humidity
- Last seen timestamp

Do not put base64 image or audio payloads into Device Shadow.

## Common Rules

### Device

MVP device id:

```text
smart-fridge-001
```

### Timestamp Format

Use ISO 8601 UTC timestamps.

Example:

```text
2026-06-03T10:00:00Z
```

### Date Format

Expiration dates use `YYYY-MM-DD`.

Example:

```text
2026-06-10
```

### Base64 Payload Rules

For MVP, images and audio are sent directly as base64 in API requests.

Image formats:

```text
image/jpeg
image/png
```

Audio format:

```text
audio/wav
```

Base64 strings must not include a data URL prefix.

Correct:

```text
/9j/4AAQSkZJRgABAQ...
```

Incorrect:

```text
data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ...
```

## Data Model

### User

Users are managed by Amazon Cognito. The backend uses the Cognito `sub` value as `userId`.

```json
{
  "userId": "cognito-sub",
  "email": "alice@example.com",
  "displayName": "Alice"
}
```

### Food Item

```json
{
  "foodId": "food-uuid",
  "ownerUserId": "cognito-sub",
  "ownerEmail": "alice@example.com",
  "foodName": "milk",
  "expirationDate": "2026-06-10",
  "deviceId": "smart-fridge-001",
  "createdAt": "2026-06-03T10:00:00Z",
  "updatedAt": "2026-06-03T10:00:00Z"
}
```

Do not store base64 images or audio in DynamoDB. If image persistence is needed later, store files in S3 and save only the S3 key or URL in DynamoDB.

## DynamoDB Schema

Table name:

```text
SmartFridgeFoods
```

Primary key:

```text
PK: foodId
```

Attributes:

```text
foodId
ownerUserId
ownerEmail
foodName
expirationDate
deviceId
createdAt
updatedAt
foodImage
foodClassification
expirationParsing
recordType
```

Frontend query index:

```text
GSI name: OwnerExpirationIndex
GSI partition key: ownerUserId
GSI sort key: expirationDate
```

This lets the frontend query the current user's foods and sort them by expiration date.

Food image storage:

```text
Do not store raw base64 food images in DynamoDB.
Store the captured food image in S3 and save only foodImage metadata in DynamoDB.
```

Food image metadata:

```json
{
  "foodImage": {
    "bucket": "smart-fridge-food-images-dev-491919374787",
    "s3Key": "food-images/cognito-sub/food-uuid.jpg",
    "contentType": "image/jpeg",
    "capturedAt": "2026-06-03T10:00:00Z"
  }
}
```

## API Contract

### Error Response Format

All APIs use this error response shape:

```json
{
  "success": false,
  "errorCode": "INVALID_IMAGE",
  "message": "Image must be a base64 encoded JPEG or PNG"
}
```

Supported MVP error codes:

```text
INVALID_SIGNUP_REQUEST
USERNAME_EXISTS
INVALID_PASSWORD
INVALID_IMAGE
INVALID_AUDIO
FACE_NOT_RECOGNIZED
USER_NOT_FOUND
FACE_REGISTRATION_FAILED
FOOD_NOT_RECOGNIZED
FOOD_NOT_FOUND
NOT_OWNER
INTERNAL_ERROR
```

## Frontend Signup And Face Registration APIs

There are two separate steps:

1. Create the Cognito account.
2. After login, upload a face image and link the Rekognition face id to the Cognito user.

Cognito stores the account identity. S3 stores the uploaded face image. Rekognition stores face metadata. DynamoDB stores the mapping between the Cognito user, the S3 image, and the Rekognition face id.

### Sign Up

```text
POST /auth/signup
```

This route is unauthenticated.

Request:

```json
{
  "username": "alice@example.com",
  "email": "alice@example.com",
  "password": "TestPassword123!",
  "displayName": "Alice"
}
```

Password currently follows the Cognito policy:

```text
Minimum length: 8
Requires uppercase: yes
Requires lowercase: yes
Requires number: yes
Requires symbol: no
```

After signup, Cognito sends a confirmation code to the user's email address. Tell the user to check their inbox and spam/junk folder; the verification email often appears in spam during testing.

Success response:

```json
{
  "success": true,
  "userConfirmed": false,
  "userSub": "cognito-sub",
  "username": "alice@example.com",
  "email": "alice@example.com",
  "message": "User signed up. Confirmation may be required."
}
```

Error response when the username already exists:

```json
{
  "success": false,
  "errorCode": "USERNAME_EXISTS",
  "message": "A user with this username already exists"
}
```

The frontend should sign the user in after account confirmation, then call `POST /users/me/face` with the Cognito JWT.

### Register My Face

```text
POST /users/me/face
```

This route requires a Cognito JWT.

Headers:

```text
Authorization: Bearer <ID_TOKEN>
Content-Type: application/json
```

Request from frontend:

```json
{
  "imageContentType": "image/jpeg",
  "faceImageBase64": "/9j/4AAQSkZJRgABAQ..."
}
```

`imageContentType` may be `image/jpeg` or `image/png`.

The backend gets the current user from Cognito token claims. The frontend does not need to send `userId`.

Success response:

```json
{
  "success": true,
  "user": {
    "userId": "cognito-sub",
    "username": "alice@example.com",
    "email": "alice@example.com",
    "displayName": "Alice"
  },
  "faceImage": {
    "bucket": "smart-fridge-user-faces-dev-491919374787",
    "s3Key": "user-faces/cognito-sub/profile-2026-06-03T10-00-00.000Z.jpg",
    "contentType": "image/jpeg"
  },
  "face": {
    "rekognitionCollectionId": "ml-smart-fridge-faces",
    "rekognitionFaceId": "rekognition-face-id",
    "confidence": 99.0
  },
  "message": "Face registration accepted"
}
```

The backend calls Rekognition `IndexFaces` and stores the returned `FaceId`.

Expected Rekognition integration input:

```json
{
  "collectionId": "ml-smart-fridge-faces",
  "externalImageId": "cognito-sub",
  "s3Object": {
    "bucket": "smart-fridge-user-faces-dev-491919374787",
    "name": "user-faces/cognito-sub/profile-2026-06-03T10-00-00.000Z.jpg"
  }
}
```

Expected Rekognition integration output:

```json
{
  "rekognitionCollectionId": "ml-smart-fridge-faces",
  "rekognitionFaceId": "rekognition-face-id",
  "confidence": 99.0
}
```

### User Face Mapping

Recommended table name:

```text
SmartFridgeUserFaces
```

Primary key:

```text
PK: userId
```

GSI for matching a Rekognition face back to a Cognito user:

```text
GSI name: FaceIdIndex
GSI partition key: rekognitionFaceId
```

Example item:

```json
{
  "userId": "cognito-sub",
  "username": "alice@example.com",
  "email": "alice@example.com",
  "displayName": "Alice",
  "faceImageBucket": "smart-fridge-user-faces-dev-491919374787",
  "faceImageS3Key": "user-faces/cognito-sub/profile-2026-06-03T10-00-00.000Z.jpg",
  "rekognitionCollectionId": "ml-smart-fridge-faces",
  "rekognitionFaceId": "rekognition-face-id",
  "imageContentType": "image/jpeg",
  "createdAt": "2026-06-03T10:00:00Z",
  "updatedAt": "2026-06-03T10:00:00Z"
}
```

## Raspberry Pi / HMI APIs

These APIs are called by the Raspberry Pi or HMI flow.

### Authenticate Face

```text
POST /auth/face
```

Request:

```json
{
  "deviceId": "smart-fridge-001",
  "action": "put",
  "imageContentType": "image/jpeg",
  "faceImageBase64": "/9j/4AAQSkZJRgABAQ..."
}
```

Allowed `action` values:

```text
put
retrieve
```

Success response:

```json
{
  "authenticated": true,
  "user": {
    "userId": "cognito-sub",
    "email": "alice@example.com",
    "displayName": "Alice"
  },
  "confidence": 96.4
}
```

Failure response:

```json
{
  "authenticated": false,
  "message": "Face not recognized"
}
```

### Put Food

```text
POST /foods/put
```

Request:

```json
{
  "deviceId": "smart-fridge-001",
  "userId": "cognito-sub",
  "foodImageContentType": "image/jpeg",
  "foodImageBase64": "/9j/4AAQSkZJRgABAQ...",
  "audioContentType": "audio/wav",
  "expirationAudioBase64": "UklGRiQAAABXQVZFZm10..."
}
```

Expiration input rules:

- Test voice and transcript phrases must use explicit relative durations, such as `三天後`, `兩週後`, `一個月後`, `two weeks later`, or `3 days later`.
- Avoid vague calendar words in tests, such as `明天`, `後天`, `下週`, `下個月`, `月底`, `tomorrow`, `next week`, or `next month`.
- Transcript text takes priority over audio. The backend checks `expirationTranscript`, `expirationTranscriptText`, and `transcriptText` first.
- If no transcript text is present, `expirationAudioS3Uri` is used before `expirationAudioBase64`.
- If `expirationDate` is also sent with transcript or audio input, the parsed expiration date takes priority.

Success response:

```json
{
  "success": true,
  "food": {
    "foodId": "food-uuid",
    "ownerUserId": "cognito-sub",
    "foodName": "milk",
    "expirationDate": "2026-06-10",
    "createdAt": "2026-06-03T10:00:00Z",
    "foodClassification": {
      "foodName": "milk",
      "confidence": 0.92
    },
    "expirationParsing": {
      "expirationDate": "2026-08-03",
      "expirationDuration": "P2M",
      "expirationDurationUnit": "months",
      "expirationDurationAmount": 2,
      "transcript": "兩個月後",
      "confidence": 0.95,
      "timezone": "Asia/Taipei"
    }
  }
}
```

### Retrieve Food

```text
POST /foods/retrieve
```

Request:

```json
{
  "deviceId": "smart-fridge-001",
  "userId": "cognito-sub",
  "foodImageContentType": "image/jpeg",
  "foodImageBase64": "/9j/4AAQSkZJRgABAQ..."
}
```

Success response when the food belongs to the current user:

```json
{
  "success": true,
  "authorized": true,
  "deletedFoodId": "food-uuid",
  "message": "Food retrieved"
}
```

Response when the food belongs to another user:

```json
{
  "success": false,
  "authorized": false,
  "food": {
    "foodId": "food-uuid",
    "foodName": "milk",
    "ownerUserId": "another-cognito-sub",
    "ownerEmail": "bob@example.com"
  },
  "message": "This food belongs to another user"
}
```

When `authorized` is `false`, Lambda should trigger SES email notification and update Device Shadow `desired.led` to `alert`.

Ownership limitation:

- This MVP can reliably check ownership when the retrieve request includes a specific `foodId`.
- If the retrieve request only includes a food image, the backend can classify the food type and identify the actor, but it cannot prove which physical item was taken when multiple users own matching items.
- Example: if A owns a cola and B also owns a cola, and B presents a cola image, the system cannot distinguish A's physical cola from B's physical cola without another item signal.
- Accurate physical-item ownership requires a unique item identifier or sensor signal, such as `foodId`, QR code, barcode, RFID tag, shelf/bin position, weight sensor event, or manual item selection.

## Frontend APIs

Frontend APIs use Cognito authentication. The backend gets the current user's Cognito `sub` from the JWT.

### Test Owner Check

```text
POST /test/owner-check
```

This route is for integration testing. Create the food item first with `POST /foods/put`, then pass that `foodId` here. The API recognizes the face image through Rekognition, maps the matched `FaceId` back to a Cognito user, then compares the recognized user with the existing food owner.

Request:

```json
{
  "foodId": "food-uuid",
  "imageContentType": "image/jpeg",
  "faceImageBase64": "/9j/4AAQSkZJRgABAQ..."
}
```

Success match:

```json
{
  "success": true,
  "result": "success",
  "authorized": true,
  "message": "Recognized user matches the food owner"
}
```

Failed match:

```json
{
  "success": false,
  "result": "fail",
  "authorized": false,
  "message": "Recognized user does not match the food owner"
}
```

### List My Foods

```text
GET /foods/me
```

Response:

```json
{
  "foods": [
    {
      "foodId": "food-uuid",
      "foodName": "milk",
      "expirationDate": "2026-06-10",
      "foodImage": {
        "s3Key": "food-images/cognito-sub/food-uuid.jpg",
        "contentType": "image/jpeg",
        "capturedAt": "2026-06-03T10:00:00Z",
        "dataUrl": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ..."
      },
      "deviceId": "smart-fridge-001",
      "createdAt": "2026-06-03T10:00:00Z"
    }
  ]
}
```

The backend returns foods sorted by earliest `expirationDate` first. Frontend should preserve that order when rendering the inventory list.

### Get Device State

```text
GET /device/{deviceId}/state
```

Example:

```text
GET /device/smart-fridge-001/state
```

Response:

```json
{
  "deviceId": "smart-fridge-001",
  "lock": "locked",
  "led": "off",
  "temperature": 4.2,
  "humidity": 55,
  "lastSeenAt": "2026-06-03T10:05:00Z"
}
```

### Update Lock Desired State

```text
POST /device/{deviceId}/lock
```

Example:

```text
POST /device/smart-fridge-001/lock
```

Request:

```json
{
  "desiredLock": "unlocked"
}
```

Allowed `desiredLock` values:

```text
locked
unlocked
```

Response:

```json
{
  "success": true,
  "desiredLock": "unlocked"
}
```

This API updates AWS IoT Device Shadow `desired.lock`.

## IoT Device Shadow Contract

Thing name:

```text
smart-fridge-001
```

Shadow document:

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
      "lastSeenAt": "2026-06-03T10:05:00Z"
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

### Frontend Lock Control Flow

1. Frontend calls `POST /device/smart-fridge-001/lock`.
2. Lambda updates Device Shadow `desired.lock`.
3. Raspberry Pi subscribes to Shadow delta.
4. Raspberry Pi receives the lock command and controls the physical lock.
5. Raspberry Pi updates Device Shadow `reported.lock`.

Lambda Shadow update:

```json
{
  "state": {
    "desired": {
      "lock": "unlocked"
    }
  }
}
```

Raspberry Pi receives delta:

```json
{
  "state": {
    "lock": "unlocked"
  }
}
```

Raspberry Pi reported update:

```json
{
  "state": {
    "reported": {
      "lock": "unlocked",
      "lastSeenAt": "2026-06-03T10:05:00Z"
    }
  }
}
```

### Temperature And Humidity Flow

Raspberry Pi periodically updates reported state:

```json
{
  "state": {
    "reported": {
      "temperature": 4.2,
      "humidity": 55,
      "lastSeenAt": "2026-06-03T10:05:00Z"
    }
  }
}
```

Frontend reads state through `GET /device/smart-fridge-001/state`.

### Unauthorized Retrieve LED Flow

1. Raspberry Pi calls `POST /foods/retrieve`.
2. Lambda identifies the food and checks the owner in DynamoDB.
3. If the current user is not the owner, Lambda sends an SES email to the owner.
4. Lambda updates Device Shadow `desired.led` to `alert`.
5. Raspberry Pi receives the Shadow delta and turns on the LED.
6. Raspberry Pi updates Device Shadow `reported.led`.
7. Raspberry Pi may turn the LED off after a short delay and report `led: off`.

Lambda Shadow update:

```json
{
  "state": {
    "desired": {
      "led": "alert"
    }
  }
}
```

Raspberry Pi reported update:

```json
{
  "state": {
    "reported": {
      "led": "alert"
    }
  }
}
```

Optional Raspberry Pi reset update:

```json
{
  "state": {
    "desired": {
      "led": "off"
    },
    "reported": {
      "led": "off"
    }
  }
}
```

## Development Notes

Recommended Cloud Architect branch:

```text
feature/cloud-architecture
```

Recommended initial PR order:

1. Backend folder structure and interface contract
2. DynamoDB and Cognito infrastructure
3. IoT Device Shadow setup and starter Lambdas
4. SES and full integration endpoints

Keep Cloud Architect changes inside `aws-backend/` unless the team agrees otherwise.
