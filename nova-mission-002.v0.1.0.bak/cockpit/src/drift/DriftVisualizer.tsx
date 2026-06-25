import { useDriftStore } from "../state/driftStore";
import "./driftVisualizer.css";

export function DriftVisualizer() {
  const agents = useDriftStore((s) => s.agents);
  const divergences = useDriftStore((s) => s.divergences);

  return (
    <div className="drift-visualizer">
      <div className="drift-header">Constitutional Drift Map</div>
      <div className="drift-grid">
        {agents.map((agent) => (
          <div key={agent.id} className="drift-agent-column">
            <div className="agent-label">{agent.id}</div>
            {agent.snapshots.map((s) => (
              <div
                key={s.id}
                className={`drift-cell state-${s.state}`}
                title={`${agent.id} @ ${s.id}`}
              />
            ))}
          </div>
        ))}
      </div>
      <div className="drift-footer">
        {divergences.map((d) => (
          <div key={d.id} className="drift-event">
            {d.type} at {d.snapshotId ?? "—"} between {d.agents.join(", ")}
          </div>
        ))}
        {divergences.length === 0 && (
          <span style={{ opacity: 0.6 }}>No divergences detected</span>
        )}
      </div>
    </div>
  );
}
