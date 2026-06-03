const DEVICE_ID = process.env.DEVICE_ID || "smart-fridge-001";
const MOCK_MODE = process.env.MOCK_MODE !== "false";
const FOOD_TABLE_NAME = process.env.FOOD_TABLE_NAME;
const USER_FACE_TABLE_NAME = process.env.USER_FACE_TABLE_NAME;
const FACE_IMAGE_BUCKET_NAME = process.env.FACE_IMAGE_BUCKET_NAME;
const USER_POOL_CLIENT_ID = process.env.USER_POOL_CLIENT_ID;
const REKOGNITION_COLLECTION_ID = process.env.REKOGNITION_COLLECTION_ID || "ml-smart-fridge-faces";
const FACE_MATCH_THRESHOLD = Number(process.env.FACE_MATCH_THRESHOLD || "85");
const SES_FROM_EMAIL = process.env.SES_FROM_EMAIL;

const mockUser = {
  userId: "mock-cognito-sub-alice",
  email: "alice@example.com",
  displayName: "Alice"
};

const mockFoods = [
  {
    foodId: "food-milk-001",
    ownerUserId: mockUser.userId,
    ownerEmail: mockUser.email,
    foodName: "milk",
    expirationDate: "2026-06-10",
    deviceId: DEVICE_ID,
    createdAt: "2026-06-03T10:00:00Z",
    updatedAt: "2026-06-03T10:00:00Z"
  },
  {
    foodId: "food-yogurt-002",
    ownerUserId: mockUser.userId,
    ownerEmail: mockUser.email,
    foodName: "yogurt",
    expirationDate: "2026-06-12",
    deviceId: DEVICE_ID,
    createdAt: "2026-06-03T10:05:00Z",
    updatedAt: "2026-06-03T10:05:00Z"
  }
];

export const handler = async (event) => {
  const method = event.httpMethod;
  const path = event.path || "/";
  const body = parseJson(event.body);

  try {
    if (method === "POST" && path === "/auth/signup") {
      return json(200, await signUp(body));
    }

    if (method === "POST" && path === "/auth/face") {
      return json(200, await authenticateFace(body));
    }

    if (method === "POST" && path === "/foods/put") {
      return json(200, await putFood(body));
    }

    if (method === "POST" && path === "/foods/retrieve") {
      return json(200, await retrieveFood(body));
    }

    if (method === "POST" && path === "/test/owner-check") {
      return json(200, await testOwnerCheck(body));
    }

    if (method === "GET" && path === "/foods/me") {
      return json(200, await listMyFoods(event));
    }

    if (method === "POST" && path === "/users/me/face") {
      return json(200, await registerMyFace(event, body));
    }

    const deviceStateMatch = path.match(/^\/device\/([^/]+)\/state$/);
    if (method === "GET" && deviceStateMatch) {
      return json(200, await getDeviceState(deviceStateMatch[1]));
    }

    const lockMatch = path.match(/^\/device\/([^/]+)\/lock$/);
    if (method === "POST" && lockMatch) {
      return json(200, await updateLock(lockMatch[1], body));
    }

    return json(404, {
      success: false,
      errorCode: "NOT_FOUND",
      message: `No route for ${method} ${path}`
    });
  } catch (error) {
    console.error(error);
    const awsErrorResponse = toAwsErrorResponse(error);
    if (awsErrorResponse) {
      return json(awsErrorResponse.statusCode, awsErrorResponse.body);
    }

    return json(500, {
      success: false,
      errorCode: "INTERNAL_ERROR",
      message: "Internal server error"
    });
  }
};

