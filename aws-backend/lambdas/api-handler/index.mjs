const DEVICE_ID = process.env.DEVICE_ID || "smart-fridge-001";
const MOCK_MODE = process.env.MOCK_MODE !== "false";
const FOOD_TABLE_NAME = process.env.FOOD_TABLE_NAME;
const USER_FACE_TABLE_NAME = process.env.USER_FACE_TABLE_NAME;
const FACE_IMAGE_BUCKET_NAME = process.env.FACE_IMAGE_BUCKET_NAME;
const FOOD_IMAGE_BUCKET_NAME = process.env.FOOD_IMAGE_BUCKET_NAME;
const USER_POOL_ID = process.env.USER_POOL_ID;
const USER_POOL_CLIENT_ID = process.env.USER_POOL_CLIENT_ID;
const REKOGNITION_COLLECTION_ID = process.env.REKOGNITION_COLLECTION_ID || "ml-smart-fridge-faces";
const FACE_MATCH_THRESHOLD = Number(process.env.FACE_MATCH_THRESHOLD || "85");
const FOOD_CLASSIFICATION_ENABLED = process.env.FOOD_CLASSIFICATION_ENABLED === "true";
const FOOD_CLASSIFICATION_MODEL_ID =
  process.env.FOOD_CLASSIFICATION_MODEL_ID || "jp.anthropic.claude-haiku-4-5-20251001-v1:0";
const FOOD_CLASSIFICATION_MIN_CONFIDENCE = Number(process.env.FOOD_CLASSIFICATION_MIN_CONFIDENCE || "0.55");
const REKOGNITION_LABEL_MIN_CONFIDENCE = Number(process.env.REKOGNITION_LABEL_MIN_CONFIDENCE || "50");
const ML_S3_BUCKET = process.env.ML_S3_BUCKET;
const ML_TIMEZONE = process.env.ML_TIMEZONE || "Asia/Taipei";
const ML_TRANSCRIBE_LANGUAGE_CODE = process.env.ML_TRANSCRIBE_LANGUAGE_CODE || "zh-TW";
const ML_TRANSCRIBE_IDENTIFY_LANGUAGE = process.env.ML_TRANSCRIBE_IDENTIFY_LANGUAGE !== "false";
const ML_TRANSCRIBE_LANGUAGE_OPTIONS = process.env.ML_TRANSCRIBE_LANGUAGE_OPTIONS || "zh-TW,en-US";
const ML_TRANSCRIBE_POLL_SECONDS = Number(process.env.ML_TRANSCRIBE_POLL_SECONDS || "2");
const ML_TRANSCRIBE_TIMEOUT_SECONDS = Number(process.env.ML_TRANSCRIBE_TIMEOUT_SECONDS || "180");
const ML_BEDROCK_DURATION_MIN_CONFIDENCE = Number(process.env.ML_BEDROCK_DURATION_MIN_CONFIDENCE || "0.7");
const SES_FROM_EMAIL = process.env.SES_FROM_EMAIL;
const CLIMATE_TEMPERATURE_MAX_C = 6;
const CLIMATE_HUMIDITY_MIN_PERCENT = 65;
const CLIMATE_HUMIDITY_MAX_PERCENT = 85;
const LEX_BOT_ID = process.env.LEX_BOT_ID;
const LEX_BOT_ALIAS_ID = process.env.LEX_BOT_ALIAS_ID;
const LEX_LOCALE_ID = process.env.LEX_LOCALE_ID || "en_US";

