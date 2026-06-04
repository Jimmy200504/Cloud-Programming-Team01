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
  ownerCheckForm: document.querySelector("#ownerCheckForm"),
  signupEmail: document.querySelector("#signupEmail"),
  signupName: document.querySelector("#signupName"),
  signupPassword: document.querySelector("#signupPassword"),
  confirmCode: document.querySelector("#confirmCode"),
  loginEmail: document.querySelector("#loginEmail"),
  loginPassword: document.querySelector("#loginPassword"),
  faceImage: document.querySelector("#faceImage"),
  ownerFoodName: document.querySelector("#ownerFoodName"),
  ownerFoodImage: document.querySelector("#ownerFoodImage"),
  ownerEmail: document.querySelector("#ownerEmail"),
  ownerUserId: document.querySelector("#ownerUserId"),
  ownerExpirationDate: document.querySelector("#ownerExpirationDate"),
  ownerExpirationTranscript: document.querySelector("#ownerExpirationTranscript"),
  ownerExpirationAudio: document.querySelector("#ownerExpirationAudio"),
  ownerFaceImage: document.querySelector("#ownerFaceImage"),
  previewImage: document.querySelector("#previewImage"),
  previewFrame: document.querySelector(".preview-frame"),
  output: document.querySelector("#output"),
  clearOutput: document.querySelector("#clearOutput"),
  refreshInventory: document.querySelector("#refreshInventory"),
  inventoryList: document.querySelector("#inventoryList"),
  sessionStatus: document.querySelector("#sessionStatus"),
  accountState: document.querySelector("#accountState"),
  uploadState: document.querySelector("#uploadState"),
  ownerCheckState: document.querySelector("#ownerCheckState")
};

syncSessionUi();
if (session.email) elements.ownerEmail.value = session.email;
elements.ownerExpirationDate.value = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
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
    elements.ownerEmail.value = session.email;
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

elements.ownerCheckForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = elements.ownerFaceImage.files[0];
  const ownerEmail = elements.ownerEmail.value.trim();
  const ownerUserId = elements.ownerUserId.value.trim();

  if (!ownerEmail && !ownerUserId) {
    writeOutput({
      success: false,
      errorCode: "NO_OWNER",
      message: "Enter owner email or owner user id"
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

  setBusy(elements.ownerCheckForm, true);
  elements.ownerCheckState.textContent = "Creating";
  try {
    const foodFile = elements.ownerFoodImage.files[0];
    const userId = currentUserId();
    const putFoodBody = {
      foodName: elements.ownerFoodName.value.trim(),
      ownerEmail,
      userId,
      ownerUserId,
      expirationDate: elements.ownerExpirationDate.value,
      recordType: "owner-check-test"
    };
    if (foodFile) {
      putFoodBody.foodImageContentType = foodFile.type || "image/jpeg";
      putFoodBody.foodImageBase64 = await fileToBase64(foodFile);
    }
    const expirationAudioFile = elements.ownerExpirationAudio.files[0];
    if (expirationAudioFile) {
      putFoodBody.audioContentType = audioContentType(expirationAudioFile);
      putFoodBody.expirationAudioBase64 = await fileToBase64(expirationAudioFile);
      putFoodBody.capturedAt = new Date().toISOString();
      putFoodBody.timezone = "Asia/Taipei";
    } else if (elements.ownerExpirationTranscript.value.trim()) {
      putFoodBody.expirationTranscript = elements.ownerExpirationTranscript.value.trim();
      putFoodBody.capturedAt = new Date().toISOString();
      putFoodBody.timezone = "Asia/Taipei";
    }

    const createdFood = await postJson(`${CONFIG.apiBaseUrl}/foods/put`, putFoodBody);

    elements.ownerCheckState.textContent = "Checking";
    const faceImageBase64 = await fileToBase64(file);
    const response = await postJsonAllowFalse(`${CONFIG.apiBaseUrl}/test/owner-check`, {
      foodId: createdFood.food.foodId,
      imageContentType: file.type || "image/jpeg",
      faceImageBase64
    });
    elements.ownerCheckState.textContent = response.authorized ? "Success" : "Fail";
    writeOutput({
      createdFood: createdFood.food,
      ownerCheck: response
    });
    await loadInventory();
  } catch (error) {
    elements.ownerCheckState.textContent = "Failed";
    writeOutput(errorToObject(error));
  } finally {
    setBusy(elements.ownerCheckForm, false);
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