async function signUp(body) {
  if (!body.username || !body.password || !body.email) {
    return {
      success: false,
      errorCode: "INVALID_SIGNUP_REQUEST",
      message: "username, email, and password are required"
    };
  }

  const { CognitoIdentityProviderClient, SignUpCommand } = await import("@aws-sdk/client-cognito-identity-provider");
  const client = new CognitoIdentityProviderClient({});
  let result;
  try {
    result = await client.send(
      new SignUpCommand({
        ClientId: USER_POOL_CLIENT_ID,
        Username: body.username,
        Password: body.password,
        UserAttributes: [
          { Name: "email", Value: body.email },
          ...(body.displayName ? [{ Name: "name", Value: body.displayName }] : [])
        ]
      })
    );
  } catch (error) {
    if (error.name === "UsernameExistsException") {
      return {
        success: false,
        errorCode: "USERNAME_EXISTS",
        message: "A user with this username already exists"
      };
    }

    if (error.name === "InvalidPasswordException") {
      return {
        success: false,
        errorCode: "INVALID_PASSWORD",
        message: error.message
      };
    }

    throw error;
  }

  return {
    success: true,
    userConfirmed: result.UserConfirmed,
    userSub: result.UserSub,
    username: body.username,
    email: body.email,
    message: result.UserConfirmed ? "User signed up" : "User signed up. Confirmation may be required."
  };
}

async function authenticateFace(body) {
  const validation = validateImage(body.faceImageBase64, body.imageContentType);
  if (validation) return validation;

  if (!["put", "retrieve"].includes(body.action)) {
    return {
      success: false,
      errorCode: "INVALID_ACTION",
      message: "action must be put or retrieve"
    };
  }

  if (MOCK_MODE && body.forceMock === true) {
    return {
      authenticated: true,
      user: mockUser,
      confidence: 96.4
    };
  }

  const mappedMatch = await searchMappedFaceByImage({
    imageBytes: decodeBase64(body.faceImageBase64)
  });
  if (!mappedMatch.match) {
    return {
      authenticated: false,
      errorCode: "FACE_NOT_RECOGNIZED",
      message: "Face not recognized"
    };
  }

  const { match, faceRecord } = mappedMatch;
  if (!faceRecord) {
    return {
      authenticated: false,
      errorCode: "USER_NOT_FOUND",
      message: "Matched face was not linked to a Cognito user",
      face: {
        rekognitionCollectionId: REKOGNITION_COLLECTION_ID,
        rekognitionFaceId: match.faceId,
        confidence: match.confidence
      }
    };
  }

  return {
    authenticated: true,
    user: {
      userId: faceRecord.userId,
      email: faceRecord.email,
      displayName: faceRecord.displayName
    },
    confidence: match.confidence,
    face: {
      rekognitionCollectionId: REKOGNITION_COLLECTION_ID,
      rekognitionFaceId: match.faceId
    }
  };
}

async function putFood(body) {
  if (body.foodImageBase64 || body.foodImageContentType) {
    const imageValidation = validateImage(body.foodImageBase64, body.foodImageContentType);
    if (imageValidation) return imageValidation;
  }

  if (body.expirationAudioBase64 || body.audioContentType) {
    const audioValidation = validateAudio(body.expirationAudioBase64, body.audioContentType);
    if (audioValidation) return audioValidation;
  }

  const now = new Date().toISOString();
  const ownerEmail = normalizeEmail(body.ownerEmail || mockUser.email);
  const food = {
    foodId: `food-${crypto.randomUUID()}`,
    ownerUserId: body.userId || body.ownerUserId || `email#${ownerEmail}`,
    ownerEmail,
    foodName: body.foodName || "milk",
    expirationDate: body.expirationDate || "2026-06-10",
    deviceId: body.deviceId || DEVICE_ID,
    createdAt: now,
    updatedAt: now,
    ...(body.recordType ? { recordType: body.recordType } : {})
  };

  if (FOOD_TABLE_NAME) {
    await putFoodItem(food);
  }

  return {
    success: true,
    food: {
      foodId: food.foodId,
      ownerUserId: food.ownerUserId,
      foodName: food.foodName,
      expirationDate: food.expirationDate,
      createdAt: food.createdAt
    }
  };
}

