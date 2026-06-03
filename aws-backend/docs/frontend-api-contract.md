# Smart Fridge Frontend API Contract

Last updated: 2026-06-04

This document describes how the frontend should call the current Smart Fridge cloud backend.

## Base Configuration

API Gateway base URL:

```text
https://v6ylyjtxga.execute-api.ap-northeast-1.amazonaws.com/dev
```

Cognito:

```text
Region: ap-northeast-1
UserPoolId: ap-northeast-1_HIySrbd1y
UserPoolClientId: 58u2jdcqh3l2r7or7uctogai9n
```

Default device id:

```text
smart-fridge-001
```

All API Gateway requests use:

```text
Content-Type: application/json
```

Base64 image strings must not include a data URL prefix.

Correct:

```text
iVBORw0KGgoAAAANSUhEUg...
```

Incorrect:

```text
data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...
```

Supported image content types:

```text
image/jpeg
image/png
```

## Error Format

Most backend errors use:

```json
{
  "success": false,
  "errorCode": "INVALID_IMAGE",
  "message": "Image must be a base64 encoded JPEG or PNG"
}
```

Common error codes:

```text
INVALID_SIGNUP_REQUEST
USERNAME_EXISTS
INVALID_PASSWORD
INVALID_IMAGE
INVALID_AUDIO
FACE_NOT_RECOGNIZED
USER_NOT_FOUND
FACE_REGISTRATION_FAILED
FOOD_NOT_FOUND
INVALID_LOCK_STATE
INTERNAL_ERROR
```

Important frontend rule:

- Some valid test results return HTTP 200 with `"success": false`, such as owner mismatch.
- Do not treat every `"success": false` as a network error.
- Show the returned `message`, `errorCode`, `recognizedUser`, and `food` when available.

## 1. Sign Up

Endpoint:

```text
POST /auth/signup
```

Full URL:

```text
https://v6ylyjtxga.execute-api.ap-northeast-1.amazonaws.com/dev/auth/signup
```

Authentication:

```text
None
```

Request:

```json
{
  "username": "alice@example.com",
  "email": "alice@example.com",
  "password": "TestPassword123",
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

Username already exists:

```json
{
  "success": false,
  "errorCode": "USERNAME_EXISTS",
  "message": "A user with this username already exists"
}
```

## 2. Confirm Sign Up

This is called directly to Cognito, not to API Gateway.

Cognito target:

```text
AWSCognitoIdentityProviderService.ConfirmSignUp
```

URL:

```text
https://cognito-idp.ap-northeast-1.amazonaws.com/
```

Headers:

```text
Content-Type: application/x-amz-json-1.1
X-Amz-Target: AWSCognitoIdentityProviderService.ConfirmSignUp
```

Request:

```json
{
  "ClientId": "58u2jdcqh3l2r7or7uctogai9n",
  "Username": "alice@example.com",
  "ConfirmationCode": "123456"
}
```

Success response is usually an empty object:

```json
{}
```

## 3. Resend Confirmation Code

This is called directly to Cognito.

Cognito target:

```text
AWSCognitoIdentityProviderService.ResendConfirmationCode
```

Request:

```json
{
  "ClientId": "58u2jdcqh3l2r7or7uctogai9n",
  "Username": "alice@example.com"
}
```

## 4. Login

This is called directly to Cognito.

Cognito target:

```text
AWSCognitoIdentityProviderService.InitiateAuth
```

Request:

```json
{
  "ClientId": "58u2jdcqh3l2r7or7uctogai9n",
  "AuthFlow": "USER_PASSWORD_AUTH",
  "AuthParameters": {
    "USERNAME": "alice@example.com",
    "PASSWORD": "TestPassword123"
  }
}
```

Success response shape:

```json
{
  "AuthenticationResult": {
    "AccessToken": "access-token",
    "ExpiresIn": 3600,
    "IdToken": "id-token",
    "RefreshToken": "refresh-token",
    "TokenType": "Bearer"
  }
}
```

Frontend should store the `IdToken` and send it to backend routes that require Cognito auth.

Authenticated backend header:

```text
Authorization: Bearer <IdToken>
```

## 5. Upload Current User Face

Endpoint:

```text
POST /users/me/face
```

Authentication:

```text
Required: Cognito ID token
```

Headers:

```text
Authorization: Bearer <IdToken>
Content-Type: application/json
```

Request:

```json
{
  "imageContentType": "image/png",
  "faceImageBase64": "iVBORw0KGgoAAAANSUhEUg..."
}
```

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
    "s3Key": "user-faces/cognito-sub/profile-2026-06-04T00-00-00.000Z.png",
    "contentType": "image/png"
  },
  "face": {
    "rekognitionCollectionId": "ml-smart-fridge-faces",
    "rekognitionFaceId": "rekognition-face-id",
    "confidence": 99.9
  },
  "message": "Face registration accepted"
}
```

Notes:

- The frontend does not send `userId`; backend reads it from the Cognito token.
- A registered user can upload a face again.
- The latest DynamoDB mapping for that user will point to the latest `rekognitionFaceId`.

## 6. Create Food Item

Endpoint:

```text
POST /foods/put
```

