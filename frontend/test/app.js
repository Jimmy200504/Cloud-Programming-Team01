const CONFIG = {
  apiBaseUrl: "https://v6ylyjtxga.execute-api.ap-northeast-1.amazonaws.com/dev",
  region: "ap-northeast-1",
  userPoolClientId: "58u2jdcqh3l2r7or7uctogai9n"
};

let session = {
  idToken: localStorage.getItem("smartFridge.idToken") || "",
  accessToken: localStorage.getItem("smartFridge.accessToken") || "",
  email: localStorage.getItem("smartFridge.email") || ""
};

const elements = {
  signupForm: document.querySelector("#signupForm"),
  confirmForm: document.querySelector("#confirmForm"),
  resendCode: document.querySelector("#resendCode"),
  loginForm: document.querySelector("#loginForm"),
  faceForm: document.querySelector("#faceForm"),
  putFlowForm: document.querySelector("#putFlowForm"),
  retrieveFlowForm: document.querySelector("#retrieveFlowForm"),
  signupEmail: document.querySelector("#signupEmail"),
  signupName: document.querySelector("#signupName"),
  signupPassword: document.querySelector("#signupPassword"),
  confirmCode: document.querySelector("#confirmCode"),
  loginEmail: document.querySelector("#loginEmail"),
  loginPassword: document.querySelector("#loginPassword"),
  faceImage: document.querySelector("#faceImage"),
  putFaceImage: document.querySelector("#putFaceImage"),
  putFoodImage: document.querySelector("#putFoodImage"),
  putFoodName: document.querySelector("#putFoodName"),
  putExpirationDate: document.querySelector("#putExpirationDate"),
  putExpirationTranscript: document.querySelector("#putExpirationTranscript"),
  putExpirationAudio: document.querySelector("#putExpirationAudio"),
  retrieveFaceImage: document.querySelector("#retrieveFaceImage"),
  retrieveFoodImage: document.querySelector("#retrieveFoodImage"),
  retrieveFoodId: document.querySelector("#retrieveFoodId"),
  retrieveFoodName: document.querySelector("#retrieveFoodName"),
  previewImage: document.querySelector("#previewImage"),
  previewFrame: document.querySelector(".preview-frame"),
  output: document.querySelector("#output"),
  clearOutput: document.querySelector("#clearOutput"),
  refreshInventory: document.querySelector("#refreshInventory"),
  inventoryList: document.querySelector("#inventoryList"),
  sessionStatus: document.querySelector("#sessionStatus"),
  accountState: document.querySelector("#accountState"),
  uploadState: document.querySelector("#uploadState"),
  putFlowState: document.querySelector("#putFlowState"),
  retrieveFlowState: document.querySelector("#retrieveFlowState")
};

syncSessionUi();
elements.putExpirationDate.value = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
  .toISOString()
  .slice(0, 10);
void loadInventory();

elements.signupForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const email = elements.signupEmail.value.trim();
  const displayName = elements.signupName.value.trim();
  const password = elements.signupPassword.value;

  setBusy(elements.signupForm, true);
  try {
    const response = await postJson(`${CONFIG.apiBaseUrl}/auth/signup`, {
      username: email,
      email,
      password,
      displayName
    });

    elements.loginEmail.value = email;
    localStorage.setItem("smartFridge.pendingEmail", email);
    elements.accountState.textContent = response.userConfirmed ? "Confirmed" : "Confirm";
    writeOutput(response);
  } catch (error) {
    writeOutput(errorToObject(error));
  } finally {
    setBusy(elements.signupForm, false);
  }
});

elements.confirmForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username =
    elements.signupEmail.value.trim() ||
    elements.loginEmail.value.trim() ||
    localStorage.getItem("smartFridge.pendingEmail");
  const code = elements.confirmCode.value.trim();

  setBusy(elements.confirmForm, true);
  try {
    const response = await cognito("ConfirmSignUp", {
      ClientId: CONFIG.userPoolClientId,
      Username: username,
      ConfirmationCode: code
    });
    elements.accountState.textContent = "Confirmed";
    writeOutput({ success: true, ...response });
  } catch (error) {
    writeOutput(errorToObject(error));
  } finally {
    setBusy(elements.confirmForm, false);
  }
});

elements.resendCode.addEventListener("click", async () => {
  const username =
    elements.signupEmail.value.trim() ||
    elements.loginEmail.value.trim() ||
    localStorage.getItem("smartFridge.pendingEmail");

  if (!username) {
    writeOutput({
      success: false,
      errorCode: "NO_USERNAME",
      message: "Enter the signup email before resending the code"
    });
    return;
  }

  elements.resendCode.disabled = true;
  try {
    const response = await cognito("ResendConfirmationCode", {
      ClientId: CONFIG.userPoolClientId,
      Username: username
    });
    writeOutput({ success: true, ...response });
  } catch (error) {
    writeOutput(errorToObject(error));
  } finally {
    elements.resendCode.disabled = false;
  }
});