async function retrieveFood(body) {
  const validation = validateImage(body.foodImageBase64, body.foodImageContentType);
  if (validation) return validation;

  if (body.userId === "mock-not-owner") {
    if (!MOCK_MODE) {
      await sendOwnerAlert({
        ownerEmail: mockUser.email,
        foodName: "milk",
        actorUserId: body.userId
      });
      await updateThingShadow(DEVICE_ID, { desired: { led: "alert" } });
    }

    return {
      success: false,
      authorized: false,
      food: {
        foodId: "food-milk-001",
        foodName: "milk",
        ownerUserId: mockUser.userId,
        ownerEmail: mockUser.email
      },
      message: "This food belongs to another user"
    };
  }

  const deletedFoodId = body.foodId || "food-milk-001";
  if (!MOCK_MODE) {
    await deleteFoodItem(deletedFoodId);
  }

  return {
    success: true,
    authorized: true,
    deletedFoodId,
    message: "Food retrieved"
  };
}

async function testOwnerCheck(body) {
  const validation = validateImage(body.faceImageBase64, body.imageContentType);
  if (validation) return validation;

  if (!body.foodId && (!body.foodName || !body.expirationDate || (!body.ownerEmail && !body.ownerUserId))) {
    return {
      success: false,
      result: "fail",
      errorCode: "INVALID_OWNER_CHECK_REQUEST",
      message: "foodId or foodName, expirationDate, and ownerEmail or ownerUserId are required"
    };
  }

  const food = body.foodId
    ? await getFoodItem(body.foodId)
    : buildOwnerCheckFood(body);

  if (!food) {
    return {
      success: false,
      result: "fail",
      authorized: false,
      errorCode: "FOOD_NOT_FOUND",
      message: "Food item was not found"
    };
  }

  const mappedMatch = await searchMappedFaceByImage({
    imageBytes: decodeBase64(body.faceImageBase64)
  });
  if (!mappedMatch.match) {
    return {
      success: false,
      result: "fail",
      authorized: false,
      errorCode: "FACE_NOT_RECOGNIZED",
      message: "Face not recognized",
      requestedFood: food
    };
  }

  const { match, faceRecord } = mappedMatch;
  if (!faceRecord) {
    return {
      success: false,
      result: "fail",
      authorized: false,
      errorCode: "USER_NOT_FOUND",
      message: "Matched face was not linked to a Cognito user",
      requestedFood: food,
      face: {
        rekognitionCollectionId: REKOGNITION_COLLECTION_ID,
        rekognitionFaceId: match.faceId,
        confidence: match.confidence
      }
    };
  }

  const ownerMatches =
    (food.ownerUserId && faceRecord.userId === food.ownerUserId) ||
    (food.ownerEmail && normalizeEmail(faceRecord.email) === normalizeEmail(food.ownerEmail));

  return {
    success: ownerMatches,
    result: ownerMatches ? "success" : "fail",
    authorized: ownerMatches,
    message: ownerMatches ? "Recognized user matches the food owner" : "Recognized user does not match the food owner",
    food,
    recognizedUser: {
      userId: faceRecord.userId,
      email: faceRecord.email,
      displayName: faceRecord.displayName
    },
    face: {
      rekognitionCollectionId: REKOGNITION_COLLECTION_ID,
      rekognitionFaceId: match.faceId,
      confidence: match.confidence
    }
  };
}

function buildOwnerCheckFood(body) {
  const now = new Date().toISOString();
  const ownerEmail = normalizeEmail(body.ownerEmail);
  return {
    foodId: body.foodId || `food-${crypto.randomUUID()}`,
    ownerUserId: body.ownerUserId || `email#${ownerEmail}`,
    ownerEmail,
    foodName: body.foodName,
    expirationDate: body.expirationDate,
    deviceId: body.deviceId || DEVICE_ID,
    createdAt: now,
    updatedAt: now,
    recordType: "owner-check-test"
  };
}

