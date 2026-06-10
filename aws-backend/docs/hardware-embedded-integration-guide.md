# Smart Fridge Hardware And Embedded Integration Guide

Last updated: 2026-06-04

This document is for the Hardware & Embedded Engineering owner. It explains how the Raspberry Pi, microphone, camera, lock, and LED should connect to the current cloud backend.

## After Pulling This Branch

Hardware engineers can read this guide and call the current shared dev API endpoints immediately, but the Raspberry Pi cannot connect to AWS IoT Core until it has device credentials.

API Gateway calls need:

```text
API base URL
JSON payloads
base64 encoded image/audio files
```

IoT Shadow MQTT calls need:

```text
AWS IoT endpoint
device certificate
private key
Amazon root CA
Thing attachment: smart-fridge-001
Policy attachment: smart-fridge-dev-device-policy
```

If you are using a different AWS account, stage, or device id, confirm these values with the cloud owner before coding:

```text
API base URL
AWS region
DeviceId / IoT Thing name
IoT policy name
MQTT client id
```

For local hardware development before MQTT is ready, you can still test camera and microphone upload by calling API Gateway over HTTPS. LED/lock behavior should be mocked locally until the IoT certificate and Shadow subscription are configured.

## Cloud Values

API base URL:

```text
https://v6ylyjtxga.execute-api.ap-northeast-1.amazonaws.com/dev
```

AWS region:

```text
ap-northeast-1
```

Device id / IoT Thing name:

```text
smart-fridge-001
```

IoT device policy:

```text
smart-fridge-dev-device-policy
```

## High-Level Rule

Use API Gateway for business events:

- face authentication
- food image classification
- expiration audio parsing
- putting food
- retrieving food
- ownership checks

Use AWS IoT Device Shadow only for device state and hardware commands:

- lock state
- LED state
- temperature
- humidity
- last seen timestamp

Do not put images, audio, or food records into Device Shadow.

## Payload Format Rules

Images and audio are sent to API Gateway as raw base64 strings inside JSON.

Do not include a data URL prefix.

Correct:

```text
/9j/4AAQSkZJRgABAQ...
```

Incorrect:

```text
data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ...
```

Supported image content types:

```text
image/jpeg
image/png
```

Supported expiration audio content types:

```text
audio/wav
audio/mpeg
audio/mp4
audio/m4a
audio/x-m4a
audio/flac
audio/ogg
audio/amr
audio/webm
```

For the most reliable microphone integration, use WAV or M4A if possible.

Expiration speech test phrases should use explicit relative durations:

```text
三天後
兩週後
一個月後
two weeks later
3 days later
```

Avoid vague calendar words during tests:

```text
明天
後天
下週
下個月
月底
tomorrow
next week
next month
```

## Camera To Cloud

The camera has two different jobs.

### User Face Photo

Use this when the device needs to recognize who is using the fridge.

Endpoint:

```text
POST /auth/face
```

Request:

```json
{
  "action": "put",
  "deviceId": "smart-fridge-001",
  "imageContentType": "image/jpeg",
  "faceImageBase64": "/9j/4AAQSkZJRgABAQ..."
}
```

For retrieve flow, use:

```json
{
  "action": "retrieve",
  "deviceId": "smart-fridge-001",
  "imageContentType": "image/jpeg",
  "faceImageBase64": "/9j/4AAQSkZJRgABAQ..."
}
```

Success response:

```json
{
  "authenticated": true,
  "user": {
    "userId": "cognito-sub",
    "email": "owner@example.com",
    "displayName": "Owner"
  },
  "confidence": 99.8
}
```

The embedded flow should keep `user.userId` and `user.email` for the next API call.

### Food Photo

Use this when the device captures the food item being put into or retrieved from the fridge.

For put-food flow, send the food photo to:

```text
POST /foods/put
```

For retrieve-food flow, send the food photo to:

```text
POST /foods/retrieve
```

The backend stores food images in S3 and stores only metadata in DynamoDB. The hardware should not upload food images directly to S3 in the MVP.

## Microphone Audio To Cloud

The microphone records the expiration duration, for example `三個月後`.