const FOOD_CATALOG = [
  { id: "soy_milk", displayName: "Soy milk", zhName: "豆漿", aliases: ["soy milk", "soymilk", "豆漿", "豆浆"], parent: "milk", category: "beverage" },
  { id: "milk", displayName: "Milk", zhName: "牛奶", aliases: ["milk", "牛奶"], parent: null, category: "beverage" },
  { id: "apple", displayName: "Apple", zhName: "蘋果", aliases: ["apple", "蘋果", "苹果"], parent: "fruit", category: "fruit" },
  { id: "banana", displayName: "Banana", zhName: "香蕉", aliases: ["banana", "香蕉"], parent: "fruit", category: "fruit" },
  { id: "egg", displayName: "Egg", zhName: "蛋", aliases: ["egg", "eggs", "蛋", "雞蛋", "鸡蛋"], parent: null, category: "protein" },
  { id: "bread", displayName: "Bread", zhName: "麵包", aliases: ["bread", "toast", "麵包", "面包", "吐司"], parent: null, category: "bakery" },
  { id: "cheese", displayName: "Cheese", zhName: "起司", aliases: ["cheese", "起司", "乳酪"], parent: null, category: "dairy" },
  { id: "yogurt", displayName: "Yogurt", zhName: "優格", aliases: ["yogurt", "yoghurt", "優格", "优格", "酸奶"], parent: null, category: "dairy" },
  { id: "chicken", displayName: "Chicken", zhName: "雞肉", aliases: ["chicken", "雞肉", "鸡肉"], parent: "meat", category: "meat" },
  { id: "pork", displayName: "Pork", zhName: "豬肉", aliases: ["pork", "豬肉", "猪肉"], parent: "meat", category: "meat" },
  { id: "beef", displayName: "Beef", zhName: "牛肉", aliases: ["beef", "牛肉"], parent: "meat", category: "meat" },
  { id: "fish", displayName: "Fish", zhName: "魚", aliases: ["fish", "魚", "鱼"], parent: null, category: "seafood" },
  { id: "vegetable", displayName: "Vegetable", zhName: "蔬菜", aliases: ["vegetable", "vegetables", "蔬菜"], parent: null, category: "vegetable" },
  { id: "fruit", displayName: "Fruit", zhName: "水果", aliases: ["fruit", "fruits", "水果"], parent: null, category: "fruit" },
  { id: "soft_drink", displayName: "Soft drink", zhName: "汽水", aliases: ["soft drink", "soft drinks", "cola", "coke", "coca-cola", "coca cola", "soda", "pop bottle", "汽水", "可樂", "可乐"], parent: "beverage", category: "beverage" },
  { id: "beverage", displayName: "Beverage", zhName: "飲料", aliases: ["beverage", "drink", "飲料", "饮料"], parent: null, category: "beverage" }
];

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

    if (method === "POST" && path === "/foods/detect") {
      return json(200, await detectFood(body));
    }

    if (method === "POST" && path === "/expiration/parse") {
      return json(200, await parseExpiration(body));
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

    if (method === "POST" && path === "/chat/message") {
      return json(200, await chatMessage(event, body));
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

    const climateAlertMatch = path.match(/^\/device\/([^/]+)\/climate-alert$/);
    if (method === "POST" && climateAlertMatch) {
      return json(200, await sendClimateAlert(climateAlertMatch[1], body));
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
  let foodClassification = null;
  let foodImage = null;
  let expirationParsing = null;
  if (body.foodImageBase64 || body.foodImageContentType) {
    const imageValidation = validateImage(body.foodImageBase64, body.foodImageContentType);
    if (imageValidation) return imageValidation;
    foodClassification = await classifyFoodImage({
      imageBase64: body.foodImageBase64,
      contentType: body.foodImageContentType,
      fallbackFoodName: body.foodName
    });
    if (foodClassification.success === false) return foodClassification;
  }

  if (body.expirationAudioBase64 || body.audioContentType) {
    const audioValidation = validateAudio(body.expirationAudioBase64, body.audioContentType);
    if (audioValidation) return audioValidation;
  }

  if (hasExpirationInput(body)) {
    expirationParsing = await parseExpiration(body);
    if (expirationParsing.success === false) return expirationParsing;
  }

  const now = new Date().toISOString();
  const ownerEmail = normalizeEmail(body.ownerEmail || mockUser.email);
  const foodId = `food-${crypto.randomUUID()}`;
  if (body.foodImageBase64 && FOOD_IMAGE_BUCKET_NAME) {
    const imageExtension = body.foodImageContentType === "image/png" ? "png" : "jpg";
    const foodImageS3Key =
      body.foodImageS3Key ||
      `food-images/${body.userId || body.ownerUserId || `email-${ownerEmail}`}/${foodId}-${now.replaceAll(":", "-")}.${imageExtension}`;
    foodImage = {
      bucket: FOOD_IMAGE_BUCKET_NAME,
      s3Key: foodImageS3Key,
      contentType: body.foodImageContentType,
      capturedAt: body.foodImageCapturedAt || body.capturedAt || now
    };
    await putFoodImageObject({
      bucketName: foodImage.bucket,
      key: foodImage.s3Key,
      bytes: decodeBase64(body.foodImageBase64),
      contentType: foodImage.contentType
    });
  }

  const food = {
    foodId,
    ownerUserId: body.userId || body.ownerUserId || `email#${ownerEmail}`,
    ownerEmail,
    foodName: catalogFoodId(body.foodName) || foodClassification?.foodName || "milk",
    expirationDate: expirationParsing?.expiration?.expirationDate || body.expirationDate || "2026-06-10",
    deviceId: body.deviceId || DEVICE_ID,
    createdAt: now,
    putAt: body.putAt || now,
    updatedAt: now,
    ...(foodImage ? { foodImage } : {}),
    ...(foodClassification ? { foodClassification } : {}),
    ...(expirationParsing ? { expirationParsing: expirationParsing.expiration } : {}),
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
      createdAt: food.createdAt,
      putAt: food.putAt,
      ...(foodImage ? { foodImage } : {}),
      ...(foodClassification ? { foodClassification } : {}),
      ...(expirationParsing ? { expirationParsing: expirationParsing.expiration } : {})
    }
  };
}

async function detectFood(body) {
  const validation = validateImage(body.foodImageBase64, body.foodImageContentType);
  if (validation) return validation;

  const foodClassification = await classifyFoodImage({
    imageBase64: body.foodImageBase64,
    contentType: body.foodImageContentType,
    fallbackFoodName: body.foodName
  });
  if (foodClassification.success === false) return foodClassification;

  return {
    success: true,
    food: {
      foodName: foodClassification.foodName,
      displayName: foodClassification.displayName
    },
    foodClassification
  };
}

async function parseExpiration(body) {
  const timezone = body.timezone || ML_TIMEZONE;
  const capturedAt = body.capturedAt || body.captured_at || new Date().toISOString();
  const transcript = await transcriptFromExpirationInput(body);
  if (transcript.success === false) return transcript;

  const duration = await normalizeDurationWithBedrock(transcript.transcript);
  if (duration.success === false) return duration;

  const expirationDate = expirationDateFromDuration(duration.expirationDuration, {
    capturedAt,
    timezone
  });

  return {
    success: true,
    expiration: {
      expirationDate,
      expirationDuration: duration.expirationDuration,
      expirationDurationUnit: duration.expirationDurationUnit,
      expirationDurationAmount: duration.expirationDurationAmount,
      transcript: transcript.transcript,
      confidence: duration.confidence,
      reason: duration.reason,
      timezone
    }
  };
}

async function retrieveFood(body) {
  const validation = validateImage(body.foodImageBase64, body.foodImageContentType);
  if (validation) return validation;

  const actorUserId = body.actorUserId || body.userId || body.ownerUserId;
  const actorEmail = normalizeEmail(body.actorEmail || body.ownerEmail);
  if (!actorUserId && !actorEmail) {
    return {
      success: false,
      authorized: false,
      errorCode: "USER_NOT_FOUND",
      message: "A recognized actor userId or actorEmail is required to retrieve food"
    };
  }

  const foodClassification = await classifyFoodImage({
    imageBase64: body.foodImageBase64,
    contentType: body.foodImageContentType,
    fallbackFoodName: body.foodName
  });
  if (foodClassification.success === false) return foodClassification;
  let requestedFood = body.foodId
    ? await getFoodItem(body.foodId)
    : await findFoodByName({
        foodName: foodClassification.foodName,
        ownerUserId: body.userId || body.ownerUserId
      });
  if (!requestedFood && !body.foodId) {
    requestedFood = await findFoodByName({
      foodName: foodClassification.foodName
    });
  }

  if (body.userId === "mock-not-owner") {
    const food = requestedFood || {
      foodId: "food-milk-001",
      foodName: foodClassification.foodName,
      ownerUserId: mockUser.userId,
      ownerEmail: mockUser.email
    };
    if (!MOCK_MODE) {
      await sendOwnerAlert({
        ownerEmail: food.ownerEmail,
        foodName: food.foodName,
        actorUserId
      });
      await updateThingShadow(DEVICE_ID, { desired: { led: "alert" } });
    }

    return {
      success: false,
      authorized: false,
      food,
      foodClassification,
      hardwareActions: ownerViolationActions(food),
      message: "This food belongs to another user"
    };
  }

  if (!requestedFood && FOOD_TABLE_NAME) {
    return {
      success: false,
      authorized: false,
      errorCode: "FOOD_NOT_FOUND",
      message: "No stored food matched the classified food image",
      foodClassification
    };
  }

  const ownerMatches =
    requestedFood &&
    ((actorUserId && requestedFood.ownerUserId === actorUserId) ||
      (actorEmail && normalizeEmail(requestedFood.ownerEmail) === actorEmail));

  if (!ownerMatches) {
    if (!MOCK_MODE) {
      await sendOwnerAlert({
        ownerEmail: requestedFood.ownerEmail,
        foodName: requestedFood.foodName,
        actorUserId: actorUserId || actorEmail
      });
      await updateThingShadow(DEVICE_ID, { desired: { led: "alert" } });
    }

    return {
      success: false,
      authorized: false,
      food: requestedFood,
      foodClassification,
      hardwareActions: ownerViolationActions(requestedFood),
      message: "This food belongs to another user"
    };
  }

  const deletedFoodId = requestedFood?.foodId || body.foodId || "food-milk-001";
  if (FOOD_TABLE_NAME) {
    await deleteFoodItem(deletedFoodId);
  }

  const actorName = body.actorDisplayName || body.actorName || actorEmail || actorUserId || "Recognized user";
  const retrievedFoodName = requestedFood?.foodName || foodClassification.displayName || foodClassification.foodName;
  return {
    success: true,
    authorized: true,
    deletedFoodId,
    food: requestedFood
      ? {
          foodId: requestedFood.foodId,
          foodName: requestedFood.foodName,
          ownerUserId: requestedFood.ownerUserId,
          ownerEmail: requestedFood.ownerEmail,
          expirationDate: requestedFood.expirationDate
        }
      : null,
    foodClassification,
    notification: {
      type: "food-retrieved",
      message: `${actorName} took ${retrievedFoodName}`
    },
    message: `${actorName} took ${retrievedFoodName}`
  };
}

function ownerViolationActions(food) {
  return [
    {
      type: "hardware-buzzer",
      status: MOCK_MODE ? "reserved" : "requested",
      message: "Ask external hardware to play an alert sound"
    },
    {
      type: "owner-email",
      status: SES_FROM_EMAIL && !MOCK_MODE ? "requested" : "reserved",
      ownerEmail: food?.ownerEmail,
      message: "Notify the food owner by email"
    }
  ];
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

  if (FOOD_TABLE_NAME) {
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
      foods: await publicFoodItems(result.Items || [])
    };
  }

  return {
    foods: await publicFoodItems(mockFoods.filter((food) => MOCK_MODE || food.ownerUserId === currentUserId))
  };
}

