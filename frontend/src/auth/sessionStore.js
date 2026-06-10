const STORAGE_KEYS = {
  idToken: "smartFridge.idToken",
  accessToken: "smartFridge.accessToken",
  refreshToken: "smartFridge.refreshToken",
  email: "smartFridge.email",
  pendingEmail: "smartFridge.pendingEmail"
};

export function loadSession() {
  const idToken = localStorage.getItem(STORAGE_KEYS.idToken) || "";
  const user = parseJwt(idToken);

  return {
    idToken,
    accessToken: localStorage.getItem(STORAGE_KEYS.accessToken) || "",
    refreshToken: localStorage.getItem(STORAGE_KEYS.refreshToken) || "",
    user: {
      userId: user.sub || "",
      email: user.email || localStorage.getItem(STORAGE_KEYS.email) || "",
      displayName: user.name || user["cognito:username"] || ""
    }
  };
}

export function saveSession({ authenticationResult, email }) {
  const idToken = authenticationResult.IdToken;
  const user = parseJwt(idToken);

  localStorage.setItem(STORAGE_KEYS.idToken, idToken);
  localStorage.setItem(STORAGE_KEYS.accessToken, authenticationResult.AccessToken || "");
  localStorage.setItem(STORAGE_KEYS.refreshToken, authenticationResult.RefreshToken || "");
  localStorage.setItem(STORAGE_KEYS.email, email);

  return {
    idToken,
    accessToken: authenticationResult.AccessToken || "",
    refreshToken: authenticationResult.RefreshToken || "",
    user: {
      userId: user.sub || "",
      email: user.email || email,
      displayName: user.name || user["cognito:username"] || ""
    }
  };
}

export function clearSession() {
  for (const key of Object.values(STORAGE_KEYS)) {
    if (key !== STORAGE_KEYS.pendingEmail) {
      localStorage.removeItem(key);
    }
  }
}

export function setPendingEmail(email) {
  localStorage.setItem(STORAGE_KEYS.pendingEmail, email);
}

export function getPendingEmail() {
  return localStorage.getItem(STORAGE_KEYS.pendingEmail) || "";
}

export function parseJwt(token) {
  const [, payload] = String(token || "").split(".");
  if (!payload) return {};

  try {
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return {};
  }
}