There are two supported integration styles.

### Option A: Parse Audio First

Endpoint:

```text
POST /expiration/parse
```

Request:

```json
{
  "audioContentType": "audio/wav",
  "expirationAudioBase64": "UklGRiQAAABXQVZFZm10...",
  "capturedAt": "2026-06-04T22:30:00+08:00",
  "timezone": "Asia/Taipei"
}
```

Response:

```json
{
  "success": true,
  "expiration": {
    "expirationDate": "2026-09-04",
    "expirationDuration": "P3M",
    "expirationDurationUnit": "months",
    "expirationDurationAmount": 3,
    "transcript": "三個月後",
    "timezone": "Asia/Taipei"
  }
}
```

The hardware/HMI can then use `expiration.expirationDate` in the `/foods/put` request.

### Option B: Send Audio With Put Food

Endpoint:

```text
POST /foods/put
```

Request:

```json
{
  "deviceId": "smart-fridge-001",
  "userId": "cognito-sub-from-face-auth",
  "ownerUserId": "cognito-sub-from-face-auth",
  "ownerEmail": "owner@example.com",
  "foodImageContentType": "image/jpeg",
  "foodImageBase64": "/9j/4AAQSkZJRgABAQ...",
  "audioContentType": "audio/wav",
  "expirationAudioBase64": "UklGRiQAAABXQVZFZm10...",
  "capturedAt": "2026-06-04T22:30:00+08:00",
  "timezone": "Asia/Taipei",
  "recordType": "put-flow-test"
}
```

The backend will classify the food image, transcribe and parse the expiration audio, store the food item in DynamoDB, and store the food image in S3.

If both transcript text and audio are sent, transcript text wins. The backend checks:

```text
expirationTranscript / expirationTranscriptText / transcriptText
expirationAudioS3Uri
expirationAudioBase64
```

## Recommended Put-Food Hardware Flow

1. Capture user's face image.
2. Call `POST /auth/face` with `action: "put"`.
3. If `authenticated` is false, do not continue.
4. Capture the food image.
5. Record microphone audio for expiration duration.
6. Call `POST /foods/put` with recognized user id/email, food image, and expiration audio.
7. Show success/failure on the device UI.

Important: The cloud currently expects a registered face. User signup, email confirmation, and face registration are handled by the frontend/test UI, not by the hardware flow.

## Recommended Retrieve-Food Hardware Flow

1. Capture user's face image.
2. Call `POST /auth/face` with `action: "retrieve"`.
3. If `authenticated` is false, do not unlock.
4. Capture the food image.
5. Call `POST /foods/retrieve` with the recognized actor and food image.
6. Only unlock if the response has `authorized: true`.
7. If `authorized: false`, do not unlock. The backend will request alert actions.

Request:

```json
{
  "deviceId": "smart-fridge-001",
  "actorUserId": "recognized-user-id",
  "actorEmail": "recognized-user@example.com",
  "userId": "recognized-user-id",
  "actorDisplayName": "Recognized User",
  "foodImageContentType": "image/jpeg",
  "foodImageBase64": "/9j/4AAQSkZJRgABAQ..."
}
```

Authorized response:

```json
{
  "success": true,
  "authorized": true,
  "deletedFoodId": "food-uuid",
  "message": "Recognized User took cola"
}
```

Unauthorized response:

```json
{
  "success": false,
  "authorized": false,
  "message": "This food belongs to another user",
  "hardwareActions": [
    {
      "type": "hardware-buzzer",
      "status": "requested"
    },
    {
      "type": "owner-email",
      "status": "requested",
      "ownerEmail": "owner@example.com"
    }
  ]
}
```

Ownership limitation:

- If the request identifies a specific `foodId`, ownership can be checked accurately.
- If the request only sends a food photo, the backend can identify the food type and actor, but cannot prove which physical item was taken when multiple users own the same food type.
- Example: if A owns a cola and B owns a cola, a cola photo alone cannot distinguish A's bottle from B's bottle.
- A production-safe flow needs `foodId`, QR code, barcode, RFID, shelf/bin position, weight sensor event, or manual item selection.

