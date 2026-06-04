# Smart Fridge Frontend Integration Guide

Last updated: 2026-06-04

This guide is for the developer who will build the real frontend with React, Vue, Svelte, Angular, Next.js, Nuxt, or any other frontend framework.

The page in `frontend/test/` is only an API test page. Treat it as a working reference for request payloads, not as the production UI architecture.

## Frontend Scope

The production frontend should own these user-facing flows:

- Register a user account.
- Confirm the Cognito verification code.
- Log in and store the Cognito ID token.
- Upload the signed-in user's face image.
- Add food for the signed-in user.
- Optionally detect food name from a food photo.
- Optionally parse expiration date from text or audio.
- Show the signed-in user's fridge inventory.
- Display each item with food name, captured food photo, expiration date, and soonest-expiring order.

The frontend does not need AWS access keys. It only calls API Gateway and Cognito public browser APIs.

## Configuration

Create one frontend config module, for example `src/config.ts`.

```ts
export const config = {
  apiBaseUrl: "https://v6ylyjtxga.execute-api.ap-northeast-1.amazonaws.com/dev",
  cognitoRegion: "ap-northeast-1",
  cognitoClientId: "58u2jdcqh3l2r7or7uctogai9n",
  defaultDeviceId: "smart-fridge-001"
};
```

Do not hardcode these values across components. Import the config from one place so the frontend can switch between dev and production later.

## Recommended App Structure

Use any framework, but keep the responsibilities separated like this:

```text
src/
  api/
    smartFridgeApi.ts
    cognitoApi.ts
  auth/
    authStore.ts
    token.ts
  features/
    signup/
    login/
    face-registration/
    food-create/
    inventory/
  utils/
    fileToBase64.ts
```

Suggested screens:

- `SignupPage`: account creation and confirmation code.
- `LoginPage`: email/password login.
- `FaceRegistrationPage`: upload or capture face image.
- `AddFoodPage`: create food manually, or use photo/audio helpers.
- `InventoryPage`: signed-in user's fridge items.

## Auth State

After Cognito login, store at least:

```ts
type AuthSession = {
  idToken: string;
  accessToken: string;
  refreshToken?: string;
  expiresAt: number;
  user: {
    userId: string; // Cognito ID token `sub`
    email: string;
    displayName?: string;
  };
};
```

Use the Cognito ID token for backend requests:

```http
Authorization: Bearer <IdToken>
```

The backend uses the ID token `sub` as the real user id. When creating food for the signed-in user, send that same `sub` as `userId`.

## Shared API Helper

Create a small JSON request helper.