Authentication:

```text
None in the current MVP route
```

Minimal request for frontend owner-check testing:

```json
{
  "foodName": "milk",
  "ownerEmail": "alice@example.com",
  "expirationDate": "2026-06-10",
  "recordType": "owner-check-test"
}
```

Optional request with owner user id:

```json
{
  "foodName": "milk",
  "ownerEmail": "alice@example.com",
  "ownerUserId": "cognito-sub",
  "expirationDate": "2026-06-10",
  "deviceId": "smart-fridge-001"
}
```

Success response:

```json
{
  "success": true,
  "food": {
    "foodId": "food-uuid",
    "ownerUserId": "email#alice@example.com",
    "foodName": "milk",
    "expirationDate": "2026-06-10",
    "createdAt": "2026-06-04T00:00:00.000Z"
  }
}
```

Frontend should keep `food.foodId` for owner check.

## 7. Test Owner Check

Endpoint:

```text
POST /test/owner-check
```

Authentication:

```text
None in the current MVP route
```

Purpose:

Use this route to test whether a face image belongs to the owner of an existing food item.

Required flow:

1. Create the food with `POST /foods/put`.
2. Use the returned `foodId`.
3. Call `POST /test/owner-check` with `foodId` and face image.

Request:

```json
{
  "foodId": "food-uuid",
  "imageContentType": "image/jpeg",
  "faceImageBase64": "/9j/4AAQSkZJRgABAQ..."
}
```

Success when the recognized user is the owner:

```json
{
  "success": true,
  "result": "success",
  "authorized": true,
  "message": "Recognized user matches the food owner",
  "food": {
    "foodId": "food-uuid",
    "ownerEmail": "alice@example.com",
    "ownerUserId": "email#alice@example.com",
    "foodName": "milk",
    "expirationDate": "2026-06-10"
  },
  "recognizedUser": {
    "userId": "cognito-sub",
    "email": "alice@example.com",
    "displayName": "Alice"
  },
  "face": {
    "rekognitionCollectionId": "ml-smart-fridge-faces",
    "rekognitionFaceId": "rekognition-face-id",
    "confidence": 100
  }
}
```

Fail when the recognized user is not the owner:

```json
{
  "success": false,
  "result": "fail",
  "authorized": false,
  "message": "Recognized user does not match the food owner",
  "recognizedUser": {
    "userId": "another-cognito-sub",
    "email": "bob@example.com",
    "displayName": "Bob"
  }
}
```

Fail when no known face is found above threshold:

```json
{
  "success": false,
  "result": "fail",
  "authorized": false,
  "errorCode": "FACE_NOT_RECOGNIZED",
  "message": "Face not recognized"
}
```

Fail when the food id does not exist:

```json
{
  "success": false,
  "result": "fail",
  "authorized": false,
  "errorCode": "FOOD_NOT_FOUND",
  "message": "Food item was not found"
}
```

## 8. List My Foods

Endpoint:

```text
GET /foods/me
```

Authentication:

```text
Required: Cognito ID token
```

Headers:

```text
Authorization: Bearer <IdToken>
```

Response:

```json
{
  "foods": [
    {
      "foodId": "food-uuid",
      "foodName": "milk",
      "expirationDate": "2026-06-10",
      "deviceId": "smart-fridge-001",
      "createdAt": "2026-06-04T00:00:00.000Z"
    }
  ]
}
```

## 9. Authenticate Face

Endpoint:

```text
POST /auth/face
```

Authentication:

```text
None in the current MVP route
```

This API is intended for the Raspberry Pi or HMI flow.

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
  "confidence": 99.5,
  "face": {
    "rekognitionCollectionId": "ml-smart-fridge-faces",
    "rekognitionFaceId": "rekognition-face-id"
  }
}
```

Failure response:

```json
{
  "authenticated": false,
  "errorCode": "FACE_NOT_RECOGNIZED",
  "message": "Face not recognized"
}
```

## 10. Get Device State

Endpoint:

```text
GET /device/{deviceId}/state
```

Authentication:

```text
Required: Cognito ID token
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
  "lastSeenAt": "2026-06-04T00:00:00.000Z"
}
```

## 11. Update Lock

Endpoint:

```text
POST /device/{deviceId}/lock
```

Authentication:

```text
Required: Cognito ID token
```

Request:

```json
{
  "desiredLock": "unlocked"
}
```

Allowed values:

```text
locked
unlocked
```

Success response:

```json
{
  "success": true,
  "deviceId": "smart-fridge-001",
  "desiredLock": "unlocked"
}
```

## Frontend Example Flow

Signup and face registration:

```text
POST /auth/signup
ConfirmSignUp directly to Cognito
InitiateAuth directly to Cognito
POST /users/me/face with Authorization: Bearer <IdToken>
```

Owner check demo:

```text
POST /foods/put
POST /test/owner-check with returned foodId
```

Expected demo cases:

- Owner is `gaga555lala@gmail.com`, face image is gaga: `success`.
- Owner is `gaga555lala@gmail.com`, face image is tim: `fail`, recognized user should be tim.
- Owner is any registered user, face image is unknown person: `FACE_NOT_RECOGNIZED`.
