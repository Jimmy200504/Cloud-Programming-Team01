import { Droplets, RefreshCw, Thermometer, Timer, UnlockKeyhole } from "lucide-react";
import { formatDateTime } from "../utils/format";
import StatusBadge from "./StatusBadge";

export default function DeviceStatePanel({ deviceState, loading, message, onRefresh }) {
  const temperature = formatMetric(deviceState?.temperature, "°C");
  const humidity = formatMetric(deviceState?.humidity, "%");

  return (
    <section className="panel device-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Environment</p>
          <h2>Device Climate</h2>
        </div>
        <div className="heading-actions">
          <StatusBadge tone={loading ? "busy" : message ? "warning" : "ready"}>{loading ? "Syncing" : "Live"}</StatusBadge>
          <button className="icon-button" type="button" onClick={onRefresh} disabled={loading} aria-label="Refresh device state">
            <RefreshCw size={18} className={loading ? "spin" : ""} />
          </button>
        </div>
      </div>

      {message ? (
        <div className="empty-state compact-empty">
          <Thermometer size={22} />
          <span>{message}</span>
        </div>
      ) : (
        <div className="metric-grid">
          <MetricCard icon={Thermometer} label="Temperature" value={temperature} />
          <MetricCard icon={Droplets} label="Humidity" value={humidity} />
          <MetricCard icon={UnlockKeyhole} label="Lock" value={deviceState?.lock || "unknown"} />
          <MetricCard icon={Timer} label="Last sync" value={formatDateTime(deviceState?.lastSeenAt)} />
        </div>
      )}
    </section>
  );
}

function MetricCard({ icon: Icon, label, value }) {
  return (
    <article className="metric-card">
      <Icon size={20} />
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </article>
  );
}

function formatMetric(value, suffix) {
  if (value === null || value === undefined || value === "") return "unknown";
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) return String(value);
  return `${numberValue.toFixed(numberValue % 1 === 0 ? 0 : 1)}${suffix}`;
}