```ts
async function apiJson<T>(
  path: string,
  options: {
    method?: "GET" | "POST";
    token?: string;
    body?: unknown;
  } = {}
): Promise<T> {
  const response = await fetch(`${config.apiBaseUrl}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {})
    },
    body: options.body ? JSON.stringify(options.body) : undefined
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.message || `HTTP ${response.status}`);
  }

  return data as T;
}
```

Important: Some valid app-level results return HTTP 200 with `success: false`, such as owner-check mismatch. Do not blindly throw just because `success` is false. Let each feature decide how to display those results.

## File To Base64

The backend expects raw base64 only. Remove the `data:image/...;base64,` prefix before sending.

```ts
export async function fileToBase64(file: File): Promise<string> {
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });

  return dataUrl.split(",")[1] || "";
}
```

Supported image types:

```text
image/jpeg
image/png
```

Supported expiration audio types include:

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

For file pickers, allow common extensions:

```html
<input type="file" accept="audio/*,.wav,.mp3,.m4a,.mp4,.flac,.ogg,.amr,.webm" />
```

## Flow 1: Register User

Call the backend signup route:

```ts
await apiJson("/auth/signup", {
  method: "POST",
  body: {
    username: email,
    email,
    password,
    displayName
  }
});
```

Then show a confirmation-code form.

Confirm directly with Cognito:

```ts
await fetch("https://cognito-idp.ap-northeast-1.amazonaws.com/", {
  method: "POST",
  headers: {
    "Content-Type": "application/x-amz-json-1.1",
    "X-Amz-Target": "AWSCognitoIdentityProviderService.ConfirmSignUp"
  },
  body: JSON.stringify({
    ClientId: config.cognitoClientId,
    Username: email,
    ConfirmationCode: code
  })
});
```

After confirmation, send the user to login.

## Flow 2: Login

Call Cognito directly:

```ts
const response = await fetch("https://cognito-idp.ap-northeast-1.amazonaws.com/", {
  method: "POST",
  headers: {
    "Content-Type": "application/x-amz-json-1.1",
    "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth"
  },
  body: JSON.stringify({
    ClientId: config.cognitoClientId,
    AuthFlow: "USER_PASSWORD_AUTH",
    AuthParameters: {
      USERNAME: email,
      PASSWORD: password
    }
  })
});
```

The response contains:

```ts
type CognitoLoginResponse = {
  AuthenticationResult: {
    IdToken: string;
    AccessToken: string;
    RefreshToken?: string;
    ExpiresIn: number;
    TokenType: "Bearer";
  };
};
```

Decode the ID token payload in the browser to get `sub` and `email`.

```ts
export function decodeJwtPayload(token: string) {
  const payload = token.split(".")[1];
  return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
}
```

Store the session in your framework's state store and optionally in `localStorage`.

## Flow 3: Upload Face

This registers the current user's face for Rekognition owner matching.

```ts
const faceImageBase64 = await fileToBase64(file);

const result = await apiJson("/users/me/face", {
  method: "POST",
  token: session.idToken,
  body: {
    imageContentType: file.type,
    faceImageBase64
  }
});
```

Frontend rules:

- Require login before this screen.
- Only allow JPEG or PNG.
- Show success when `result.success === true`.
- The frontend does not send `userId`; the backend reads it from the ID token.

## Flow 4: Add Food

The simplest production create-food flow is manual input:

```ts
await apiJson("/foods/put", {
  method: "POST",
  body: {
    foodName,
    expirationDate,
    ownerEmail: session.user.email,
    userId: session.user.userId,
    deviceId: config.defaultDeviceId
  }
});
```

After a successful create, immediately refresh inventory:

```ts
await loadInventory();
```

Do not wait for the user to reload the page.

## Flow 5: Add Food With Photo Classification

If the add-food page lets the user upload a food photo, send it to `/foods/put` together with owner info.

```ts
const foodImageBase64 = await fileToBase64(foodImageFile);

const result = await apiJson("/foods/put", {
  method: "POST",
  body: {
    ownerEmail: session.user.email,
    userId: session.user.userId,
    expirationDate,
    foodImageContentType: foodImageFile.type,
    foodImageBase64,
    deviceId: config.defaultDeviceId
  }
});
```

The backend will:

- Run Rekognition labels.
- Ask Bedrock to map the labels to the food catalog.
- Store the captured food image in S3.
- Store only image metadata in DynamoDB.
- Return the created food item.

If the user manually edits the food name after classification, send `foodName` too. The backend can still keep the classification metadata.

## Flow 6: Parse Expiration Date

For typed text, call:

```ts
const result = await apiJson("/expiration/parse", {
  method: "POST",
  body: {
    expirationTranscript: "兩個月後",
    capturedAt: new Date().toISOString(),
    timezone: "Asia/Taipei"
  }
});
```

For audio:

```ts
const expirationAudioBase64 = await fileToBase64(audioFile);

const result = await apiJson("/expiration/parse", {
  method: "POST",
  body: {
    audioContentType: audioFile.type || "audio/x-m4a",
    expirationAudioBase64,
    capturedAt: new Date().toISOString(),
    timezone: "Asia/Taipei"
  }
});
```

Use `result.expiration.expirationDate` to fill the expiration date input.

The backend supports Chinese speech/text such as `兩個月後`, as well as English such as `two months later`.

## Flow 7: Add Food With Expiration Audio

You can combine food creation and expiration audio in one `/foods/put` call:

```ts
const expirationAudioBase64 = await fileToBase64(audioFile);

