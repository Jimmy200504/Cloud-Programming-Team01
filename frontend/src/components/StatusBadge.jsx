import { CheckCircle2, CircleAlert, Loader2, XCircle } from "lucide-react";

const icons = {
  ready: CheckCircle2,
  busy: Loader2,
  warning: CircleAlert,
  error: XCircle,
  success: CheckCircle2
};

export default function StatusBadge({ tone = "ready", children }) {
  const Icon = icons[tone] || CheckCircle2;

  return (
    <span className={`status-badge ${tone}`}>
      <Icon size={15} className={tone === "busy" ? "spin" : ""} />
      {children}
    </span>
  );
}