elements.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = elements.loginEmail.value.trim();
  const password = elements.loginPassword.value;

  setBusy(elements.loginForm, true);
  try {
    const response = await cognito("InitiateAuth", {
      ClientId: CONFIG.userPoolClientId,
      AuthFlow: "USER_PASSWORD_AUTH",
      AuthParameters: {
        USERNAME: username,
        PASSWORD: password
      }
    });

    session = {
      idToken: response.AuthenticationResult.IdToken,
      accessToken: response.AuthenticationResult.AccessToken,
      email: username
    };
    localStorage.setItem("smartFridge.idToken", session.idToken);
    localStorage.setItem("smartFridge.accessToken", session.accessToken);
    localStorage.setItem("smartFridge.email", session.email);
    syncSessionUi();
    await loadInventory();
    writeOutput({
      success: true,
      email: username,
      tokenType: response.AuthenticationResult.TokenType,
      expiresIn: response.AuthenticationResult.ExpiresIn
    });
  } catch (error) {
    writeOutput(errorToObject(error));
  } finally {
    setBusy(elements.loginForm, false);
  }
});

elements.faceImage.addEventListener("change", () => {
  const file = elements.faceImage.files[0];
  if (!file) {
    elements.previewFrame.classList.remove("has-image");
    elements.previewImage.removeAttribute("src");
    return;
  }

  elements.previewImage.src = URL.createObjectURL(file);
  elements.previewFrame.classList.add("has-image");
});

elements.faceForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = elements.faceImage.files[0];

  if (!session.idToken) {
    writeOutput({
      success: false,
      errorCode: "NOT_SIGNED_IN",
      message: "Sign in before uploading a face image"
    });
    return;
  }

  if (!file) {
    writeOutput({
      success: false,
      errorCode: "NO_IMAGE",
      message: "Select a JPEG or PNG image"
    });
    return;
  }

  setBusy(elements.faceForm, true);
  elements.uploadState.textContent = "Uploading";
  try {
    const faceImageBase64 = await fileToBase64(file);
    const response = await postJson(
      `${CONFIG.apiBaseUrl}/users/me/face`,
      {
        imageContentType: file.type || "image/jpeg",
        faceImageBase64
      },
      {
        Authorization: `Bearer ${session.idToken}`
      }
    );
    elements.uploadState.textContent = "Stored";
    writeOutput(response);
  } catch (error) {
    elements.uploadState.textContent = "Failed";
    writeOutput(errorToObject(error));
  } finally {
    setBusy(elements.faceForm, false);
  }
});

elements.putFlowForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const faceFile = elements.putFaceImage.files[0];

  if (!faceFile) {
    writeOutput({
      success: false,
      errorCode: "NO_IMAGE",
      message: "Select a face image"
    });
    return;
  }

  setBusy(elements.putFlowForm, true);
  elements.putFlowState.textContent = "Face auth";
  try {
    const faceAuth = await authenticateFlowFace({
      action: "put",
      file: faceFile
    });
    if (!faceAuth.authenticated) {
      elements.putFlowState.textContent = "Denied";
      writeOutput({
        workflow: "put-food",
        faceAuth,
        hardwareUnlock: {
          requested: false,
          reason: "Face was not recognized"
        }
      });
      return;
    }

    elements.putFlowState.textContent = "Unlock";
    const hardwareUnlock = await signalFridgeUnlock("put");
    const foodFile = elements.putFoodImage.files[0];
    const recognizedUser = faceAuth.user || {};
    const now = new Date().toISOString();
    const putFoodBody = {
      foodName: elements.putFoodName.value.trim(),
      ownerEmail: recognizedUser.email || session.email,
      userId: recognizedUser.userId || currentUserId(),
      ownerUserId: recognizedUser.userId || currentUserId(),
      expirationDate: elements.putExpirationDate.value,
      capturedAt: now,
      putAt: now,
      deviceId: "smart-fridge-001",
      recordType: "put-flow-test"
    };
    if (foodFile) {
      putFoodBody.foodImageContentType = foodFile.type || "image/jpeg";
      putFoodBody.foodImageBase64 = await fileToBase64(foodFile);
    }
    const expirationAudioFile = elements.putExpirationAudio.files[0];
    if (expirationAudioFile) {
      putFoodBody.audioContentType = audioContentType(expirationAudioFile);
      putFoodBody.expirationAudioBase64 = await fileToBase64(expirationAudioFile);
      putFoodBody.timezone = "Asia/Taipei";
    } else if (elements.putExpirationTranscript.value.trim()) {
      putFoodBody.expirationTranscript = elements.putExpirationTranscript.value.trim();
      putFoodBody.timezone = "Asia/Taipei";
    }

    elements.putFlowState.textContent = "Storing";
    const createdFood = await postJson(`${CONFIG.apiBaseUrl}/foods/put`, putFoodBody);
    elements.putFlowState.textContent = "Stored";
    writeOutput({
      workflow: "put-food",
      faceAuth,
      hardwareUnlock,
      storedFood: createdFood.food
    });
    await loadInventory();
  } catch (error) {
    elements.putFlowState.textContent = "Failed";
    writeOutput(errorToObject(error));
  } finally {
    setBusy(elements.putFlowForm, false);
  }
});

