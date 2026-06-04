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
- Viewing the signed-in user's fridge inventory
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
INTEGRATION_GUIDE.md
```

It explains how a production frontend should structure auth state, API helpers, file uploads, face registration, food creation, expiration parsing, and inventory rendering when using React, Vue, Svelte, Angular, Next.js, Nuxt, or another framework.

For exact backend request and response examples, also read:

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

Inventory:

```text
After Cognito InitiateAuth, save the IdToken.
Decode the IdToken payload and keep `sub` as the current user id.
Call GET /foods/me with Authorization: Bearer <IdToken>.
Render foods in the order returned by the API.
```

Inventory item UI requirements:

```text
foodName or foodClassification.displayName
foodImage.dataUrl as the captured food photo
expirationDate
```

The inventory list must show only the signed-in user's foods and be ordered by soonest expiration first. The backend query uses `ownerUserId`, so when the frontend creates a food item for the signed-in user it should include:

```json
{
  "userId": "<IdToken sub>",
  "ownerEmail": "<signed-in email>"
}
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
