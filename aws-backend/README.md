# Smart Fridge AWS Backend

This folder contains the Cloud Architect MVP setup:

- Amazon Cognito User Pool and web app client
- DynamoDB food inventory table with `OwnerExpirationIndex`
- AWS IoT Core Thing and device policy for Device Shadow
- S3 bucket for user face images
- API Gateway routes
- Lambda handler for the agreed interface contract
- SES permissions for future notification logic

The current MVP uses real Cognito, S3, Rekognition, and DynamoDB for signup, face upload, face matching, and owner-check testing. Some device and final food-retrieval behavior still has starter/mock logic.

## Structure

```text
aws-backend/
  template.yaml
  lambdas/api-handler/index.mjs
  dynamodb/schema.json
  docs/final-design.md
  docs/frontend-api-contract.md
  docs/interface-contract.md
```

## Current Documents

- `docs/final-design.md`: current deployed design, completed scope, data flow, and configurable items.
- `docs/frontend-api-contract.md`: API contract and Cognito calls for frontend integration.
- `docs/hardware-embedded-integration-guide.md`: microphone, camera, IoT Shadow, LED, and lock integration notes for hardware.
- `docs/rekognition-integration-guide.md`: notes for the Rekognition integration owner.
- `docs/interface-contract.md`: original broader MVP interface contract.

## Deploy

If you only need to read the code or call the existing shared dev backend, no backend deploy is required.

If you need to deploy your own backend stack, first review `samconfig.toml`. The checked-in file is for the current dev/demo stack and contains account-specific values:

```text
stack_name
s3_prefix
region
StageName
DeviceId
MockMode
SesFromEmail
LambdaExecutionRoleArn
LambdaExecutionRoleName
```

Before deploying to another AWS account or another stack, change at least:

```text
stack_name
s3_prefix
SesFromEmail
LambdaExecutionRoleArn
LambdaExecutionRoleName
```

Use `MockMode=true` for safe frontend/backend development when you do not want real IoT Shadow writes, DynamoDB deletes during retrieve, or SES emails. Use `MockMode=false` only for cloud integration testing.

Install and configure the AWS SAM CLI, then run:

```bash
cd aws-backend
cd lambdas/api-handler
npm install
cd ../..
sam build
sam deploy --guided
```

Suggested stack name:

```text
smart-fridge-dev-yourname
```

The `SesFromEmail` parameter must be a verified SES sender address if real email sending is enabled later. It can be left empty for the current MVP setup.

The Lambda function uses an existing execution role through the `LambdaExecutionRoleArn` parameter. The deploying AWS user needs `iam:PassRole` for that role.
Set `LambdaExecutionRoleName` to the role name portion of that ARN so CloudFormation can attach the IoT Device Shadow and SES permissions.
Set `MockMode=false` only when you want real DynamoDB delete, IoT Device Shadow, and SES calls.

## 12-Factor Configuration

Runtime configuration should be changed through SAM parameters or deployment parameter overrides, not by editing Lambda code. This keeps build, release, and runtime configuration separate.

Common parameter overrides:

```text
StageName
DeviceId
MockMode
SesFromEmail
LambdaExecutionRoleArn
LambdaExecutionRoleName
RekognitionCollectionId
FaceMatchThreshold
FoodClassificationEnabled
FoodClassificationModelId
FoodClassificationMinConfidence
RekognitionLabelMinConfidence
MlS3BucketName
MlTimezone
MlTranscribeLanguageCode
MlTranscribeIdentifyLanguage
MlTranscribeLanguageOptions
MlTranscribePollSeconds
MlTranscribeTimeoutSeconds
MlBedrockDurationMinConfidence
```

Recommended local/frontend-development setting:

```text
MockMode=true
SesFromEmail=""
FoodClassificationEnabled=true
```

Use this when you want to avoid real IoT Shadow writes, DynamoDB delete during retrieve, and SES emails.

Recommended cloud-integration setting:

```text
MockMode=false
SesFromEmail=<verified SES sender email>
```