## LED Alert Through IoT Device Shadow

The cloud writes LED commands to Device Shadow when a non-owner tries to retrieve food.

Expected shadow state:

```json
{
  "state": {
    "desired": {
      "lock": "unlocked",
      "led": "alert"
    },
    "reported": {
      "lock": "locked",
      "led": "off",
      "temperature": 4.2,
      "humidity": 55,
      "lastSeenAt": "2026-06-04T22:30:00+08:00"
    }
  }
}
```

Allowed LED values:

```text
off
alert
```

The Raspberry Pi should subscribe to Device Shadow delta topics:

```text
$aws/things/smart-fridge-001/shadow/update/delta
```

When the Pi receives:

```json
{
  "state": {
    "led": "alert"
  }
}
```

it should make the LED blink.

After the LED starts blinking, the Pi should report:

```json
{
  "state": {
    "reported": {
      "led": "alert",
      "lastSeenAt": "2026-06-04T22:30:00+08:00"
    }
  }
}
```

After the alert timeout, the Pi may turn the LED off and report:

```json
{
  "state": {
    "reported": {
      "led": "off",
      "lastSeenAt": "2026-06-04T22:30:10+08:00"
    },
    "desired": {
      "led": "off"
    }
  }
}
```

The Pi should also handle lock deltas:

```json
{
  "state": {
    "lock": "unlocked"
  }
}
```

When it unlocks or locks the physical lock, report:

```json
{
  "state": {
    "reported": {
      "lock": "unlocked",
      "lastSeenAt": "2026-06-04T22:30:00+08:00"
    }
  }
}
```

## Device Shadow Topics

Subscribe:

```text
$aws/things/smart-fridge-001/shadow/update/delta
$aws/things/smart-fridge-001/shadow/update/accepted
$aws/things/smart-fridge-001/shadow/update/rejected
```

Publish reported state:

```text
$aws/things/smart-fridge-001/shadow/update
```

Get current shadow:

```text
$aws/things/smart-fridge-001/shadow/get
```

Get response:

```text
$aws/things/smart-fridge-001/shadow/get/accepted
$aws/things/smart-fridge-001/shadow/get/rejected
```

## Device Certificate Setup

CloudFormation creates the IoT Thing and IoT Policy, but the Raspberry Pi still needs its own IoT certificate and private key.

Create a certificate in AWS IoT Core, then attach:

```text
Thing: smart-fridge-001
Policy: smart-fridge-dev-device-policy
```

The policy allows the Pi to connect as client id `smart-fridge-001` and use the shadow topics for this thing.

## API Call Notes For Embedded Code

All API Gateway requests are JSON:

```text
Content-Type: application/json
```

For MVP test routes, `/auth/face`, `/foods/put`, `/foods/retrieve`, and `/expiration/parse` do not require AWS credentials from the device. They are API Gateway HTTPS calls.

Do not put AWS secret keys in frontend or embedded code unless the hardware owner is explicitly building an AWS IoT client with a device certificate.

## Minimal Python Base64 Example

```python
import base64
import requests

API_BASE_URL = "https://v6ylyjtxga.execute-api.ap-northeast-1.amazonaws.com/dev"

def file_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

face_base64 = file_to_base64("face.jpg")

response = requests.post(
    f"{API_BASE_URL}/auth/face",
    json={
        "action": "retrieve",
        "deviceId": "smart-fridge-001",
        "imageContentType": "image/jpeg",
        "faceImageBase64": face_base64,
    },
    timeout=30,
)

print(response.status_code)
print(response.json())
```

## Current Cloud-Tested Status

The cloud side has already been tested for:

- Lambda reading IoT Device Shadow reported state.
- Lambda writing Device Shadow desired lock state.
- Device Shadow delta appearing for the Raspberry Pi to consume.
- SES owner alert sending when sender and recipient constraints are satisfied.

The hardware side still needs to implement:

- camera capture and JPEG/PNG encoding
- microphone recording and supported audio encoding
- API Gateway HTTPS calls
- IoT Core MQTT connection with device certificate
- Shadow delta handling for lock and LED
- reported state updates after hardware action