elements.retrieveFlowForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const faceFile = elements.retrieveFaceImage.files[0];
  const foodFile = elements.retrieveFoodImage.files[0];

  if (!faceFile || !foodFile) {
    writeOutput({
      success: false,
      errorCode: "MISSING_IMAGE",
      message: "Select both a face image and a food image"
    });
    return;
  }

  setBusy(elements.retrieveFlowForm, true);
  elements.retrieveFlowState.textContent = "Face auth";
  try {
    const faceAuth = await authenticateFlowFace({
      action: "retrieve",
      file: faceFile
    });
    if (!faceAuth.authenticated) {
      elements.retrieveFlowState.textContent = "Denied";
      writeOutput({
        workflow: "retrieve-food",
        faceAuth,
        hardwareUnlock: {
          requested: false,
          reason: "Face was not recognized"
        }
      });
      return;
    }

    elements.retrieveFlowState.textContent = "Unlock";
    const hardwareUnlock = await signalFridgeUnlock("retrieve");
    const recognizedUser = faceAuth.user || {};
    const foodImageBase64 = await fileToBase64(foodFile);

    elements.retrieveFlowState.textContent = "Checking";
    const response = await postJsonAllowFalse(`${CONFIG.apiBaseUrl}/foods/retrieve`, {
      foodId: elements.retrieveFoodId.value.trim(),
      foodName: elements.retrieveFoodName.value.trim(),
      userId: recognizedUser.userId || currentUserId(),
      ownerEmail: recognizedUser.email || session.email,
      actorDisplayName: recognizedUser.displayName || recognizedUser.email || "Recognized user",
      foodImageContentType: foodFile.type || "image/jpeg",
      foodImageBase64,
      deviceId: "smart-fridge-001"
    });

    elements.retrieveFlowState.textContent = response.authorized ? "Retrieved" : "Alert";
    writeOutput({
      workflow: "retrieve-food",
      faceAuth,
      hardwareUnlock,
      retrieveResult: response,
      hardwareAlert: response.authorized
        ? {
            requested: false,
            reason: "Recognized user owns the food"
          }
        : {
            requested: true,
            actions: response.hardwareActions || ["buzzer", "owner-email"]
          }
    });
    await loadInventory();
  } catch (error) {
    elements.retrieveFlowState.textContent = "Failed";
    writeOutput(errorToObject(error));
  } finally {
    setBusy(elements.retrieveFlowForm, false);
  }
});

elements.clearOutput.addEventListener("click", () => {
  writeOutput({});
});

elements.refreshInventory.addEventListener("click", async () => {
  await loadInventory();
});

async function postJson(url, body, headers = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...headers
    },
    body: JSON.stringify(body)
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.success === false) {
    const error = new Error(payload.message || response.statusText);
    error.payload = {
      status: response.status,
      ...payload
    };
    throw error;
  }
  return payload;
}

async function postJsonAllowFalse(url, body, headers = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...headers
    },
    body: JSON.stringify(body)
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.message || response.statusText);
    error.payload = {
      status: response.status,
      ...payload
    };
    throw error;
  }
  return payload;
}