async function chatMessage(event, body) {
  const message = String(body.message || body.text || "").trim();
  if (!message) {
    return {
      success: false,
      errorCode: "INVALID_CHAT_MESSAGE",
      message: "message is required"
    };
  }

  const currentUser = getCurrentUser(event);
  const currentUserId = currentUser.userId || mockUser.userId;
  const foods = await getInventoryForUser(currentUserId);
  const lex = await recognizeInventoryIntent({
    text: message,
    sessionId: body.sessionId || currentUserId || `chat-${DEVICE_ID}`
  });
  const answer = answerInventoryChat({
    question: message,
    foods,
    lex
  });

  return {
    success: true,
    message: answer,
    source: lex.used ? "lex" : "local",
    lex,
    inventoryCount: foods.length
  };
}

async function getInventoryForUser(ownerUserId) {
  if (FOOD_TABLE_NAME) {
    const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
    const { DynamoDBDocumentClient, QueryCommand } = await import("@aws-sdk/lib-dynamodb");
    const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));
    const result = await client.send(
      new QueryCommand({
        TableName: FOOD_TABLE_NAME,
        IndexName: "OwnerExpirationIndex",
        KeyConditionExpression: "ownerUserId = :ownerUserId",
        ExpressionAttributeValues: {
          ":ownerUserId": ownerUserId
        }
      })
    );
    return publicFoodItems(result.Items || []);
  }

  return publicFoodItems(mockFoods.filter((food) => MOCK_MODE || food.ownerUserId === ownerUserId));
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

async function sendClimateAlert(deviceId, body) {
  const temperature = numberOrNull(body.temperature);
  const humidity = numberOrNull(body.humidity);
  const capturedAt = body.capturedAt || body.lastSeenAt || new Date().toISOString();
  const alerts = climateAlertsFor({ temperature, humidity });

  if (temperature === null && humidity === null) {
    return {
      success: false,
      errorCode: "INVALID_CLIMATE_READING",
      message: "temperature or humidity is required"
    };
  }

  if (alerts.length === 0) {
    return {
      success: true,
      alertSent: false,
      deviceId,
      temperature,
      humidity,
      capturedAt,
      message: "Climate is within the configured safe range"
    };
  }

  const recipients = await getAllKnownUserEmails();
  if (recipients.length === 0) {
    return {
      success: false,
      alertSent: false,
      errorCode: "NO_ALERT_RECIPIENTS",
      deviceId,
      temperature,
      humidity,
      capturedAt,
      alerts,
      message: "No user email addresses were found"
    };
  }

  const subject = "Smart Fridge climate alert";
  const bodyText = [
    "Smart Fridge detected an unsafe climate reading.",
    "",
    `Device: ${deviceId}`,
    `Temperature: ${temperature === null ? "unknown" : `${temperature} C`}`,
    `Humidity: ${humidity === null ? "unknown" : `${humidity}%`}`,
    `Time: ${capturedAt}`,
    "",
    "Alerts:",
    ...alerts.map((alert) => `- ${alert.message}`)
  ].join("\n");

  const results = await sendEmailToRecipients({
    recipients,
    subject,
    bodyText
  });

  let shadowAlertUpdated = false;
  if (!MOCK_MODE) {
    try {
      await updateThingShadow(deviceId, { desired: { led: "alert" } });
      shadowAlertUpdated = true;
    } catch (error) {
      console.error("Unable to update climate alert LED shadow state", error);
    }
  }

  return {
    success: results.failed.length === 0,
    alertSent: results.sent.length > 0,
    deviceId,
    temperature,
    humidity,
    capturedAt,
    thresholds: {
      temperatureMaxC: CLIMATE_TEMPERATURE_MAX_C,
      humidityMinPercent: CLIMATE_HUMIDITY_MIN_PERCENT,
      humidityMaxPercent: CLIMATE_HUMIDITY_MAX_PERCENT
    },
    alerts,
    recipients: {
      total: recipients.length,
      sent: results.sent,
      failed: results.failed
    },
    shadowAlertUpdated
  };
}

async function recognizeInventoryIntent({ text, sessionId }) {
  if (!LEX_BOT_ID || !LEX_BOT_ALIAS_ID) {
    return {
      used: false,
      reason: "LEX_NOT_CONFIGURED"
    };
  }

  try {
    const { LexRuntimeV2Client, RecognizeTextCommand } = await import("@aws-sdk/client-lex-runtime-v2");
    const client = new LexRuntimeV2Client({});
    const result = await client.send(
      new RecognizeTextCommand({
        botId: LEX_BOT_ID,
        botAliasId: LEX_BOT_ALIAS_ID,
        localeId: LEX_LOCALE_ID,
        sessionId: String(sessionId).slice(0, 100),
        text
      })
    );
    const topInterpretation = result.interpretations?.[0] || {};
    return {
      used: true,
      botId: LEX_BOT_ID,
      botAliasId: LEX_BOT_ALIAS_ID,
      localeId: LEX_LOCALE_ID,
      intentName: topInterpretation.intent?.name || result.sessionState?.intent?.name || null,
      confidence: topInterpretation.nluConfidence?.score ?? null,
      slots: lexSlotsToValues(topInterpretation.intent?.slots || result.sessionState?.intent?.slots || {}),
      messages: (result.messages || []).map((message) => message.content).filter(Boolean)
    };
  } catch (error) {
    console.error("Lex RecognizeText failed; falling back to local inventory chat", error);
    return {
      used: false,
      reason: error.name || "LEX_RECOGNIZE_TEXT_FAILED",
      message: error.message
    };
  }
}