async function listMyFoods(event) {
  const currentUserId =
    event.requestContext?.authorizer?.claims?.sub ||
    event.requestContext?.authorizer?.jwt?.claims?.sub ||
    mockUser.userId;

  if (!MOCK_MODE) {
    const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
    const { DynamoDBDocumentClient, QueryCommand } = await import("@aws-sdk/lib-dynamodb");
    const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));
    const result = await client.send(
      new QueryCommand({
        TableName: FOOD_TABLE_NAME,
        IndexName: "OwnerExpirationIndex",
        KeyConditionExpression: "ownerUserId = :ownerUserId",
        ExpressionAttributeValues: {
          ":ownerUserId": currentUserId
        }
      })
    );

    return {
      foods: (result.Items || []).map(({ ownerEmail, ownerUserId, updatedAt, ...food }) => food)
    };
  }

  return {
    foods: mockFoods
      .filter((food) => MOCK_MODE || food.ownerUserId === currentUserId)
      .map(({ ownerEmail, ownerUserId, updatedAt, ...food }) => food)
  };
}

async function getDeviceState(deviceId) {
  if (!MOCK_MODE) {
    const shadow = await getThingShadow(deviceId);
    const reported = shadow.state?.reported || {};
    return {
      deviceId,
      lock: reported.lock || "locked",
      led: reported.led || "off",
      temperature: reported.temperature ?? null,
      humidity: reported.humidity ?? null,
      lastSeenAt: reported.lastSeenAt || null
    };
  }

  return {
    deviceId,
    lock: "locked",
    led: "off",
    temperature: 4.2,
    humidity: 55,
    lastSeenAt: new Date().toISOString()
  };
}

async function updateLock(deviceId, body) {
  if (!["locked", "unlocked"].includes(body.desiredLock)) {
    return {
      success: false,
      errorCode: "INVALID_LOCK_STATE",
      message: "desiredLock must be locked or unlocked"
    };
  }

  if (!MOCK_MODE) {
    await updateThingShadow(deviceId, { desired: { lock: body.desiredLock } });
  }

  return {
    success: true,
    deviceId,
    desiredLock: body.desiredLock
  };
}

async function registerMyFace(event, body) {
  const validation = validateImage(body.faceImageBase64, body.imageContentType);
  if (validation) return validation;

  const currentUser = getCurrentUser(event);
  if (!currentUser.userId) {
    return {
      success: false,
      errorCode: "USER_NOT_FOUND",
      message: "Cognito user id was not found in token claims"
    };
  }

  const now = new Date().toISOString();
  const faceImageBytes = decodeBase64(body.faceImageBase64);
  const imageExtension = body.imageContentType === "image/png" ? "png" : "jpg";
  const faceImageS3Key =
    body.faceImageS3Key ||
    `user-faces/${currentUser.userId}/profile-${now.replaceAll(":", "-")}.${imageExtension}`;
  const indexedFace = await indexFace({
    userId: currentUser.userId,
    imageBytes: faceImageBytes
  });
  if (!indexedFace.faceId) {
    return indexedFace;
  }

  const faceRecord = {
    userId: currentUser.userId,
    username: currentUser.username,
    email: currentUser.email,
    displayName: currentUser.displayName,
    faceImageBucket: FACE_IMAGE_BUCKET_NAME,
    faceImageS3Key,
    rekognitionCollectionId: REKOGNITION_COLLECTION_ID,
    rekognitionFaceId: indexedFace.faceId,
    imageContentType: body.imageContentType,
    createdAt: now,
    updatedAt: now
  };

  await putFaceImageObject({
    bucketName: faceRecord.faceImageBucket,
    key: faceRecord.faceImageS3Key,
    bytes: faceImageBytes,
    contentType: faceRecord.imageContentType
  });
  await putUserFaceRecord(faceRecord);

  return {
    success: true,
    user: {
      userId: faceRecord.userId,
      username: faceRecord.username,
      email: faceRecord.email,
      displayName: faceRecord.displayName
    },
    faceImage: {
      bucket: faceRecord.faceImageBucket,
      s3Key: faceRecord.faceImageS3Key,
      contentType: faceRecord.imageContentType
    },
    face: {
      rekognitionCollectionId: faceRecord.rekognitionCollectionId,
      rekognitionFaceId: faceRecord.rekognitionFaceId,
      confidence: indexedFace.confidence
    },
    message: "Face registration accepted"
  };
}

