import { useClusterStore } from "../state/clusterStore";

export function ClusterTimeline() {
  const events = useClusterStore((s) => s.clusterEvents);
  const replayWindow = useClusterStore((s) => s.replayWindow);
  const setReplayWindow = useClusterStore((s) => s.actions.setReplayWindow);

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "center" }}>
        <strong style={{ fontSize: 13 }}>Cluster Timeline</strong>
        <button
          type="button"
          onClick={() => setReplayWindow({ from: "s1", to: "s2" })}
          style={{ fontSize: 11, marginLeft: "auto" }}
        >
          Replay window
        </button>
        {replayWindow && (
          <span style={{ fontSize: 11, opacity: 0.7 }}>
            {replayWindow.from} → {replayWindow.to}
          </span>
        )}
      </div>
      <div style={{ display: "flex", gap: 8, overflowX: "auto" }}>
        {events.length === 0 && (
          <span style={{ fontSize: 12, opacity: 0.6 }}>No cluster events yet</span>
        )}
        {events.slice(0, 12).map((e) => (
          <span
            key={e.id}
            style={{
              fontSize: 11,
              padding: "4px 8px",
              border: "1px solid var(--nova-border)",
              borderRadius: 4,
              whiteSpace: "nowrap",
            }}
          >
            {e.type} {e.agentId ?? ""}
          </span>
        ))}
      </div>
    </div>
  );
}
