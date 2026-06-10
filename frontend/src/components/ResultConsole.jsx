import { Terminal, Trash2 } from "lucide-react";

export default function ResultConsole({ value, onClear }) {
  return (
    <section className="console-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Telemetry</p>
          <h2>API Result</h2>
        </div>
        <button className="icon-button" type="button" onClick={onClear} aria-label="Clear result">
          <Trash2 size={18} />
        </button>
      </div>
      <div className="console-window">
        <div className="console-title">
          <Terminal size={16} />
          latest-response.json
        </div>
        <pre>{JSON.stringify(value, null, 2)}</pre>
      </div>
    </section>
  );
}