async function indexFace({ userId, imageBytes }) {
  const { RekognitionClient, IndexFacesCommand } = await import("@aws-sdk/client-rekognition");
  const client = new RekognitionClient({});
  const result = await client.send(
    new IndexFacesCommand({
      CollectionId: REKOGNITION_COLLECTION_ID,
      ExternalImageId: userId,
      Image: {
        Bytes: imageBytes
      },
      MaxFaces: 1,
      QualityFilter: "AUTO",
      DetectionAttributes: ["DEFAULT"]
    })
  );

  const faceRecord = result.FaceRecords?.[0];
  const face = faceRecord?.Face;
  if (!face?.FaceId) {
    return {
      success: false,
      errorCode: "FACE_REGISTRATION_FAILED",
      message: "No face was detected in the uploaded image"
    };
  }

  return {
    faceId: face.FaceId,
    confidence: face.Confidence ?? 0
  };
}

async function searchFaceByImage({ imageBytes }) {
  const { RekognitionClient, SearchFacesByImageCommand } = await import("@aws-sdk/client-rekognition");
  const client = new RekognitionClient({});
  const result = await client.send(
    new SearchFacesByImageCommand({
      CollectionId: REKOGNITION_COLLECTION_ID,
      Image: {
        Bytes: imageBytes
      },
      FaceMatchThreshold: FACE_MATCH_THRESHOLD,
      MaxFaces: 5
    })
  );

  return (result.FaceMatches || [])
    .map((match) => ({
      faceId: match.Face?.FaceId,
      externalImageId: match.Face?.ExternalImageId,
      confidence: match.Similarity ?? 0
    }))
    .filter((match) => match.faceId);
}

async function searchMappedFaceByImage({ imageBytes }) {
  const matches = await searchFaceByImage({ imageBytes });
  if (matches.length === 0) {
    return {
      match: null,
      faceRecord: null
    };
  }

  for (const match of matches) {
    const faceRecord = await getUserFaceByFaceId(match.faceId);
    if (faceRecord) {
      return {
        match,
        faceRecord
      };
    }
  }

  return {
    match: matches[0],
    faceRecord: null
  };
}

async function putFaceImageObject({ bucketName, key, bytes, contentType }) {
  const { S3Client, PutObjectCommand } = await import("@aws-sdk/client-s3");
  const client = new S3Client({});
  await client.send(
    new PutObjectCommand({
      Bucket: bucketName,
      Key: key,
      Body: bytes,
      ContentType: contentType,
      ServerSideEncryption: "AES256"
    })
  );
}

function getCurrentUser(event) {
  const claims =
    event.requestContext?.authorizer?.claims ||
    event.requestContext?.authorizer?.jwt?.claims ||
    {};

  return {
    userId: claims.sub,
    username: claims["cognito:username"] || claims.email,
    email: claims.email,
    displayName: claims.name
  };
}

async function getThingShadow(deviceId) {
  const { IoTDataPlaneClient, GetThingShadowCommand } = await import("@aws-sdk/client-iot-data-plane");
  const client = new IoTDataPlaneClient({});
  const result = await client.send(new GetThingShadowCommand({ thingName: deviceId }));
  return JSON.parse(new TextDecoder().decode(result.payload));
}

async function updateThingShadow(deviceId, state) {
  const { IoTDataPlaneClient, UpdateThingShadowCommand } = await import("@aws-sdk/client-iot-data-plane");
  const client = new IoTDataPlaneClient({});
  const payload = JSON.stringify({ state });
  await client.send(
    new UpdateThingShadowCommand({
      thingName: deviceId,
      payload: new TextEncoder().encode(payload)
    })
  );
}

