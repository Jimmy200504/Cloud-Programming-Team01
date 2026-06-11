# Amazon Lex Inventory Chatbot Integration

This project now supports an Amazon Lex V2 inventory chatbot path:

```text
React Fridge Chat
  -> POST /chat/message
  -> API Gateway
  -> Lambda smart-fridge-dev-api-handler
  -> Amazon Lex V2 RecognizeText when configured
  -> DynamoDB inventory answer from Lambda
```

The frontend never calls Lex directly and does not need AWS credentials. It calls the existing backend with the Cognito ID token. The backend uses Lex as an intent classifier, then answers from DynamoDB.

## Runtime Behavior

If these Lambda environment variables are empty, the chatbot still works with local intent rules:

```text
LEX_BOT_ID
LEX_BOT_ALIAS_ID
LEX_LOCALE_ID
```

When `LEX_BOT_ID` and `LEX_BOT_ALIAS_ID` are configured, Lambda calls Lex V2 `RecognizeText`. If Lex fails, Lambda falls back to local inventory logic so the frontend remains usable.

## Backend API

```text
POST /chat/message
Authorization: Bearer <Cognito ID token>
Content-Type: application/json
```

Request:

```json
{
  "message": "第一個快過期的是什麼",
  "sessionId": "cognito-user-sub"
}
```

Response:

```json
{
  "success": true,
  "message": "最先快過期的是 banana，2026-06-13 到期，剩 1 天。",
  "source": "lex",
  "lex": {
    "used": true,
    "intentName": "NearestExpirationIntent",
    "confidence": 0.99
  },
  "inventoryCount": 3
}
```

If Lex is not configured:

```json
{
  "success": true,
  "message": "最先快過期的是 banana，2026-06-13 到期，剩 1 天。",
  "source": "local",
  "lex": {
    "used": false,
    "reason": "LEX_NOT_CONFIGURED"
  },
  "inventoryCount": 3
}
```

## Suggested Lex Bot

Create a Lex V2 bot named:

```text
SmartFridgeInventoryBot
```

Use locale:

```text
en_US
```

The current code can still understand Chinese text after Lex classification, because Lambda performs the final answer. Lex V2 Chinese locale availability depends on region and account features, so `en_US` is the safest default for deployment in `ap-northeast-1`.

## Suggested Intents

### CheckInventoryIntent

Sample utterances:

```text
What is in my fridge
List my fridge inventory
Show my inventory
What food do I have
冰箱裡有什麼
目前庫存
```

### NearestExpirationIntent

Sample utterances:

```text
What expires first
Which food expires next
What is the first expiring item
最快到期的是什麼
第一個快過期的是什麼
哪個先過期
```

### ExpiringSoonIntent

Sample utterances:

```text
What is expiring soon
Show food expiring soon
Which items expire in two days
快過期有哪些
即將過期的食物
```

### ExpiredFoodIntent

Sample utterances:

```text
What is expired
Show expired food
Which items are late
已過期有哪些
過期了的食物
```

### CountInventoryIntent

Sample utterances:

```text
How many items are in my fridge
Count my food
How much food do I have
目前有幾項食物
冰箱有多少東西
```

### FoodLookupIntent

Add one slot:

```text
Slot name: FoodName
Slot type: AMAZON.AlphaNumeric or a custom FoodName slot type
```

Sample utterances:

```text
Do I have {FoodName}
Is there {FoodName} in my fridge
When does {FoodName} expire
有 {FoodName} 嗎
{FoodName} 什麼時候到期
```

Suggested custom slot values:

```text
milk
soy milk
banana
apple
egg
bread
yogurt
cheese
soft drink
cola
豆漿
牛奶
香蕉
蘋果
蛋
麵包
優格
汽水
可樂
```

## Configure Lambda After Creating Lex Bot

You can create the suggested bot with the included CLI script:

```bash
cd aws-backend
chmod +x scripts/create-lex-inventory-bot.sh
LEX_ROLE_ARN=arn:aws:iam::<account-id>:role/<lex-runtime-role> \
  scripts/create-lex-inventory-bot.sh
```

Optional environment variables:

```text
AWS_REGION=ap-northeast-1
BOT_NAME=SmartFridgeInventoryBot
LEX_LOCALE_ID=en_US
BOT_ALIAS_NAME=prod
```

The script prints `LexBotId`, `LexBotAliasId`, and `LexLocaleId` after creating the bot.

The role passed through `LEX_ROLE_ARN` must be assumable by Lex V2 and should allow the Lex service to write logs if you enable logging later. The IAM user running the script needs Lex model-building permissions and `iam:PassRole` for that role.

After the bot is built and an alias is created, deploy with:

```bash
cd aws-backend
sam deploy \
  --parameter-overrides \
  StageName=dev \
  DeviceId=smart-fridge-001 \
  MockMode=false \
  SesFromEmail=gaga555lala@gmail.com \
  LambdaExecutionRoleArn=arn:aws:iam::491919374787:role/SmartFridgeLambdaExecutionRole \
  LambdaExecutionRoleName=SmartFridgeLambdaExecutionRole \
  LexBotId=<your-lex-bot-id> \
  LexBotAliasId=<your-lex-bot-alias-id> \
  LexLocaleId=en_US
```

The Lambda execution role needs Lex runtime permission:

```json
{
  "Effect": "Allow",
  "Action": [
    "lex:RecognizeText",
    "lex:RecognizeUtterance",
    "lex:GetSession",
    "lex:PutSession",
    "lex:DeleteSession"
  ],
  "Resource": "arn:aws:lex:ap-northeast-1:491919374787:bot-alias/*"
}
```

If this permission is missing, the API still responds through local fallback, and logs the Lex error in CloudWatch.
