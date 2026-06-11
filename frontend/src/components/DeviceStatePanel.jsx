import { Droplets, LockKeyhole, RefreshCw, Thermometer, Timer, UnlockKeyhole } from "lucide-react";
import { formatDateTime } from "../utils/format";
import StatusBadge from "./StatusBadge";

export default function DeviceStatePanel({ deviceState, loading, lockCommand, lockUpdating, message, onRefresh, onSetLock }) {
  const temperature = formatMetric(deviceState?.temperature, "°C");
  const humidity = formatMetric(deviceState?.humidity, "%");
  const currentLock = deviceState?.lock || "unknown";

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
          <MetricCard icon={currentLock === "unlocked" ? UnlockKeyhole : LockKeyhole} label="Lock" value={currentLock} />
          <MetricCard icon={Timer} label="Last sync" value={formatDateTime(deviceState?.lastSeenAt)} />
        </div>
      )}

      {!message && (
        <div className="lock-control">
          <button
            className={currentLock === "locked" ? "lock-action active" : "lock-action"}
            type="button"
            disabled={loading || lockUpdating}
            onClick={() => onSetLock("locked")}
          >
            <LockKeyhole size={18} />
            Locked
          </button>
          <button
            className={currentLock === "unlocked" ? "lock-action active" : "lock-action"}
            type="button"
            disabled={loading || lockUpdating}
            onClick={() => onSetLock("unlocked")}
          >
            <UnlockKeyhole size={18} />
            Unlocked
          </button>
        </div>
      )}

      {lockCommand && !message && (
        <p className="lock-command-note">
          Command sent: {lockCommand}. Refresh after the device reports the new shadow state.
        </p>
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
