import { useClusterStore } from "../state/clusterStore";

export function ContinuityMatrix() {
  const agents = useClusterStore((s) => s.agents);

  return (
    <table className="continuity-matrix" style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
      <tbody>
        {Object.entries(agents).map(([id, agent]) => (
          <tr key={id}>
            <td style={{ padding: 4, borderBottom: "1px solid var(--nova-border)" }}>{id}</td>
            {agent.snapshots.map((s) => (
              <td
                key={s.id}
                className={`cell ${s.state}`}
                style={{
                  padding: 4,
                  borderBottom: "1px solid var(--nova-border)",
                  color:
                    s.state === "drift"
                      ? "#f2c94c"
                      : s.state === "error"
                        ? "#eb5757"
                        : "#27ae60",
                }}
              >
                {s.id}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
