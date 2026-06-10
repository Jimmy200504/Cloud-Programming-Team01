import { config } from "../config";
import { apiJson } from "./http";

export function signupUser(body) {
  return apiJson("/auth/signup", {
    method: "POST",
    body
  });
}

export function uploadCurrentUserFace(token, body) {
  return apiJson("/users/me/face", {
    method: "POST",
    token,
    body
  });
}

export function listMyFoods(token) {
  return apiJson("/foods/me", {
    token
  });
}

export function getDeviceState(token) {
  return apiJson(`/device/${config.defaultDeviceId}/state`, {
    token
  });
}

export function authenticateFace({ action, imageContentType, faceImageBase64 }) {
  return apiJson("/auth/face", {
    method: "POST",
    allowAppFalse: true,
    body: {
      action,
      deviceId: config.defaultDeviceId,
      imageContentType,
      faceImageBase64
    }
  });
}

export function putFood(body) {
  return apiJson("/foods/put", {
    method: "POST",
    body: {
      deviceId: config.defaultDeviceId,
      ...body
    }
  });
}

export function retrieveFood(body) {
  return apiJson("/foods/retrieve", {
    method: "POST",
    allowAppFalse: true,
    body: {
      deviceId: config.defaultDeviceId,
      ...body
    }
  });
}

export function parseExpiration(body) {
  return apiJson("/expiration/parse", {
    method: "POST",
    body: {
      timezone: config.timezone,
      capturedAt: new Date().toISOString(),
      ...body
    }
  });
}

export function signalLock(token, desiredLock = "unlocked") {
  return apiJson(`/device/${config.defaultDeviceId}/lock`, {
    method: "POST",
    token,
    body: {
      desiredLock
    }
  });
}
