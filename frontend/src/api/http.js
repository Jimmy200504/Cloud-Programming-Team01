import { config } from "../config";

export class ApiError extends Error {
  constructor(message, payload = {}) {
    super(message);
    this.name = "ApiError";
    this.payload = payload;
  }
}

export async function apiJson(path, options = {}) {
  const response = await fetch(`${config.apiBaseUrl}${path}`, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {})
    },
    body: options.body ? JSON.stringify(options.body) : undefined
  });

  const payload = await response.json().catch(() => ({}));
  const appFailed = payload?.success === false && !options.allowAppFalse;

  if (!response.ok || appFailed) {
    throw new ApiError(payload.message || response.statusText || "Request failed", {
      status: response.status,
      ...payload
    });
  }

  return payload;
}

export function errorToObject(error) {
  return {
    success: false,
    message: error.message || "Unexpected error",
    ...(error.payload || {})
  };
}