function answerInventoryChat({ question, foods, lex }) {
  if (foods.length === 0) return "目前庫存是空的。";

  const summary = summarizeInventoryForChat(foods);
  const normalized = normalizeChatText(question);
  const lexIntent = normalizeChatText(lex.intentName);
  const slotFoodName = normalizeChatText(lex.slots?.FoodName || lex.slots?.foodName);
  const mentionedFoods = findChatMentionedFoods(slotFoodName || normalized, foods);

  if (["nearest expiration intent", "nearestexpirationintent", "next expiring food intent"].includes(lexIntent) || asksNearestExpirationText(normalized)) {
    return formatNearestChatExpiration(summary);
  }

  if (["expiring soon intent", "expiringsoonintent"].includes(lexIntent) || asksExpiringSoonText(normalized)) {
    return formatChatFoodList(summary.expiringSoon, "接下來 2 天內快過期的食物", "目前沒有 2 天內快過期的食物。");
  }

  if (["expired food intent", "expiredfoodintent"].includes(lexIntent) || asksExpiredText(normalized)) {
    return formatChatFoodList(summary.expired, "已過期的食物", "目前沒有已過期的食物。");
  }

  if (["count inventory intent", "countinventoryintent"].includes(lexIntent) || asksCountText(normalized)) {
    return `目前冰箱裡共有 ${foods.length} 項食物。${summary.countsText ? ` ${summary.countsText}` : ""}`;
  }

  if (["food lookup intent", "foodlookupintent"].includes(lexIntent) || mentionedFoods.length > 0) {
    return formatMatchedChatFoods(mentionedFoods);
  }

  if (["check inventory intent", "checkinventoryintent"].includes(lexIntent) || asksAllInventoryText(normalized)) {
    return formatChatFoodList(summary.sortedFoods, "目前冰箱內容物", "目前庫存是空的。");
  }

  return `目前有 ${foods.length} 項食物。${formatChatFoodList(summary.sortedFoods.slice(0, 5), "庫存摘要", "")}`;
}

function lexSlotsToValues(slots) {
  return Object.fromEntries(
    Object.entries(slots || {}).map(([name, slot]) => [
      name,
      slot?.value?.interpretedValue || slot?.value?.originalValue || null
    ])
  );
}

function summarizeInventoryForChat(foods) {
  const sortedFoods = [...foods].sort((a, b) => {
    const left = daysUntilDate(a.expirationDate);
    const right = daysUntilDate(b.expirationDate);
    if (left === null && right === null) return 0;
    if (left === null) return 1;
    if (right === null) return -1;
    return left - right;
  });
  const upcomingFoods = sortedFoods.filter((food) => {
    const days = daysUntilDate(food.expirationDate);
    return days !== null && days >= 0;
  });
  const expiringSoon = sortedFoods.filter((food) => {
    const days = daysUntilDate(food.expirationDate);
    return days !== null && days >= 0 && days <= 2;
  });
  const expired = sortedFoods.filter((food) => {
    const days = daysUntilDate(food.expirationDate);
    return days !== null && days < 0;
  });
  const counts = new Map();
  for (const food of foods) {
    const name = chatFoodDisplayName(food);
    counts.set(name, (counts.get(name) || 0) + 1);
  }
  const countsText = [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 4)
    .map(([name, count]) => `${name} ${count} 項`)
    .join("、");

  return { sortedFoods, upcomingFoods, expiringSoon, expired, countsText };
}

function findChatMentionedFoods(query, foods) {
  const normalizedQuery = normalizeChatText(query);
  if (!normalizedQuery) return [];

  const matchedIds = new Set();
  for (const entry of FOOD_CATALOG) {
    const terms = [entry.id, entry.displayName, entry.zhName, ...(entry.aliases || [])];
    if (terms.some((term) => normalizedQuery.includes(normalizeChatText(term)))) {
      matchedIds.add(normalizeChatText(entry.id));
    }
  }

  return foods.filter((food) => {
    const names = [
      food.foodName,
      food.foodClassification?.foodName,
      food.foodClassification?.displayName,
      chatFoodDisplayName(food)
    ].map(normalizeChatText);

    return names.some((name) => matchedIds.has(name) || normalizedQuery.includes(name));
  });
}

function formatMatchedChatFoods(foods) {
  if (foods.length === 0) return "目前沒有找到你問的食物。";
  const foodName = chatFoodDisplayName(foods[0]);
  return `有，找到 ${foods.length} 項 ${foodName}。${foods.map(formatChatFoodLine).join("；")}`;
}

function formatChatFoodList(foods, title, emptyText) {
  if (foods.length === 0) return emptyText;
  return `${title}：${foods.map(formatChatFoodLine).join("；")}`;
}

function formatNearestChatExpiration(summary) {
  const food = summary.upcomingFoods[0];
  if (food) {
    const expiredNote = summary.expired.length
      ? ` 另外 ${summary.expired.map((item) => chatFoodDisplayName(item)).join("、")} 已經過期。`
      : "";
    return `最先快過期的是 ${formatChatFoodLine(food)}。${expiredNote}`;
  }

  if (summary.expired.length > 0) {
    return `目前沒有未來才到期的食物，但有已過期項目：${summary.expired.map(formatChatFoodLine).join("；")}`;
  }

  return "目前沒有可判斷到期日的食物。";
}

function formatChatFoodLine(food) {
  const days = daysUntilDate(food.expirationDate);
  const daysText = days === null ? "剩餘天數未知" : days < 0 ? `已過期 ${Math.abs(days)} 天` : `剩 ${days} 天`;
  return `${chatFoodDisplayName(food)}，${formatDateOnly(food.expirationDate)} 到期，${daysText}`;
}

function chatFoodDisplayName(food) {
  return food.foodName || food.foodClassification?.displayName || food.foodClassification?.foodName || "Unknown";
}

function daysUntilDate(dateValue) {
  if (!dateValue) return null;
  const target = new Date(`${dateValue}T00:00:00`);
  if (Number.isNaN(target.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - today.getTime()) / 86400000);
}

function formatDateOnly(value) {
  return value ? String(value).slice(0, 10) : "unknown";
}

function asksNearestExpirationText(value) {
  const asksOrder = ["第一個", "哪個先", "最先", "最快", "最早", "最近", "next", "first", "earliest"].some((term) =>
    value.includes(term)
  );
  const asksExpiration = ["快過期", "過期", "到期", "expire", "expiration"].some((term) => value.includes(term));
  return asksOrder && asksExpiration;
}

function asksExpiringSoonText(value) {
  return ["快過期", "即將過期", "soon", "expire soon", "expiring"].some((term) => value.includes(term));
}

