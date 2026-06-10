export function formatDate(value) {
  if (!value) return "unknown";
  return String(value).slice(0, 10);
}

export function formatDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value || "unknown";

  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

export function daysUntil(dateValue) {
  if (!dateValue) return null;
  const target = new Date(`${dateValue}T00:00:00`);
  if (Number.isNaN(target.getTime())) return null;

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return Math.ceil((target.getTime() - today.getTime()) / 86400000);
}

export function defaultExpirationDate(days = 7) {
  return new Date(Date.now() + days * 86400000).toISOString().slice(0, 10);
}