await apiJson("/foods/put", {
  method: "POST",
  body: {
    foodName,
    ownerEmail: session.user.email,
    userId: session.user.userId,
    audioContentType: audioFile.type || "audio/x-m4a",
    expirationAudioBase64,
    capturedAt: new Date().toISOString(),
    timezone: "Asia/Taipei",
    deviceId: config.defaultDeviceId
  }
});
```

The backend will parse the expiration date and store the resulting `expirationDate`.

## Flow 8: Show My Fridge Inventory

Call this after login, after face registration if your UI returns to the home page, and after every successful food create.

```ts
type FoodItem = {
  foodId: string;
  foodName?: string;
  expirationDate?: string;
  deviceId?: string;
  createdAt?: string;
  foodImage?: {
    s3Key?: string;
    contentType?: string;
    capturedAt?: string;
    dataUrl?: string;
  };
  foodClassification?: {
    foodName?: string;
    displayName?: string;
    confidence?: number;
    matchedCatalogId?: string;
  };
};

const result = await apiJson<{ foods: FoodItem[] }>("/foods/me", {
  token: session.idToken
});
```

Render rules:

- Show `food.foodName` first.
- If `food.foodName` is missing, show `food.foodClassification?.displayName`.
- Show `food.foodImage?.dataUrl` as the captured food photo.
- If `dataUrl` is missing, show an empty image placeholder.
- Show `expirationDate` in `YYYY-MM-DD`.
- The backend returns foods ordered by soonest expiration first.
- The frontend may sort again defensively, but should not reverse the API order.

Example display selector:

```ts
function getFoodDisplayName(food: FoodItem) {
  return food.foodName || food.foodClassification?.displayName || "Unknown food";
}
```

## Owner Check

`POST /test/owner-check` is an integration-test route, not the normal inventory UI.

Use it only if the frontend needs a demo/admin page for validating face ownership:

```ts
const faceImageBase64 = await fileToBase64(faceFile);

const result = await apiJson("/test/owner-check", {
  method: "POST",
  body: {
    foodId,
    imageContentType: faceFile.type,
    faceImageBase64
  }
});
```

Expected result handling:

- `success: true`, `authorized: true`: recognized user is the food owner.
- `success: false`, `authorized: false`: recognized user is not the owner or face is unknown.
- `errorCode: "FACE_NOT_RECOGNIZED"`: show an unknown-face message.

## API Matrix

| Feature | Method | Route | Auth |
| --- | --- | --- | --- |
| Signup | `POST` | `/auth/signup` | No |
| Confirm signup | `POST` | Cognito `ConfirmSignUp` | No |
| Login | `POST` | Cognito `InitiateAuth` | No |
| Upload face | `POST` | `/users/me/face` | ID token |
| Create food | `POST` | `/foods/put` | No in current MVP, still send current user fields |
| Detect food only | `POST` | `/foods/detect` | No |
| Parse expiration | `POST` | `/expiration/parse` | No |
| List my foods | `GET` | `/foods/me` | ID token |
| Owner check test | `POST` | `/test/owner-check` | No |

## Production UI Notes

- Protect inventory and face-registration routes behind login.
- Keep auth/session state centralized instead of passing tokens through many components.
- Disable submit buttons while requests are in progress.
- Validate file type before upload.
- Validate expiration date format as `YYYY-MM-DD`.
- Refresh `/foods/me` after creating a food item.
- Do not call S3 directly from the browser for food photos; use `foodImage.dataUrl` from `/foods/me`.
- Do not expose AWS secret keys in frontend code.
- Use user-friendly error messages, but keep `errorCode` visible in debug/admin mode.

## Source Of Truth

For exact request and response examples, use:

```text
../aws-backend/docs/frontend-api-contract.md
```

For deployed architecture and resource names, use:

```text
../aws-backend/docs/final-design.md
```