async function getJson(url, headers = {}) {
  const response = await fetch(url, {
    method: "GET",
    headers
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.success === false) {
    const error = new Error(payload.message || response.statusText);
    error.payload = {
      status: response.status,
      ...payload
    };
    throw error;
  }
  return payload;
}

async function authenticateFlowFace({ action, file }) {
  const faceImageBase64 = await fileToBase64(file);
  return postJsonAllowFalse(`${CONFIG.apiBaseUrl}/auth/face`, {
    action,
    deviceId: "smart-fridge-001",
    imageContentType: file.type || "image/jpeg",
    faceImageBase64
  });
}

async function signalFridgeUnlock(reason) {
  const hardwareSignal = {
    requested: true,
    type: "unlock-fridge-lock",
    deviceId: "smart-fridge-001",
    reason
  };

  if (!session.idToken) {
    return {
      ...hardwareSignal,
      sent: false,
      message: "No signed-in session token; hardware unlock interface is reserved but was not called"
    };
  }

  try {
    const response = await postJson(
      `${CONFIG.apiBaseUrl}/device/smart-fridge-001/lock`,
      {
        desiredLock: "unlocked"
      },
      {
        Authorization: `Bearer ${session.idToken}`
      }
    );
    return {
      ...hardwareSignal,
      sent: true,
      response
    };
  } catch (error) {
    return {
      ...hardwareSignal,
      sent: false,
      error: errorToObject(error)
    };
  }
}

async function cognito(target, body) {
  const response = await fetch(`https://cognito-idp.${CONFIG.region}.amazonaws.com/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-amz-json-1.1",
      "X-Amz-Target": `AWSCognitoIdentityProviderService.${target}`
    },
    body: JSON.stringify(body)
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.message || payload.__type || response.statusText);
    error.payload = {
      status: response.status,
      ...payload
    };
    throw error;
  }
  return payload;
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      const value = String(reader.result || "");
      resolve(value.includes(",") ? value.split(",")[1] : value);
    });
    reader.addEventListener("error", () => reject(reader.error));
    reader.readAsDataURL(file);
  });
}

function setBusy(form, busy) {
  for (const control of form.querySelectorAll("button, input")) {
    control.disabled = busy;
  }
}

function syncSessionUi() {
  if (session.idToken) {
    elements.sessionStatus.textContent = `Signed in: ${session.email}`;
    elements.sessionStatus.classList.add("signed-in");
    elements.accountState.textContent = "Signed in";
  } else {
    elements.sessionStatus.textContent = "Signed out";
    elements.sessionStatus.classList.remove("signed-in");
  }
  renderInventoryPlaceholder(session.idToken ? "Loading foods" : "Sign in to view foods");
}

function audioContentType(file) {
  if (file.type) return file.type;
  const extension = file.name.split(".").pop().toLowerCase();
  return {
    wav: "audio/wav",
    mp3: "audio/mpeg",
    mp4: "audio/mp4",
    m4a: "audio/x-m4a",
    flac: "audio/flac",
    ogg: "audio/ogg",
    amr: "audio/amr",
    webm: "audio/webm"
  }[extension] || "audio/mpeg";
}

function currentUserId() {
  const payload = parseJwt(session.idToken);
  return payload.sub || "";
}

function parseJwt(token) {
  const [, payload] = String(token || "").split(".");
  if (!payload) return {};
  try {
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return {};
  }
}

async function loadInventory() {
  if (!session.idToken) {
    renderInventoryPlaceholder("Sign in to view foods");
    return;
  }

  elements.refreshInventory.disabled = true;
  renderInventoryPlaceholder("Loading foods");
  try {
    const response = await getJson(`${CONFIG.apiBaseUrl}/foods/me`, {
      Authorization: `Bearer ${session.idToken}`
    });
    renderInventory(response.foods || []);
  } catch (error) {
    renderInventoryPlaceholder(error.message || "Unable to load foods");
    writeOutput(errorToObject(error));
  } finally {
    elements.refreshInventory.disabled = false;
  }
}

function renderInventory(foods) {
  if (foods.length === 0) {
    renderInventoryPlaceholder("No foods in fridge");
    return;
  }

  elements.inventoryList.innerHTML = "";
  for (const food of foods) {
    const item = document.createElement("article");
    item.className = "inventory-item";

    const imageWrap = document.createElement("div");
    imageWrap.className = "inventory-image";
    if (food.foodImage?.dataUrl) {
      const image = document.createElement("img");
      image.src = food.foodImage.dataUrl;
      image.alt = food.foodName || "Food image";
      imageWrap.append(image);
    } else {
      imageWrap.textContent = "No photo";
    }

    const details = document.createElement("div");
    details.className = "inventory-details";

    const name = document.createElement("h3");
    name.textContent = displayFoodName(food);

    const expiration = document.createElement("p");
    expiration.className = "inventory-date";
    expiration.textContent = `Expires ${food.expirationDate || "unknown"}`;

    const capturedAt = document.createElement("p");
    capturedAt.className = "inventory-meta";
    capturedAt.textContent = food.foodImage?.capturedAt
      ? `Captured ${formatDateTime(food.foodImage.capturedAt)}`
      : "No capture time";

    details.append(name, expiration, capturedAt);
    item.append(imageWrap, details);
    elements.inventoryList.append(item);
  }
}

function renderInventoryPlaceholder(message) {
  elements.inventoryList.innerHTML = "";
  const empty = document.createElement("div");
  empty.className = "empty-state";
  empty.textContent = message;
  elements.inventoryList.append(empty);
}

function displayFoodName(food) {
  return food.foodClassification?.displayName || food.foodName || "Unnamed food";
}

function formatDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function writeOutput(value) {
  elements.output.textContent = JSON.stringify(value, null, 2);
}

function errorToObject(error) {
  return {
    success: false,
    message: error.message,
    ...(error.payload || {})
  };
}