function asksExpiredText(value) {
  return ["已過期", "過期了", "expired", "late"].some((term) => value.includes(term));
}

function asksCountText(value) {
  return ["幾個", "幾項", "多少", "count", "how many"].some((term) => value.includes(term));
}

function asksAllInventoryText(value) {
  return ["有什麼", "內容物", "庫存", "清單", "inventory", "list", "what"].some((term) => value.includes(term));
}

function normalizeChatText(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[_-]+/g, " ");
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

async function classifyFoodImage({ imageBase64, contentType, fallbackFoodName }) {
  if (!FOOD_CLASSIFICATION_ENABLED) {
    return mockFoodClassification(fallbackFoodName);
  }

  const imageBytes = decodeBase64(imageBase64);
  const rekognitionCandidates = await detectFoodLabels({ imageBytes });
  const bedrockClassification = await classifyFoodWithBedrock({
    imageBytes,
    contentType,
    rekognitionCandidates
  });

  return {
    ...bedrockClassification,
    model: FOOD_CLASSIFICATION_MODEL_ID,
    rekognitionCandidates
  };
}

async function detectFoodLabels({ imageBytes }) {
  const { RekognitionClient, DetectLabelsCommand } = await import("@aws-sdk/client-rekognition");
  const client = new RekognitionClient({});
  const result = await client.send(
    new DetectLabelsCommand({
      Image: {
        Bytes: imageBytes
      },
      MaxLabels: 10,
      MinConfidence: REKOGNITION_LABEL_MIN_CONFIDENCE
    })
  );

  return (result.Labels || []).map((label) => ({
    label: normalizeFoodLabel(label.Name),
    confidence: label.Confidence ?? 0
  }));
}

async function classifyFoodWithBedrock({ imageBytes, contentType, rekognitionCandidates }) {
  const { BedrockRuntimeClient, ConverseCommand } = await import("@aws-sdk/client-bedrock-runtime");
  const client = new BedrockRuntimeClient({});
  const result = await client.send(
    new ConverseCommand({
      modelId: FOOD_CLASSIFICATION_MODEL_ID,
      system: [
        {
          text:
            "You classify the main food item being stored in a smart refrigerator. " +
            "Use the image as primary evidence. Use Rekognition labels as supporting evidence. " +
            "Ignore people, hands, background, fridge parts, table, and generic container-only labels " +
            "unless they help identify the food. Choose exactly one item from the food catalog. " +
            "If no catalog item is plausible, return food_id null and confidence 0. " +
            "Return one JSON object only. No markdown. No extra text."
        }
      ],
      messages: [
        {
          role: "user",
          content: [
            {
              image: {
                format: imageFormatFromContentType(contentType),
                source: {
                  bytes: imageBytes
                }
              }
            },
            {
              text:
                `Food catalog JSON:\n${JSON.stringify(FOOD_CATALOG)}\n\n` +
                `Rekognition labels JSON:\n${JSON.stringify(rekognitionCandidates)}\n\n` +
                "Return JSON with this schema:\n" +
                "{\"food_id\": string|null, \"display_name\": string|null, \"confidence\": number, \"reason\": string}"
            }
          ]
        }
      ],
      inferenceConfig: {
        maxTokens: 768,
        temperature: 0
      }
    })
  );

  const data = parseBedrockJson(result);
  const foodId = data.food_id;
  const confidence = normalizeClassificationConfidence(data.confidence);
  const catalogItem = FOOD_CATALOG.find((item) => item.id === foodId);
  if (!catalogItem) {
    return {
      success: false,
      errorCode: "ML_NO_FOOD_DETECTED",
      message: "Bedrock did not classify the image into a catalog food item",
      bedrock: data
    };
  }

  if (confidence === null || confidence < FOOD_CLASSIFICATION_MIN_CONFIDENCE) {
    return {
      success: false,
      errorCode: "ML_LOW_CONFIDENCE",
      message: "Bedrock food classification confidence is below threshold",
      threshold: FOOD_CLASSIFICATION_MIN_CONFIDENCE,
      bedrock: data
    };
  }

  return {
    foodId,
    foodName: foodId,
    displayName: data.display_name || catalogItem.displayName || foodId,
    confidence,
    matchedCatalogId: foodId,
    reason: String(data.reason || "")
  };
}

function parseBedrockJson(result) {
  const text = (result.output?.message?.content || [])
    .map((block) => block.text || "")
    .filter(Boolean)
    .join("\n")
    .trim();
  if (!text) {
    throw Object.assign(new Error("Bedrock returned an empty food classification response"), {
      name: "BedrockEmptyResponse"
    });
  }

  try {
    return JSON.parse(text);
  } catch {
    const match = text.match(/\{[\s\S]*\}/);
    if (!match) {
      throw Object.assign(new Error("Bedrock response did not contain JSON"), {
        name: "BedrockInvalidJson",
        responseText: text
      });
    }
    return JSON.parse(match[0]);
  }
}

function normalizeClassificationConfidence(value) {
  const confidence = Number(value);
  if (!Number.isFinite(confidence)) return null;
  if (confidence >= 0 && confidence <= 1) return confidence;
  if (confidence > 1 && confidence <= 100) return confidence / 100;
  return null;
}

function mockFoodClassification(foodName = "milk") {
  const catalogId = catalogFoodId(foodName) || "milk";
  const catalogItem = FOOD_CATALOG.find((item) => item.id === catalogId) || FOOD_CATALOG.find((item) => item.id === "milk");
  return {
    foodId: catalogItem.id,
    foodName: catalogItem.id,
    displayName: catalogItem.displayName,
    confidence: 1,
    matchedCatalogId: catalogItem.id,
    model: "mock",
    reason: "Food classification is disabled",
    rekognitionCandidates: []
  };
}

function normalizeFoodLabel(label) {
  return String(label || "").trim().toLowerCase();
}

function catalogFoodId(value) {
  const normalized = normalizeFoodLabel(value);
  if (!normalized) return "";
  const catalogItem = FOOD_CATALOG.find(
    (item) =>
      item.id === normalized ||
      normalizeFoodLabel(item.displayName) === normalized ||
      normalizeFoodLabel(item.zhName) === normalized ||
      item.aliases.some((alias) => normalizeFoodLabel(alias) === normalized)
  );
  return catalogItem?.id || normalized;
}

function equivalentFoodNames(foodName) {
  const catalogId = catalogFoodId(foodName);
  const names = new Set([normalizeFoodLabel(foodName), catalogId]);
  const catalogItem = FOOD_CATALOG.find((item) => item.id === catalogId);
  if (catalogItem) {
    names.add(catalogItem.id);
    names.add(normalizeFoodLabel(catalogItem.displayName));
    names.add(normalizeFoodLabel(catalogItem.zhName));
    if (catalogItem.parent) names.add(catalogItem.parent);
    for (const alias of catalogItem.aliases) {
      names.add(normalizeFoodLabel(alias));
      names.add(catalogFoodId(alias));
    }
    for (const childItem of FOOD_CATALOG.filter((item) => item.parent === catalogItem.id)) {
      names.add(childItem.id);
      names.add(normalizeFoodLabel(childItem.displayName));
      names.add(normalizeFoodLabel(childItem.zhName));
      for (const alias of childItem.aliases) {
        names.add(normalizeFoodLabel(alias));
        names.add(catalogFoodId(alias));
      }
    }
  }
  return [...names].filter(Boolean);
}

