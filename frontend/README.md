# Smart Fridge Frontend

This folder is reserved for the production frontend.

The current simple HTML/CSS/JS page has been moved to:

```text
frontend/test/
```

That page is only for API integration testing. Frontend developers can use it as a working example for:

- Cognito signup
- Cognito confirmation code
- Cognito login
- Uploading a user face image
- Creating a food item
- Testing whether a face matches the food owner

## Run The Test Page

From the repository root:

```bash
cd frontend/test
python3 -m http.server 5173
```

Open:

```text
http://localhost:5173
```

If serving from `frontend/` instead, open:

```text
http://localhost:5173/test/
```

## API Contract

Read this file before implementing the real frontend:

```text
../aws-backend/docs/frontend-api-contract.md
```

It includes:

- API Gateway base URL
- Cognito region and client id
- Request and response formats
- Which routes require a Cognito ID token
- How to call Cognito directly for confirm and login
- Owner check test flow

Architecture and current deployed resources are documented here:

```text
../aws-backend/docs/final-design.md
```

## Does The Frontend Developer Need The Same AWS CLI User?

No, not for normal frontend development.

The frontend developer does not need your AWS CLI user or your AWS secret keys to build the app. The frontend only needs these public integration values:

```text
API base URL
Cognito region
Cognito User Pool ID
Cognito User Pool Client ID
Default device id
```

Current values are in:

```text
../aws-backend/docs/frontend-api-contract.md
```

The frontend developer can create users, confirm users, log in, upload photos, and call the test APIs from the browser using those values.

They only need their own AWS CLI permissions if they want to do cloud administration work, such as:

- Deploying SAM or CloudFormation
- Reading or editing DynamoDB directly
- Viewing S3 uploaded face images
- Inspecting Cognito users in AWS
- Changing Lambda, API Gateway, Rekognition, IoT Core, or SES settings

For frontend-only work, do not share your AWS access key or secret key. Share the API contract and Cognito/API configuration instead.

## Recommended Frontend Flow

Signup and face registration:

```text
POST /auth/signup
Cognito ConfirmSignUp
Cognito InitiateAuth
POST /users/me/face with Authorization: Bearer <IdToken>
```

Owner check test:

```text
POST /foods/put
POST /test/owner-check with the returned foodId
```

Expected demo behavior:

- Owner is `gaga555lala@gmail.com`, face image is gaga: success.
- Owner is `gaga555lala@gmail.com`, face image is tim: fail, recognized user should be tim.
- Face image is an unknown person: `FACE_NOT_RECOGNIZED`.
