# Smart Fridge Deployment Outputs

Last updated: 2026-06-04

This document keeps the current deployed AWS output values in one place. For design details, read `final-design.md`. For frontend request and response formats, read `frontend-api-contract.md`.

## Region

```text
ap-northeast-1
```

## API Gateway

```text
ApiBaseUrl: https://v6ylyjtxga.execute-api.ap-northeast-1.amazonaws.com/dev
```

## Cognito

```text
UserPoolId: ap-northeast-1_HIySrbd1y
UserPoolClientId: 58u2jdcqh3l2r7or7uctogai9n
```

Frontend developers need these values for Cognito signup confirmation and login. They do not need the Cloud Architect AWS CLI user for normal frontend development.

## DynamoDB

```text
FoodTableName: SmartFridgeFoods-dev
UserFaceTableName: SmartFridgeUserFaces-dev
```

## S3

```text
FaceImageBucketName: smart-fridge-user-faces-dev-491919374787
```

## Rekognition

```text
CollectionId: ml-smart-fridge-faces
FaceMatchThreshold: 85
Search MaxFaces: 5
```

## IoT Core

```text
ThingName: smart-fridge-001
DevicePolicyName: smart-fridge-dev-device-policy
```

## Current Verified Behavior

- `POST /auth/signup` creates Cognito users.
- Cognito `ConfirmSignUp` and `InitiateAuth` are called directly by the frontend.
- `POST /users/me/face` indexes a real face in Rekognition, stores the uploaded image in S3, and stores the Cognito-to-FaceId mapping in DynamoDB.
- `POST /foods/put` creates a food item in DynamoDB.
- `POST /test/owner-check` loads an existing food item by `foodId`, searches faces in Rekognition, maps the matched face to Cognito, and checks whether the recognized user is the owner.
- Unknown faces return `FACE_NOT_RECOGNIZED`.
- Recognized users who are not the owner return `Recognized user does not match the food owner`.