Use this only after the Lambda role has IoT/SES/DynamoDB permissions and the SES sender identity is verified. If the AWS account is still in SES sandbox, recipient owner emails must also be verified.

Parameter notes:

- `StageName` changes API Gateway stage names and resource names. Changing it creates or points to different stage-specific resources.
- `DeviceId` must match the IoT Thing name and the Raspberry Pi MQTT client id used by the device policy.
- `MockMode=false` is required for real IoT Shadow reads/writes, real retrieve deletes, and real SES owner email attempts.
- `SesFromEmail` only sends real email when it is non-empty, verified in SES, and `MockMode=false`.
- `RekognitionCollectionId` must match an existing Rekognition collection that Lambda can access.
- `FaceMatchThreshold` can be increased for stricter face matching. Higher values reduce false positives but may reject valid users.
- `FoodClassificationEnabled=false` skips Bedrock food classification and uses fallback/mock classification logic.
- `FoodClassificationModelId` must match a Bedrock model or inference profile that the Lambda role can invoke. Inference profiles may also require permission for routed foundation model ARNs.
- `MlS3BucketName` can override the default `ml-smart-fridge-media-${AccountId}-${Region}-an` bucket. The bucket must exist, and Lambda must have `s3:PutObject` and `s3:GetObject` for it.
- `MlTimezone` controls how relative expiration durations become calendar dates.
- `MlTranscribeLanguageCode`, `MlTranscribeIdentifyLanguage`, and `MlTranscribeLanguageOptions` must stay compatible with Amazon Transcribe.
- `MlTranscribeTimeoutSeconds` must be lower than or equal to the Lambda timeout if audio parsing happens inside the same Lambda invocation.
- `MlBedrockDurationMinConfidence` controls how strict expiration duration parsing is.

Avoid long-term manual changes through `aws lambda update-function-configuration`. If you must use CLI for a quick test, copy the final setting back into `samconfig.toml` or deployment parameters so the next `sam deploy` is reproducible.

The Lambda execution role needs these permissions for the current backend:

```text
AWSLambdaBasicExecutionRole
cognito-idp:SignUp
dynamodb:PutItem
dynamodb:GetItem
dynamodb:Query
dynamodb:Scan
dynamodb:DeleteItem
s3:PutObject
s3:GetObject
rekognition:IndexFaces
rekognition:SearchFacesByImage
rekognition:DetectLabels
transcribe:StartTranscriptionJob
transcribe:GetTranscriptionJob
bedrock:InvokeModel
iot:GetThingShadow
iot:UpdateThingShadow
ses:SendEmail
ses:SendRawEmail
```

The SAM template attaches the IoT Device Shadow and SES permissions to `LambdaExecutionRoleName`.

For Rekognition face integration, add at least:

```json
{
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rekognition:IndexFaces",
        "rekognition:SearchFacesByImage",
        "rekognition:DescribeCollection"
      ],
      "Resource": "arn:aws:rekognition:ap-northeast-1:491919374787:collection/ml-smart-fridge-faces"
    },
    {
      "Effect": "Allow",
      "Action": "rekognition:DetectLabels",
      "Resource": "*"
    }
  ]
}
```

For Bedrock food classification, add model invoke permission for the configured model:

```json
{
  "Effect": "Allow",
  "Action": "bedrock:InvokeModel",
  "Resource": [
    "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
    "arn:aws:bedrock:ap-northeast-3::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
    "arn:aws:bedrock:ap-northeast-1:491919374787:inference-profile/jp.anthropic.claude-haiku-4-5-20251001-v1:0"
  ]
}
```

The `jp.` model id is an inference profile id. It currently routes to foundation models in `ap-northeast-1` and `ap-northeast-3`, so the Lambda role must allow both routed foundation model ARNs plus the account-scoped `inference-profile` ARN from the runtime error.

For expiration audio parsing, the Lambda role also needs access to the configured `ML_S3_BUCKET` and Transcribe:

```json
{
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::ml-smart-fridge-media-491919374787-ap-northeast-1-an/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "transcribe:StartTranscriptionJob",
        "transcribe:GetTranscriptionJob"
      ],
      "Resource": "*"
    }
  ]
}
```

