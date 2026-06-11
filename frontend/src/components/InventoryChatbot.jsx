import { Bot, RefreshCw, Send, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import { getFoodDisplayName } from "../utils/food";
import { daysUntil, formatDate } from "../utils/format";
import StatusBadge from "./StatusBadge";

const FOOD_TERMS = [
  { id: "soy_milk", terms: ["soy milk", "soymilk", "豆漿", "豆浆"] },
  { id: "milk", terms: ["milk", "牛奶"] },
  { id: "apple", terms: ["apple", "蘋果", "苹果"] },
  { id: "banana", terms: ["banana", "香蕉"] },
  { id: "egg", terms: ["egg", "eggs", "蛋", "雞蛋", "鸡蛋"] },
  { id: "bread", terms: ["bread", "toast", "麵包", "面包", "吐司"] },
  { id: "cheese", terms: ["cheese", "起司", "乳酪"] },
  { id: "yogurt", terms: ["yogurt", "yoghurt", "優格", "优格", "酸奶"] },
  { id: "chicken", terms: ["chicken", "雞肉", "鸡肉"] },
  { id: "pork", terms: ["pork", "豬肉", "猪肉"] },
  { id: "beef", terms: ["beef", "牛肉"] },
  { id: "fish", terms: ["fish", "魚", "鱼"] },
  { id: "vegetable", terms: ["vegetable", "vegetables", "蔬菜"] },
  { id: "fruit", terms: ["fruit", "fruits", "水果"] },
  { id: "soft_drink", terms: ["soft drink", "soft drinks", "cola", "coke", "soda", "汽水", "可樂", "可乐"] },
  { id: "beverage", terms: ["beverage", "drink", "飲料", "饮料"] }
];

const QUICK_PROMPTS = ["冰箱裡有什麼？", "快過期有哪些？", "有豆漿嗎？"];

export default function InventoryChatbot({ foods, loading, onRefresh }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState(() => [
    {
      role: "assistant",
      text: "我可以查目前庫存、到期日和快過期食物。"
    }
  ]);
  const summary = useMemo(() => summarizeInventory(foods), [foods]);

  async function handleSubmit(event) {
    event.preventDefault();
    const question = input.trim();
    if (!question) return;

    setMessages((current) => [
      ...current,
      { role: "user", text: question },
      { role: "assistant", text: answerInventoryQuestion(question, foods, summary) }
    ]);
    setInput("");
  }

  function askQuickPrompt(prompt) {
    setInput(prompt);
    setMessages((current) => [
      ...current,
      { role: "user", text: prompt },
      { role: "assistant", text: answerInventoryQuestion(prompt, foods, summary) }
    ]);
  }

  return (
    <section className="panel chatbot-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Assistant</p>
          <h2>Fridge Chat</h2>
        </div>
        <div className="heading-actions">
          <StatusBadge tone={loading ? "busy" : "ready"}>{loading ? "Syncing" : `${foods.length} items`}</StatusBadge>
          <button className="icon-button" type="button" onClick={onRefresh} disabled={loading} aria-label="Refresh inventory before chatting">
            <RefreshCw size={18} className={loading ? "spin" : ""} />
          </button>
        </div>
      </div>

      <div className="chat-window" aria-live="polite">
        {messages.map((message, index) => (
          <div className={`chat-message ${message.role}`} key={`${message.role}-${index}-${message.text.slice(0, 12)}`}>
            <span className="chat-avatar">{message.role === "assistant" ? <Bot size={16} /> : <Sparkles size={16} />}</span>
            <p>{message.text}</p>
          </div>
        ))}
      </div>

      <div className="quick-prompts">
        {QUICK_PROMPTS.map((prompt) => (
          <button className="ghost-button" type="button" key={prompt} onClick={() => askQuickPrompt(prompt)}>
            {prompt}
          </button>
        ))}
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="問冰箱內容物..." />
        <button type="submit" aria-label="Send inventory question">
          <Send size={18} />
        </button>
      </form>
    </section>
  );
}

function answerInventoryQuestion(question, foods, summary) {
  if (foods.length === 0) {
    return "目前庫存是空的。";
  }

  const normalized = normalizeText(question);
  const matchedFoods = findMentionedFoods(normalized, foods);

  if (asksExpiringSoon(normalized)) {
    return formatFoodList(summary.expiringSoon, "接下來 2 天內快過期的食物", "目前沒有 2 天內快過期的食物。");
  }

  if (asksExpired(normalized)) {
    return formatFoodList(summary.expired, "已過期的食物", "目前沒有已過期的食物。");
  }

  if (asksCount(normalized)) {
    return `目前冰箱裡共有 ${foods.length} 項食物。${summary.countsText ? ` ${summary.countsText}` : ""}`;
  }

  if (matchedFoods.length > 0) {
    return formatMatchedFoods(matchedFoods);
  }

  if (asksAllInventory(normalized)) {
    return formatFoodList(summary.sortedFoods, "目前冰箱內容物", "目前庫存是空的。");
  }

  return `目前有 ${foods.length} 項食物。${formatFoodList(summary.sortedFoods.slice(0, 5), "庫存摘要", "")}`;
}

function summarizeInventory(foods) {
  const sortedFoods = [...foods].sort((a, b) => {
    const left = daysUntil(a.expirationDate);
    const right = daysUntil(b.expirationDate);
    if (left === null && right === null) return 0;
    if (left === null) return 1;
    if (right === null) return -1;
    return left - right;
  });
  const expiringSoon = sortedFoods.filter((food) => {
    const days = daysUntil(food.expirationDate);
    return days !== null && days >= 0 && days <= 2;
  });
  const expired = sortedFoods.filter((food) => {
    const days = daysUntil(food.expirationDate);
    return days !== null && days < 0;
  });
  const counts = new Map();
  for (const food of foods) {
    const name = getFoodDisplayName(food);
    counts.set(name, (counts.get(name) || 0) + 1);
  }
  const countsText = [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 4)
    .map(([name, count]) => `${name} ${count} 項`)
    .join("、");

  return { sortedFoods, expiringSoon, expired, countsText };
}

function findMentionedFoods(normalizedQuestion, foods) {
  const matchedIds = new Set();
  for (const entry of FOOD_TERMS) {
    if (entry.terms.some((term) => normalizedQuestion.includes(normalizeText(term)))) {
      matchedIds.add(normalizeText(entry.id));
    }
  }

  return foods.filter((food) => {
    const names = [
      food.foodName,
      food.foodClassification?.foodName,
      food.foodClassification?.displayName,
      getFoodDisplayName(food)
    ].map(normalizeText);

    return names.some((name) => matchedIds.has(name) || normalizedQuestion.includes(name));
  });
}

function formatMatchedFoods(foods) {
  if (foods.length === 0) return "目前沒有找到你問的食物。";
  const foodName = getFoodDisplayName(foods[0]);
  return `有，找到 ${foods.length} 項 ${foodName}。${foods.map(formatFoodLine).join("；")}`;
}

function formatFoodList(foods, title, emptyText) {
  if (foods.length === 0) return emptyText;
  return `${title}：${foods.map(formatFoodLine).join("；")}`;
}

function formatFoodLine(food) {
  const days = daysUntil(food.expirationDate);
  const daysText = days === null ? "剩餘天數未知" : days < 0 ? `已過期 ${Math.abs(days)} 天` : `剩 ${days} 天`;
  return `${getFoodDisplayName(food)}，${formatDate(food.expirationDate)} 到期，${daysText}`;
}

function asksExpiringSoon(value) {
  return ["快過期", "即將過期", "soon", "expire soon", "expiring"].some((term) => value.includes(term));
}

function asksExpired(value) {
  return ["已過期", "過期了", "expired", "late"].some((term) => value.includes(term));
}

function asksCount(value) {
  return ["幾個", "幾項", "多少", "count", "how many"].some((term) => value.includes(term));
}

function asksAllInventory(value) {
  return ["有什麼", "內容物", "庫存", "清單", "inventory", "list", "what"].some((term) => value.includes(term));
}

function normalizeText(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[_-]+/g, " ");
}
