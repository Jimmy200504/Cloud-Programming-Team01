#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-ap-northeast-1}"
BOT_NAME="${BOT_NAME:-SmartFridgeInventoryBot}"
LOCALE_ID="${LEX_LOCALE_ID:-en_US}"
BOT_ALIAS_NAME="${BOT_ALIAS_NAME:-prod}"

if [[ -z "${LEX_ROLE_ARN:-}" ]]; then
  echo "Missing LEX_ROLE_ARN." >&2
  echo "Usage: LEX_ROLE_ARN=arn:aws:iam::<account-id>:role/<lex-role> $0" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

utterances_file() {
  local file="$1"
  shift
  printf '[' > "$file"
  local first=1
  for utterance in "$@"; do
    if [[ "$first" -eq 0 ]]; then
      printf ',' >> "$file"
    fi
    first=0
    python3 -c 'import json,sys; print(json.dumps({"utterance": sys.argv[1]}, ensure_ascii=False), end="")' "$utterance" >> "$file"
  done
  printf ']' >> "$file"
}

wait_for_bot_status() {
  local bot_id="$1"
  local wanted="$2"
  local status
  for _ in {1..60}; do
    status="$(aws lexv2-models describe-bot \
      --region "$REGION" \
      --bot-id "$bot_id" \
      --query 'botStatus' \
      --output text)"
    if [[ "$status" == "$wanted" ]]; then
      return 0
    fi
    if [[ "$status" == "Failed" || "$status" == "Deleting" ]]; then
      echo "Bot reached unexpected status: $status" >&2
      return 1
    fi
    sleep 5
  done
  echo "Timed out waiting for bot status $wanted" >&2
  return 1
}

wait_for_locale_status() {
  local bot_id="$1"
  local wanted="$2"
  local status
  for _ in {1..90}; do
    status="$(aws lexv2-models describe-bot-locale \
      --region "$REGION" \
      --bot-id "$bot_id" \
      --bot-version DRAFT \
      --locale-id "$LOCALE_ID" \
      --query 'botLocaleStatus' \
      --output text)"
    if [[ "$status" == "$wanted" ]]; then
      return 0
    fi
    if [[ "$status" == "Failed" || "$status" == "Deleting" ]]; then
      echo "Locale reached unexpected status: $status" >&2
      aws lexv2-models describe-bot-locale \
        --region "$REGION" \
        --bot-id "$bot_id" \
        --bot-version DRAFT \
        --locale-id "$LOCALE_ID" >&2 || true
      return 1
    fi
    sleep 10
  done
  echo "Timed out waiting for locale status $wanted" >&2
  return 1
}

create_intent() {
  local bot_id="$1"
  local intent_name="$2"
  local file="$3"
  aws lexv2-models create-intent \
    --region "$REGION" \
    --bot-id "$bot_id" \
    --bot-version DRAFT \
    --locale-id "$LOCALE_ID" \
    --intent-name "$intent_name" \
    --sample-utterances "file://$file" \
    --query 'intentId' \
    --output text
}

echo "Creating Lex V2 bot: $BOT_NAME ($REGION)"
BOT_ID="$(aws lexv2-models create-bot \
  --region "$REGION" \
  --bot-name "$BOT_NAME" \
  --role-arn "$LEX_ROLE_ARN" \
  --data-privacy childDirected=false \
  --idle-session-ttl-in-seconds 300 \
  --query 'botId' \
  --output text)"

wait_for_bot_status "$BOT_ID" "Available"

echo "Creating locale: $LOCALE_ID"
aws lexv2-models create-bot-locale \
  --region "$REGION" \
  --bot-id "$BOT_ID" \
  --bot-version DRAFT \
  --locale-id "$LOCALE_ID" \
  --nlu-intent-confidence-threshold 0.4 \
  --query 'botLocaleStatus' \
  --output text >/dev/null

wait_for_locale_status "$BOT_ID" "NotBuilt"

utterances_file "$TMP_DIR/check_inventory.json" \
  "What is in my fridge" \
  "List my fridge inventory" \
  "Show my inventory" \
  "What food do I have" \
  "冰箱裡有什麼" \
  "目前庫存"