async function sendOwnerAlert({ ownerEmail, foodName, actorUserId }) {
  if (!SES_FROM_EMAIL) return;

  const { SESClient, SendEmailCommand } = await import("@aws-sdk/client-ses");
  const client = new SESClient({});
  await client.send(
    new SendEmailCommand({
      Source: SES_FROM_EMAIL,
      Destination: {
        ToAddresses: [ownerEmail]
      },
      Message: {
        Subject: {
          Data: "Smart Fridge food alert"
        },
        Body: {
          Text: {
            Data: `Someone attempted to retrieve your ${foodName}. Actor user id: ${actorUserId}`
          }
        }
      }
    })
  );
}

async function putFoodItem(food) {
  const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
  const { DynamoDBDocumentClient, PutCommand } = await import("@aws-sdk/lib-dynamodb");
  const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));
  await client.send(
    new PutCommand({
      TableName: FOOD_TABLE_NAME,
      Item: food
    })
  );
}

async function getFoodItem(foodId) {
  const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
  const { DynamoDBDocumentClient, GetCommand } = await import("@aws-sdk/lib-dynamodb");
  const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));
  const result = await client.send(
    new GetCommand({
      TableName: FOOD_TABLE_NAME,
      Key: { foodId }
    })
  );

  return result.Item || null;
}

async function putUserFaceRecord(faceRecord) {
  const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
  const { DynamoDBDocumentClient, PutCommand } = await import("@aws-sdk/lib-dynamodb");
  const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));
  await client.send(
    new PutCommand({
      TableName: USER_FACE_TABLE_NAME,
      Item: faceRecord
    })
  );
}

async function getUserFaceByFaceId(faceId) {
  const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
  const { DynamoDBDocumentClient, QueryCommand } = await import("@aws-sdk/lib-dynamodb");
  const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));
  const result = await client.send(
    new QueryCommand({
      TableName: USER_FACE_TABLE_NAME,
      IndexName: "FaceIdIndex",
      KeyConditionExpression: "rekognitionFaceId = :rekognitionFaceId",
      ExpressionAttributeValues: {
        ":rekognitionFaceId": faceId
      },
      Limit: 1
    })
  );

  return result.Items?.[0] || null;
}

async function deleteFoodItem(foodId) {
  const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
  const { DynamoDBDocumentClient, DeleteCommand } = await import("@aws-sdk/lib-dynamodb");
  const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));
  await client.send(
    new DeleteCommand({
      TableName: FOOD_TABLE_NAME,
      Key: { foodId }
    })
  );
}

function validateImage(base64Value, contentType) {
  if (!["image/jpeg", "image/png"].includes(contentType) || !isBase64Like(base64Value)) {
    return {
      success: false,
      errorCode: "INVALID_IMAGE",
      message: "Image must be a base64 encoded JPEG or PNG"
    };
  }

  return null;
}

function validateAudio(base64Value, contentType) {
  if (contentType !== "audio/wav" || !isBase64Like(base64Value)) {
    return {
      success: false,
      errorCode: "INVALID_AUDIO",
      message: "Audio must be a base64 encoded WAV file"
    };
  }

  return null;
}

function isBase64Like(value) {
  return typeof value === "string" && value.length > 0 && !value.startsWith("data:");
}

function decodeBase64(value) {
  return Buffer.from(value, "base64");
}

function normalizeEmail(value) {
  return String(value || "").trim().toLowerCase();
}

function parseJson(value) {
  if (!value) return {};

  try {
    return JSON.parse(value);
  } catch {
    return {};
  }
}

function json(statusCode, body) {
  return {
    statusCode,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*"
    },
    body: JSON.stringify(body)
  };
}

function toAwsErrorResponse(error) {
  const errorName = error?.name || error?.__type || error?.Code;
  if (errorName === "AccessDeniedException" || errorName === "AccessDenied") {
    return {
      statusCode: 403,
      body: {
        success: false,
        errorCode: "ML_AWS_PERMISSION_DENIED",
        message: error.message
      }
    };
  }

  if (
    errorName === "InvalidImageFormatException" ||
    errorName === "InvalidImageFormat" ||
    errorName === "InvalidParameterException"
  ) {
    return {
      statusCode: 400,
      body: {
        success: false,
        errorCode: "INVALID_IMAGE",
        message: error.message
      }
    };
  }

  return null;
}