function imageFormatFromContentType(contentType) {
  if (contentType === "image/png") return "png";
  return "jpeg";
}

function hasExpirationInput(body) {
  return Boolean(
    body.expirationTranscript ||
      body.expirationTranscriptText ||
      body.transcriptText ||
      body.expirationAudioBase64 ||
      body.expirationAudioS3Uri
  );
}

async function transcriptFromExpirationInput(body) {
  const transcript = body.expirationTranscript || body.expirationTranscriptText || body.transcriptText;
  if (typeof transcript === "string" && transcript.trim()) {
    return {
      success: true,
      transcript: transcript.trim()
    };
  }

  if (body.expirationAudioS3Uri) {
    if (!ML_S3_BUCKET) {
      return {
        success: false,
        errorCode: "ML_INVALID_INPUT",
        message: "ML_S3_BUCKET is required for audio transcription"
      };
    }
    return transcribeAudio({ mediaUri: body.expirationAudioS3Uri });
  }

  if (!body.expirationAudioBase64) {
    return {
      success: false,
      errorCode: "ML_INVALID_INPUT",
      message: "expirationTranscript, expirationAudioS3Uri, or expirationAudioBase64 is required"
    };
  }

  if (!ML_S3_BUCKET) {
    return {
      success: false,
      errorCode: "ML_INVALID_INPUT",
      message: "ML_S3_BUCKET is required for audio transcription"
    };
  }

  const contentType = body.audioContentType || "audio/wav";
  const extension = audioExtensionFromContentType(contentType);
  if (!extension || !isBase64Like(body.expirationAudioBase64)) {
    return {
      success: false,
      errorCode: "ML_UNSUPPORTED_MEDIA_TYPE",
      message: "Audio must be WAV, MP3, MP4, M4A, FLAC, OGG, AMR, or WEBM"
    };
  }

  const key = `audio/${crypto.randomUUID()}.${extension}`;
  await putMediaObject({
    bucketName: ML_S3_BUCKET,
    key,
    bytes: decodeBase64(body.expirationAudioBase64),
    contentType
  });

  return transcribeAudio({
    mediaUri: `s3://${ML_S3_BUCKET}/${key}`
  });
}

async function transcribeAudio({ mediaUri }) {
  const { TranscribeClient, StartTranscriptionJobCommand, GetTranscriptionJobCommand } =
    await import("@aws-sdk/client-transcribe");
  const client = new TranscribeClient({});
  const jobName = `ml-expiration-${crypto.randomUUID()}`;
  const outputKey = `transcribe/${jobName}.json`;

  await client.send(
    new StartTranscriptionJobCommand({
      TranscriptionJobName: jobName,
      Media: {
        MediaFileUri: mediaUri
      },
      OutputBucketName: ML_S3_BUCKET,
      OutputKey: outputKey,
      ...transcriptionLanguageConfig(),
      ...(audioFormatFromUri(mediaUri) ? { MediaFormat: audioFormatFromUri(mediaUri) } : {})
    })
  );

  const deadline = Date.now() + ML_TRANSCRIBE_TIMEOUT_SECONDS * 1000;
  while (Date.now() < deadline) {
    const result = await client.send(
      new GetTranscriptionJobCommand({
        TranscriptionJobName: jobName
      })
    );
    const job = result.TranscriptionJob;
    const status = job?.TranscriptionJobStatus;
    if (status === "COMPLETED") {
      return readTranscriptOutput({ bucketName: ML_S3_BUCKET, key: outputKey });
    }
    if (status === "FAILED") {
      return {
        success: false,
        errorCode: "ML_TRANSCRIBE_FAILED",
        message: "Transcribe job failed",
        details: {
          jobName,
          reason: job?.FailureReason
        }
      };
    }
    await sleep(ML_TRANSCRIBE_POLL_SECONDS * 1000);
  }

  return {
    success: false,
    errorCode: "ML_TRANSCRIBE_FAILED",
    message: "Transcribe job timed out",
    details: {
      jobName,
      timeoutSeconds: ML_TRANSCRIBE_TIMEOUT_SECONDS
    }
  };
}

function transcriptionLanguageConfig() {
  if (ML_TRANSCRIBE_IDENTIFY_LANGUAGE) {
    const options = ML_TRANSCRIBE_LANGUAGE_OPTIONS.split(",")
      .map((option) => option.trim())
      .filter(Boolean);
    return {
      IdentifyLanguage: true,
      ...(options.length ? { LanguageOptions: options } : {})
    };
  }

  return {
    LanguageCode: ML_TRANSCRIBE_LANGUAGE_CODE
  };
}

async function readTranscriptOutput({ bucketName, key }) {
  const { S3Client, GetObjectCommand } = await import("@aws-sdk/client-s3");
  const client = new S3Client({});
  const result = await client.send(
    new GetObjectCommand({
      Bucket: bucketName,
      Key: key
    })
  );
  const payload = JSON.parse(await result.Body.transformToString());
  const transcript = payload.results?.transcripts?.[0]?.transcript;
  if (!transcript) {
    return {
      success: false,
      errorCode: "ML_TRANSCRIBE_FAILED",
      message: "Transcribe output did not include transcript text",
      details: {
        outputKey: key
      }
    };
  }

  return {
    success: true,
    transcript
  };
}