utterances_file "$TMP_DIR/nearest_expiration.json" \
  "What expires first" \
  "Which food expires next" \
  "What is the first expiring item" \
  "最快到期的是什麼" \
  "第一個快過期的是什麼" \
  "哪個先過期"

utterances_file "$TMP_DIR/expiring_soon.json" \
  "What is expiring soon" \
  "Show food expiring soon" \
  "Which items expire in two days" \
  "快過期有哪些" \
  "即將過期的食物"

utterances_file "$TMP_DIR/expired_food.json" \
  "What is expired" \
  "Show expired food" \
  "Which items are late" \
  "已過期有哪些" \
  "過期了的食物"

utterances_file "$TMP_DIR/count_inventory.json" \
  "How many items are in my fridge" \
  "Count my food" \
  "How much food do I have" \
  "目前有幾項食物" \
  "冰箱有多少東西"

utterances_file "$TMP_DIR/food_lookup.json" \
  "Do I have {FoodName}" \
  "Is there {FoodName} in my fridge" \
  "When does {FoodName} expire" \
  "有 {FoodName} 嗎" \
  "{FoodName} 什麼時候到期"

echo "Creating intents"
create_intent "$BOT_ID" "CheckInventoryIntent" "$TMP_DIR/check_inventory.json" >/dev/null
create_intent "$BOT_ID" "NearestExpirationIntent" "$TMP_DIR/nearest_expiration.json" >/dev/null
create_intent "$BOT_ID" "ExpiringSoonIntent" "$TMP_DIR/expiring_soon.json" >/dev/null
create_intent "$BOT_ID" "ExpiredFoodIntent" "$TMP_DIR/expired_food.json" >/dev/null
create_intent "$BOT_ID" "CountInventoryIntent" "$TMP_DIR/count_inventory.json" >/dev/null
FOOD_LOOKUP_INTENT_ID="$(create_intent "$BOT_ID" "FoodLookupIntent" "$TMP_DIR/food_lookup.json")"

echo "Creating FoodName slot"
aws lexv2-models create-slot \
  --region "$REGION" \
  --bot-id "$BOT_ID" \
  --bot-version DRAFT \
  --locale-id "$LOCALE_ID" \
  --intent-id "$FOOD_LOOKUP_INTENT_ID" \
  --slot-name FoodName \
  --slot-type-id AMAZON.AlphaNumeric \
  --value-elicitation-setting 'slotConstraint=Optional' \
  --query 'slotId' \
  --output text >/dev/null

echo "Building locale"
aws lexv2-models build-bot-locale \
  --region "$REGION" \
  --bot-id "$BOT_ID" \
  --bot-version DRAFT \
  --locale-id "$LOCALE_ID" \
  --query 'botLocaleStatus' \
  --output text >/dev/null

wait_for_locale_status "$BOT_ID" "Built"

echo "Creating bot version"
BOT_VERSION="$(aws lexv2-models create-bot-version \
  --region "$REGION" \
  --bot-id "$BOT_ID" \
  --bot-version-locale-specification "$LOCALE_ID={sourceBotVersion=DRAFT}" \
  --query 'botVersion' \
  --output text)"

echo "Creating alias: $BOT_ALIAS_NAME"
BOT_ALIAS_ID="$(aws lexv2-models create-bot-alias \
  --region "$REGION" \
  --bot-id "$BOT_ID" \
  --bot-alias-name "$BOT_ALIAS_NAME" \
  --bot-version "$BOT_VERSION" \
  --query 'botAliasId' \
  --output text)"

cat <<EOF

Lex bot created.

LexBotId=$BOT_ID
LexBotAliasId=$BOT_ALIAS_ID
LexLocaleId=$LOCALE_ID

Deploy backend with:

sam deploy --parameter-overrides \\
  StageName=dev \\
  DeviceId=smart-fridge-001 \\
  MockMode=false \\
  SesFromEmail=gaga555lala@gmail.com \\
  LambdaExecutionRoleArn=arn:aws:iam::491919374787:role/SmartFridgeLambdaExecutionRole \\
  LambdaExecutionRoleName=SmartFridgeLambdaExecutionRole \\
  LexBotId=$BOT_ID \\
  LexBotAliasId=$BOT_ALIAS_ID \\
  LexLocaleId=$LOCALE_ID
EOF