## Current Runtime Mode

The Lambda is deployed with:

```text
MOCK_MODE=<MockMode parameter>
```

Current real behavior:

- `POST /auth/signup` calls Cognito.
- `POST /users/me/face` calls Rekognition `IndexFaces`, writes the uploaded image to S3, and writes the user-face mapping to DynamoDB.
- `POST /foods/detect` classifies a food image with Rekognition labels plus Bedrock catalog selection.
- `POST /expiration/parse` converts expiration audio or transcript text into an expiration date through Transcribe and Bedrock.
- `POST /foods/put` can classify `foodImageBase64`, parse `expirationAudioBase64`, stores the catalog `foodName`, and writes food items to DynamoDB.
- `POST /foods/retrieve` can classify `foodImageBase64` to find the stored food item when `foodId` is not supplied.
- `GET /foods/me` returns the current user's inventory sorted by expiration date, including food image display data when available.
- `POST /test/owner-check` reads the food item from DynamoDB, calls Rekognition `SearchFacesByImage`, maps the face to Cognito through DynamoDB, and checks ownership.

Current starter/mock behavior:

- retrieve food succeeds unless `userId` is `mock-not-owner`
- device state returns fixed lock, LED, temperature, and humidity data

When `MOCK_MODE=false`, the same Lambda has starter logic for:

- querying `SmartFridgeFoods-${StageName}` through `OwnerExpirationIndex`
- deleting retrieved food items from DynamoDB
- reading and updating IoT Device Shadow
- sending SES email for unauthorized retrieval when `SesFromEmail` is configured

## IoT Device Shadow And SES Pre-Hardware Test

Keep `MockMode=true` for the normal frontend demo. To test the cloud integration before Raspberry Pi hardware is connected, deploy with:

```bash
sam deploy \
  --parameter-overrides \
  StageName=dev \
  DeviceId=smart-fridge-001 \
  MockMode=false \
  SesFromEmail=verified-sender@example.com \
  LambdaExecutionRoleArn=arn:aws:iam::491919374787:role/SmartFridgeLambdaExecutionRole \
  LambdaExecutionRoleName=SmartFridgeLambdaExecutionRole
```

Seed a reported shadow state from your AWS CLI:

```bash
aws iot-data update-thing-shadow \
  --thing-name smart-fridge-001 \
  --payload '{"state":{"reported":{"lock":"locked","led":"off","temperature":4.2,"humidity":55,"lastSeenAt":"2026-06-04T00:00:00Z"}}}' \
  /tmp/smart-fridge-shadow-response.json
```

Then `GET /device/smart-fridge-001/state` should read the reported values, and `POST /device/smart-fridge-001/lock` with `{"desiredLock":"unlocked"}` should update the shadow desired lock state.

SES email only sends when all of these are true:

- `MockMode=false`
- `SesFromEmail` is not empty
- the sender address is verified in SES
- if the AWS account is still in SES sandbox, the recipient owner email is also verified

## Local Lambda Smoke Test

From the repository root:

```bash
node --check aws-backend/lambdas/api-handler/index.mjs
node --input-type=module -e "import('./aws-backend/lambdas/api-handler/index.mjs').then(async ({ handler }) => console.log(await handler({ httpMethod: 'GET', path: '/foods/me' })))"
```

## Important Outputs

After deploy, share these values with the frontend and Raspberry Pi teams:

- `ApiBaseUrl`
- `UserPoolId`
- `UserPoolClientId`
- `FoodTableName`
- `ThingName`
- `DevicePolicyName`

## Device Certificate Note

CloudFormation creates the IoT Thing and IoT Policy, but the Raspberry Pi still needs an IoT certificate and private key. Create those in the AWS IoT Core console or CLI, then attach:

- the generated certificate to `smart-fridge-001`
- the `DevicePolicyName` output policy to the certificate

The Raspberry Pi should subscribe to Device Shadow delta topics and report `lock`, `led`, `temperature`, `humidity`, and `lastSeenAt`.
