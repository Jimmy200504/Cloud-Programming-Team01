# Frontend API Test Page

This folder contains a small vanilla HTML/CSS/JS page for testing the deployed Smart Fridge APIs.

It is not the production frontend. Use it only as a reference implementation for API calls.

## Run

```bash
cd frontend/test
python3 -m http.server 5173
```

Open:

```text
http://localhost:5173
```

Optional local config override:

```bash
cp config.example.js config.js
```

Then edit `config.js` for a different API Gateway stage or Cognito client. `config.js` is ignored by git.

`config.js` is useful when testing another deployed stack or stage. It is loaded before `app.js` and can override:

```js
window.SMART_FRIDGE_CONFIG = {
  apiBaseUrl: "https://example.execute-api.ap-northeast-1.amazonaws.com/dev",
  region: "ap-northeast-1",
  userPoolClientId: "replace-with-cognito-client-id"
};
```

The override only affects the local browser test page. It does not change deployed AWS resources, Lambda environment variables, or SAM parameters.

For normal development against the current shared dev backend, do not create `config.js`; the default values in `app.js` are enough. After editing `config.js`, hard refresh the page so the browser reloads the script.

## Covered Flows

- `POST /auth/signup`
- Cognito `ConfirmSignUp`
- Cognito `ResendConfirmationCode`
- Cognito `InitiateAuth`
- `POST /users/me/face`
- Put food flow:
  - `POST /auth/face`
  - reserved hardware unlock signal through `POST /device/smart-fridge-001/lock`
  - `POST /foods/put`
- Retrieve food flow:
  - `POST /auth/face`
  - reserved hardware unlock signal through `POST /device/smart-fridge-001/lock`
  - `POST /foods/retrieve`
  - reserved hardware buzzer and owner email actions when ownership check fails

`POST /test/owner-check` still exists as a lower-level backend test route, but this page now separates the user-facing put and retrieve flows.

For the official frontend API contract, read:

```text
../../aws-backend/docs/frontend-api-contract.md
```
