export function getFoodDisplayName(food) {
  return food.foodName || food.foodClassification?.displayName || food.foodClassification?.foodName || "Unknown";
}

export function getFoodImageUrl(food) {
  return food.foodImage?.dataUrl || food.foodImage?.url || "";
}

export function expirationTone(food) {
  const value = food.expirationDate;
  if (!value) return "neutral";

  const target = new Date(`${value}T00:00:00`);
  if (Number.isNaN(target.getTime())) return "neutral";

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.ceil((target.getTime() - today.getTime()) / 86400000);

  if (days < 0) return "critical";
  if (days <= 2) return "warning";
  return "healthy";
}
