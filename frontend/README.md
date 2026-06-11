# Smart Fridge Frontend

This is the production React/Vite workspace for the Smart Fridge UI. The legacy vanilla API test page remains in `frontend/test/`.

## Run Locally

From the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Routes:

```text
http://localhost:5173
```

Shows the main user-facing console with face registration and inventory.
It also includes the current device climate panel for temperature and humidity.

```text
http://localhost:5173/dev
```

Shows the full development console with device climate, put-food, retrieve-food, and API telemetry panels.

The app uses the current shared dev backend by default. To point it at another stack:

```bash
cp .env.example .env.local
```

Then edit `.env.local`.

## Project Layout

```text
frontend/
  index.html
  package.json
  vite.config.js
  src/
    api/
      cognitoApi.js
      http.js
      smartFridgeApi.js
    auth/
      sessionStore.js
    components/
      AuthPanel.jsx
      CommandHeader.jsx
      FaceRegistrationPanel.jsx
      FilePreview.jsx
      InventoryPanel.jsx
      PutFoodPanel.jsx
      ResultConsole.jsx
      RetrieveFoodPanel.jsx
      StatusBadge.jsx
    utils/
      fileToBase64.js
      food.js
      format.js
    App.jsx
    config.js
    main.jsx
    styles.css
```

## Covered Flows

- Initial screen is a sign-in gate. Users must sign in before inventory, face registration, put-food, retrieve-food, and telemetry panels are shown.
- The signup button opens the account creation and confirmation flow for users without an account.
- Cognito signup, confirmation, resend code, and login.
- Cognito ID token persistence in `localStorage`.
- Face image registration through `POST /users/me/face`.
- User inventory loading through `GET /foods/me`.
- Device temperature and humidity loading through `GET /device/{deviceId}/state`.
- Put-food flow through face auth, optional hardware unlock, food creation, and inventory refresh.
- Retrieve-food flow through face auth, ownership check, optional hardware unlock, and inventory refresh.
- Expiration transcript/audio parsing through `POST /expiration/parse`.

## Device ID

`smart-fridge-001` is the default hardware device id from the backend contract. It is still sent in API calls that represent the fridge device or lock, but the UI shows the signed-in username/email instead of displaying the device id as the user's identity.

## API Contract

The implementation follows:

```text
INTEGRATION_GUIDE.md
../aws-backend/docs/frontend-api-contract.md
```

Frontend developers do not need AWS CLI credentials for normal local work. The app only needs the public API Gateway URL, Cognito region, Cognito client id, and default device id.

## Test Page

The old test page is still available:

```bash
cd frontend/test
python3 -m http.server 5173
```

Open:

```text
http://localhost:5173
```