async function normalizeDurationWithBedrock(transcript) {
  const { BedrockRuntimeClient, ConverseCommand } = await import("@aws-sdk/client-bedrock-runtime");
  const client = new BedrockRuntimeClient({});
  const result = await client.send(
    new ConverseCommand({
      modelId: FOOD_CLASSIFICATION_MODEL_ID,
      system: [
        {
          text:
            "You convert spoken expiration duration text into strict JSON. " +
            "The user may speak Traditional Chinese, Simplified Chinese, or English. " +
            "Return one JSON object only. No markdown. No extra text. " +
            "Only accept relative duration expressions, not calendar dates. " +
            "Supported units are days, weeks, and months. " +
            "The duration field must be ISO-8601 date duration: PnD, PnW, or PnM. " +
            "If the text is not a clear duration, return duration null and confidence 0."
        }
      ],
      messages: [
        {
          role: "user",
          content: [
            {
              text:
                `Transcript:\n${transcript}\n\n` +
                "Return JSON with this schema:\n" +
                "{\"duration\": string|null, \"amount\": integer|null, \"unit\": \"days\"|\"weeks\"|\"months\"|null, \"confidence\": number, \"reason\": string}"
            }
          ]
        }
      ],
      inferenceConfig: {
        maxTokens: 512,
        temperature: 0
      }
    })
  );

  const data = parseBedrockJson(result);
  const parsed = parseIsoDateDuration(data.duration);
  if (!parsed) {
    return {
      success: false,
      errorCode: "ML_AMBIGUOUS_DATE",
      message: "Bedrock could not normalize the spoken expiration duration",
      bedrock: data
    };
  }

  const confidence = normalizeClassificationConfidence(data.confidence);
  if (confidence === null || confidence < ML_BEDROCK_DURATION_MIN_CONFIDENCE) {
    return {
      success: false,
      errorCode: "ML_LOW_CONFIDENCE",
      message: "Bedrock duration confidence is below threshold",
      threshold: ML_BEDROCK_DURATION_MIN_CONFIDENCE,
      bedrock: data
    };
  }

  if (data.unit !== parsed.unit || Number(data.amount) !== parsed.amount) {
    return {
      success: false,
      errorCode: "ML_AMBIGUOUS_DATE",
      message: "Bedrock duration fields are internally inconsistent",
      bedrock: data
    };
  }

  return {
    success: true,
    expirationDuration: parsed.isoDuration,
    expirationDurationUnit: parsed.unit,
    expirationDurationAmount: parsed.amount,
    confidence,
    reason: String(data.reason || "")
  };
}

function parseIsoDateDuration(value) {
  const match = String(value || "").trim().toUpperCase().match(/^P([1-9]\d*)([DWM])$/);
  if (!match) return null;
  const amount = Number(match[1]);
  const unit = {
    D: "days",
    W: "weeks",
    M: "months"
  }[match[2]];
  return {
    amount,
    unit,
    isoDuration: `P${amount}${match[2]}`
  };
}

function expirationDateFromDuration(duration, { capturedAt, timezone }) {
  const parsed = parseIsoDateDuration(duration);
  if (!parsed) {
    throw Object.assign(new Error("Invalid ISO-8601 date duration"), {
      name: "InvalidDuration"
    });
  }

  const base = datePartsInTimezone(capturedAt, timezone);
  if (parsed.unit === "days") return formatDate(addDays(base, parsed.amount));
  if (parsed.unit === "weeks") return formatDate(addDays(base, parsed.amount * 7));
  return formatDate(addMonths(base, parsed.amount));
}

function datePartsInTimezone(value, timezone) {
  const raw = String(value || "");
  const localMatch = raw.match(/^(\d{4})-(\d{2})-(\d{2})T\d{2}:\d{2}:\d{2}$/);
  if (localMatch) {
    return {
      year: Number(localMatch[1]),
      month: Number(localMatch[2]),
      day: Number(localMatch[3])
    };
  }

  const date = value ? new Date(value) : new Date();
  if (Number.isNaN(date.getTime())) {
    throw Object.assign(new Error("capturedAt must be an ISO-8601 timestamp"), {
      name: "InvalidCapturedAt"
    });
  }

  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).formatToParts(date);
  return {
    year: Number(parts.find((part) => part.type === "year").value),
    month: Number(parts.find((part) => part.type === "month").value),
    day: Number(parts.find((part) => part.type === "day").value)
  };
}

function addDays(parts, days) {
  const date = new Date(Date.UTC(parts.year, parts.month - 1, parts.day + days));
  return {
    year: date.getUTCFullYear(),
    month: date.getUTCMonth() + 1,
    day: date.getUTCDate()
  };
}

function addMonths(parts, months) {
  const monthIndex = parts.month - 1 + months;
  const year = parts.year + Math.floor(monthIndex / 12);
  const month = (monthIndex % 12) + 1;
  const day = Math.min(parts.day, daysInMonth(year, month));
  return {
    year,
    month,
    day
  };
}

