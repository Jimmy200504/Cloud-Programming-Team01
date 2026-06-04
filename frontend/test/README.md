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
