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
- `docs/rekognition-integration-guide.md`: notes for the Rekognition integration owner.
- `docs/interface-contract.md`: original broader MVP interface contract.

## Deploy

Install and configure the AWS SAM CLI, then run:

```bash
cd aws-backend
sam build
sam deploy --guided
```

Suggested stack name:

```text
smart-fridge-dev-yourname
```

The `SesFromEmail` parameter must be a verified SES sender address if real email sending is enabled later. It can be left empty for the current MVP setup.

The Lambda function uses an existing execution role through the `LambdaExecutionRoleArn` parameter. The deploying AWS user needs `iam:PassRole` for that role.

The Lambda execution role needs these permissions for the current backend:

```text
AWSLambdaBasicExecutionRole
cognito-idp:SignUp
dynamodb:PutItem
dynamodb:GetItem
dynamodb:Query
s3:PutObject
rekognition:IndexFaces
rekognition:SearchFacesByImage
```

Device Shadow, SES, and full retrieve-food flows also need IoT, SES, and DynamoDB delete/update permissions.

For Rekognition face integration, add at least:

```json
{
  "Effect": "Allow",
  "Action": [
    "rekognition:IndexFaces",
    "rekognition:SearchFacesByImage",
    "rekognition:DescribeCollection"
  ],
  "Resource": "arn:aws:rekognition:ap-northeast-1:491919374787:collection/ml-smart-fridge-faces"
}
```

## Current Runtime Mode

The Lambda is deployed with:

```text
MOCK_MODE=true
```

Current real behavior:

- `POST /auth/signup` calls Cognito.
- `POST /users/me/face` calls Rekognition `IndexFaces`, writes the uploaded image to S3, and writes the user-face mapping to DynamoDB.
- `POST /foods/put` writes food items to DynamoDB.
- `POST /test/owner-check` reads the food item from DynamoDB, calls Rekognition `SearchFacesByImage`, maps the face to Cognito through DynamoDB, and checks ownership.

Current starter/mock behavior:

- retrieve food succeeds unless `userId` is `mock-not-owner`
- device state returns fixed lock, LED, temperature, and humidity data

When `MOCK_MODE=false`, the same Lambda has starter logic for:

- querying `SmartFridgeFoods-${StageName}` through `OwnerExpirationIndex`
- deleting retrieved food items from DynamoDB
- reading and updating IoT Device Shadow
- sending SES email for unauthorized retrieval when `SesFromEmail` is configured

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