function daysInMonth(year, month) {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

function formatDate(parts) {
  return [
    String(parts.year).padStart(4, "0"),
    String(parts.month).padStart(2, "0"),
    String(parts.day).padStart(2, "0")
  ].join("-");
}

function audioExtensionFromContentType(contentType) {
  return {
    "audio/wav": "wav",
    "audio/wave": "wav",
    "audio/x-wav": "wav",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/mp4": "mp4",
    "audio/m4a": "m4a",
    "audio/x-m4a": "m4a",
    "audio/flac": "flac",
    "audio/ogg": "ogg",
    "audio/amr": "amr",
    "audio/webm": "webm"
  }[contentType];
}

function audioFormatFromUri(mediaUri) {
  const suffix = String(mediaUri).split("?")[0].split(".").pop()?.toLowerCase();
  if (["mp3", "mp4", "wav", "flac", "ogg", "amr", "webm", "m4a"].includes(suffix)) {
    return suffix;
  }
  return null;
}

async function putMediaObject({ bucketName, key, bytes, contentType }) {
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

async function putFoodImageObject({ bucketName, key, bytes, contentType }) {
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

async function publicFoodItems(items) {
  const sorted = [...items].sort((a, b) => String(a.expirationDate || "").localeCompare(String(b.expirationDate || "")));
  return Promise.all(
    sorted.map(async ({ ownerEmail, ownerUserId, updatedAt, ...food }) => ({
      ...food,
      ...(food.foodImage ? { foodImage: await publicFoodImage(food.foodImage) } : {})
    }))
  );
}

async function publicFoodImage(foodImage) {
  const publicImage = {
    s3Key: foodImage.s3Key,
    contentType: foodImage.contentType,
    capturedAt: foodImage.capturedAt
  };

  if (!foodImage.bucket || !foodImage.s3Key || !foodImage.contentType) {
    return publicImage;
  }

  try {
    return {
      ...publicImage,
      url: await getS3ObjectPresignedUrl({
        bucketName: foodImage.bucket,
        key: foodImage.s3Key
      })
    };
  } catch (error) {
    console.warn("Unable to create food image URL", {
      bucket: foodImage.bucket,
      s3Key: foodImage.s3Key,
      error: error.message
    });
    return publicImage;
  }
}

async function getS3ObjectPresignedUrl({ bucketName, key }) {
  const { S3Client, GetObjectCommand } = await import("@aws-sdk/client-s3");
  const { getSignedUrl } = await import("@aws-sdk/s3-request-presigner");
  const client = new S3Client({});
  return getSignedUrl(
    client,
    new GetObjectCommand({
      Bucket: bucketName,
      Key: key
    }),
    { expiresIn: 900 }
  );
}

async function getS3ObjectBytes({ bucketName, key }) {
  const { S3Client, GetObjectCommand } = await import("@aws-sdk/client-s3");
  const client = new S3Client({});
  const result = await client.send(
    new GetObjectCommand({
      Bucket: bucketName,
      Key: key
    })
  );
  return result.Body.transformToByteArray();
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
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

  await sendEmail({
    recipient: ownerEmail,
    subject: "Smart Fridge food alert",
    bodyText: `Someone attempted to retrieve your ${foodName}. Actor user id: ${actorUserId}`
  });
}

async function sendEmailToRecipients({ recipients, subject, bodyText }) {
  if (!SES_FROM_EMAIL || MOCK_MODE) {
    return {
      sent: [],
      failed: recipients.map((email) => ({
        email,
        error: SES_FROM_EMAIL ? "MOCK_MODE" : "SES_FROM_EMAIL_NOT_CONFIGURED"
      }))
    };
  }

  const sent = [];
  const failed = [];
  for (const recipient of recipients) {
    try {
      await sendEmail({ recipient, subject, bodyText });
      sent.push(recipient);
    } catch (error) {
      console.error(`Failed to send email to ${recipient}`, error);
      failed.push({
        email: recipient,
        error: error.name || "SEND_EMAIL_FAILED",
        message: error.message
      });
    }
  }

  return { sent, failed };
}

async function sendEmail({ recipient, subject, bodyText }) {
  const { SESClient, SendEmailCommand } = await import("@aws-sdk/client-ses");
  const client = new SESClient({});
  await client.send(
    new SendEmailCommand({
      Source: SES_FROM_EMAIL,
      Destination: {
        ToAddresses: [recipient]
      },
      Message: {
        Subject: {
          Data: subject
        },
        Body: {
          Text: {
            Data: bodyText
          }
        }
      }
    })
  );
}

function climateAlertsFor({ temperature, humidity }) {
  const alerts = [];
  if (temperature !== null && temperature > CLIMATE_TEMPERATURE_MAX_C) {
    alerts.push({
      type: "temperature-high",
      value: temperature,
      threshold: CLIMATE_TEMPERATURE_MAX_C,
      message: `Temperature is above ${CLIMATE_TEMPERATURE_MAX_C} C`
    });
  }

  if (
    humidity !== null &&
    (humidity < CLIMATE_HUMIDITY_MIN_PERCENT || humidity > CLIMATE_HUMIDITY_MAX_PERCENT)
  ) {
    alerts.push({
      type: humidity < CLIMATE_HUMIDITY_MIN_PERCENT ? "humidity-low" : "humidity-high",
      value: humidity,
      safeRange: {
        min: CLIMATE_HUMIDITY_MIN_PERCENT,
        max: CLIMATE_HUMIDITY_MAX_PERCENT
      },
      message: `Humidity is outside ${CLIMATE_HUMIDITY_MIN_PERCENT}-${CLIMATE_HUMIDITY_MAX_PERCENT}%`
    });
  }

  return alerts;
}

function numberOrNull(value) {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

async function getAllKnownUserEmails() {
  const emails = new Set();
  if (USER_POOL_ID) {
    try {
      for (const email of await listCognitoUserEmails()) {
        addNormalizedEmail(emails, email);
      }
    } catch (error) {
      console.error("Unable to list Cognito users for climate alert recipients", error);
    }
  }

  if (USER_FACE_TABLE_NAME) {
    for (const item of await scanAllItems({
      tableName: USER_FACE_TABLE_NAME,
      projectionExpression: "email"
    })) {
      addNormalizedEmail(emails, item.email);
    }
  }

  if (FOOD_TABLE_NAME) {
    for (const item of await scanAllItems({
      tableName: FOOD_TABLE_NAME,
      projectionExpression: "ownerEmail"
    })) {
      addNormalizedEmail(emails, item.ownerEmail);
    }
  }

  if (emails.size === 0 && mockUser.email) {
    addNormalizedEmail(emails, mockUser.email);
  }

  return [...emails].sort();
}

async function listCognitoUserEmails() {
  const { CognitoIdentityProviderClient, ListUsersCommand } = await import("@aws-sdk/client-cognito-identity-provider");
  const client = new CognitoIdentityProviderClient({});
  const emails = [];
  let PaginationToken;
  do {
    const result = await client.send(
      new ListUsersCommand({
        UserPoolId: USER_POOL_ID,
        PaginationToken
      })
    );
    for (const user of result.Users || []) {
      const emailAttribute = user.Attributes?.find((attribute) => attribute.Name === "email");
      if (emailAttribute?.Value) emails.push(emailAttribute.Value);
    }
    PaginationToken = result.PaginationToken;
  } while (PaginationToken);

  return emails;
}

function addNormalizedEmail(emails, value) {
  const email = normalizeEmail(value);
  if (email && email.includes("@")) emails.add(email);
}

async function scanAllItems({ tableName, projectionExpression }) {
  const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
  const { DynamoDBDocumentClient, ScanCommand } = await import("@aws-sdk/lib-dynamodb");
  const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));
  const items = [];
  let ExclusiveStartKey;
  do {
    const result = await client.send(
      new ScanCommand({
        TableName: tableName,
        ProjectionExpression: projectionExpression,
        ExclusiveStartKey
      })
    );
    items.push(...(result.Items || []));
    ExclusiveStartKey = result.LastEvaluatedKey;
  } while (ExclusiveStartKey);

  return items;
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
  if (!FOOD_TABLE_NAME) {
    return mockFoods.find((food) => food.foodId === foodId) || null;
  }

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

async function findFoodByName({ foodName, ownerUserId }) {
  const foodNames = equivalentFoodNames(foodName);
  if (foodNames.length === 0) return null;

  if (!FOOD_TABLE_NAME) {
    return mockFoods.find((food) => foodNames.includes(catalogFoodId(food.foodName))) || null;
  }

  const expressionAttributeValues = Object.fromEntries(foodNames.map((name, index) => [`:foodName${index}`, name]));
  const foodNamePlaceholders = Object.keys(expressionAttributeValues).join(", ");

  if (ownerUserId) {
    const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
    const { DynamoDBDocumentClient, QueryCommand } = await import("@aws-sdk/lib-dynamodb");
    const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));
    const result = await client.send(
      new QueryCommand({
        TableName: FOOD_TABLE_NAME,
        IndexName: "OwnerExpirationIndex",
        KeyConditionExpression: "ownerUserId = :ownerUserId",
        FilterExpression: `foodName IN (${foodNamePlaceholders})`,
        ExpressionAttributeValues: {
          ":ownerUserId": ownerUserId,
          ...expressionAttributeValues
        }
      })
    );
    return result.Items?.[0] || null;
  }

  const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
  const { DynamoDBDocumentClient, ScanCommand } = await import("@aws-sdk/lib-dynamodb");
  const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));
  const result = await client.send(
    new ScanCommand({
      TableName: FOOD_TABLE_NAME,
      FilterExpression: `foodName IN (${foodNamePlaceholders})`,
      ExpressionAttributeValues: expressionAttributeValues
    })
  );
  return result.Items?.[0] || null;
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
  if (!audioExtensionFromContentType(contentType) || !isBase64Like(base64Value)) {
    return {
      success: false,
      errorCode: "INVALID_AUDIO",
      message: "Audio must be base64 encoded WAV, MP3, MP4, M4A, FLAC, OGG, AMR, or WEBM"
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
