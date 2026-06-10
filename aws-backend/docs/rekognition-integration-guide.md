# Rekognition Integration Guide

This guide explains how the AI/ML integrator should connect Amazon Rekognition to the current Smart Fridge backend.

## Current Backend State

The backend already handles:

- Cognito signup through `POST /auth/signup`
- Cognito-protected face image upload through `POST /users/me/face`
- S3 storage for uploaded user face images
- DynamoDB mapping table for user-to-face records
- Rekognition `IndexFaces` in `POST /users/me/face`
- Rekognition `SearchFacesByImage` in `POST /auth/face`

Rekognition is now connected in the backend Lambda.

## Existing AWS Resources

```text
Region: ap-northeast-1
ApiBaseUrl: https://v6ylyjtxga.execute-api.ap-northeast-1.amazonaws.com/dev
UserPoolId: ap-northeast-1_HIySrbd1y
UserPoolClientId: 58u2jdcqh3l2r7or7uctogai9n
UserFaceTableName: SmartFridgeUserFaces-dev
FaceImageBucketName: smart-fridge-user-faces-dev-491919374787
```

Rekognition collection id:

```text
ml-smart-fridge-faces
```

## Face Registration Flow

Frontend calls:

```text
POST /users/me/face
```

Request:

```json
{
  "imageContentType": "image/jpeg",
  "faceImageBase64": "/9j/4AAQSkZJRgABAQ..."
}
```

`imageContentType` may be `image/jpeg` or `image/png`.

Current backend behavior:

1. Gets current user from Cognito JWT.
2. Calls Rekognition `IndexFaces`.
3. Saves the uploaded image to S3.
4. Writes a mapping item to `SmartFridgeUserFaces-dev`.
5. Stores the real `rekognitionFaceId`.

Current response shape:

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
    "confidence": 99
  },
  "message": "Face registration accepted"
}
```

## Current Implementation

`POST /users/me/face` calls Rekognition `IndexFaces`.

Use:

```text
Rekognition API: IndexFaces
CollectionId: ml-smart-fridge-faces
ExternalImageId: Cognito userId
Image: uploaded face image bytes
```

Input to Rekognition should look like:

```json
{
  "CollectionId": "ml-smart-fridge-faces",
  "ExternalImageId": "cognito-sub",
  "Image": {
    "Bytes": "base64 decoded image bytes"
  }
}
```

Expected useful output from Rekognition:

```json
{
  "FaceRecords": [
    {
      "Face": {
        "FaceId": "rekognition-face-id",
        "ExternalImageId": "cognito-sub",
        "Confidence": 99.9
      }
    }
  ]
}
```

Save these fields in `SmartFridgeUserFaces-dev`:

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

## Face Authentication Flow

Raspberry Pi calls:

```text
POST /auth/face
```

Current request:

```json
{
  "deviceId": "smart-fridge-001",
  "action": "retrieve",
  "imageContentType": "image/jpeg",
  "faceImageBase64": "/9j/4AAQSkZJRgABAQ..."
}
```

Current backend behavior:

1. Decode `faceImageBase64`.
2. Call Rekognition `SearchFacesByImage`.
3. Get up to 5 matching `FaceId` values above threshold.
4. Query `SmartFridgeUserFaces-dev` using `FaceIdIndex`.
5. Skip matches that do not have a Cognito mapping.
6. Return the first matched Cognito user.

Use:

```text
Rekognition API: SearchFacesByImage
CollectionId: ml-smart-fridge-faces
FaceMatchThreshold: 85
MaxFaces: 5
```

Expected Rekognition input:

```json
{
  "CollectionId": "ml-smart-fridge-faces",
  "Image": {
    "Bytes": "base64 decoded image bytes"
  },
  "FaceMatchThreshold": 85,
  "MaxFaces": 5
}
```

Expected Rekognition output:

```json
{
  "FaceMatches": [
    {
      "Similarity": 98.7,
      "Face": {
        "FaceId": "rekognition-face-id",
        "ExternalImageId": "cognito-sub"
      }
    }
  ]
}
```

Then query DynamoDB:

```text
Table: SmartFridgeUserFaces-dev
Index: FaceIdIndex
rekognitionFaceId = Face.FaceId
```

Return success:

```json
{
  "authenticated": true,
  "user": {
    "userId": "cognito-sub",
    "email": "alice@example.com",
    "displayName": "Alice"
  },
  "confidence": 98.7
}
```

Return failure:

```json
{
  "authenticated": false,
  "errorCode": "FACE_NOT_RECOGNIZED",
  "message": "Face not recognized"
}
```

## Owner Check For Food Retrieval

Food ownership should be checked by comparing user ids, not raw photos.

Correct comparison:

```text
recognizedUserId === food.ownerUserId
```

Flow:

1. Pi sends face image to `POST /auth/face`.
2. Backend returns recognized Cognito `userId`.
3. Pi or backend uses that `userId` during retrieve flow.
4. Retrieve logic compares recognized user with `ownerUserId`.

## Required IAM Permissions

The Lambda execution role needs Rekognition permissions:

```json
{
  "Effect": "Allow",
  "Action": [
    "rekognition:CreateCollection",
    "rekognition:DescribeCollection",
    "rekognition:IndexFaces",
    "rekognition:SearchFacesByImage"
  ],
  "Resource": "*"
}
```

The role also needs to read uploaded face images from S3:

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject"
  ],
  "Resource": "arn:aws:s3:::smart-fridge-user-faces-dev-491919374787/user-faces/*"
}
```

And it needs DynamoDB access to the user-face table:

```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:PutItem",
    "dynamodb:UpdateItem",
    "dynamodb:Query"
  ],
  "Resource": [
    "arn:aws:dynamodb:ap-northeast-1:491919374787:table/SmartFridgeUserFaces-dev",
    "arn:aws:dynamodb:ap-northeast-1:491919374787:table/SmartFridgeUserFaces-dev/index/*"
  ]
}
```

## Implementation Notes

- Do not store base64 images in DynamoDB.
- Store uploaded user photos in S3.
- Store only user id, face id, collection id, and S3 key in DynamoDB.
- Use Cognito `sub` as the stable user id.
- Use Rekognition `ExternalImageId = userId` when indexing faces.
- Use `FaceIdIndex` to map a recognized Rekognition `FaceId` back to a Cognito user.
- Keep the current response shape stable so frontend and Raspberry Pi code do not need to change.
