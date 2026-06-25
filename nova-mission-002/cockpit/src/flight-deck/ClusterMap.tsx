import { useClusterStore } from "../state/clusterStore";

export function ClusterMap() {
  const agents = useClusterStore((s) => s.agents);

  return (
    <div style={{ padding: 16, display: "flex", flexWrap: "wrap", gap: 12 }}>
      {Object.entries(agents).map(([id, agent]) => (
        <div
          key={id}
          className={`node status-${agent.status}`}
          style={{
            minWidth: 120,
            padding: 16,
            borderRadius: 8,
            border: "1px solid var(--nova-border)",
            background:
              agent.status === "drift"
                ? "rgba(242, 201, 76, 0.15)"
                : agent.status === "error"
                  ? "rgba(235, 87, 87, 0.15)"
                  : "rgba(39, 174, 96, 0.1)",
          }}
        >
          <strong>{id}</strong>
          <div style={{ fontSize: 12, opacity: 0.8 }}>{agent.kernelStatus ?? agent.status}</div>
        </div>
      ))}
    </div>
  );
}
