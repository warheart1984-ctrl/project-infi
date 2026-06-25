import { useClusterStore } from "../state/clusterStore";

export function AgentSelector() {
  const agents = useClusterStore((s) => s.agents);
  const selected = useClusterStore((s) => s.selectedAgent);
  const selectAgent = useClusterStore((s) => s.actions.selectAgent);

  return (
    <div style={{ padding: 12 }}>
      <h3 style={{ margin: "0 0 8px", fontSize: 13 }}>Agents</h3>
      {Object.values(agents).map((agent) => (
        <button
          key={agent.id}
          type="button"
          onClick={() => selectAgent(agent.id)}
          style={{
            display: "block",
            width: "100%",
            marginBottom: 6,
            padding: "8px 10px",
            textAlign: "left",
            background: selected === agent.id ? "var(--nova-accent-dim)" : "transparent",
            border: "1px solid var(--nova-border)",
            borderRadius: 4,
            color: "var(--nova-text)",
            cursor: "pointer",
          }}
        >
          {agent.id}
          <span style={{ float: "right", opacity: 0.7 }}>{agent.status}</span>
        </button>
      ))}
    </div>
  );
}
