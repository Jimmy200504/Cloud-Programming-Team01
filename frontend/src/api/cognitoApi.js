import { config } from "../config";
import { ApiError } from "./http";

export async function cognitoAction(target, body) {
  const response = await fetch(`https://cognito-idp.${config.cognitoRegion}.amazonaws.com/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-amz-json-1.1",
      "X-Amz-Target": `AWSCognitoIdentityProviderService.${target}`
    },
    body: JSON.stringify(body)
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new ApiError(payload.message || payload.__type || response.statusText, {
      status: response.status,
      ...payload
    });
  }

  return payload;
}

export function confirmSignup({ username, confirmationCode }) {
  return cognitoAction("ConfirmSignUp", {
    ClientId: config.cognitoClientId,
    Username: username,
    ConfirmationCode: confirmationCode
  });
}

export function resendConfirmationCode(username) {
  return cognitoAction("ResendConfirmationCode", {
    ClientId: config.cognitoClientId,
    Username: username
  });
}

export function loginWithPassword({ email, password }) {
  return cognitoAction("InitiateAuth", {
    ClientId: config.cognitoClientId,
    AuthFlow: "USER_PASSWORD_AUTH",
    AuthParameters: {
      USERNAME: email,
      PASSWORD: password
    }
  });
}
