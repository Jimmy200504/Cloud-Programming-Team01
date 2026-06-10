export const config = {
  apiBaseUrl:
    import.meta.env.VITE_SMART_FRIDGE_API_BASE_URL ||
    "https://v6ylyjtxga.execute-api.ap-northeast-1.amazonaws.com/dev",
  cognitoRegion: import.meta.env.VITE_COGNITO_REGION || "ap-northeast-1",
  cognitoClientId:
    import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID || "58u2jdcqh3l2r7or7uctogai9n",
  defaultDeviceId: import.meta.env.VITE_DEFAULT_DEVICE_ID || "smart-fridge-001",
  timezone: "Asia/Taipei"
};
