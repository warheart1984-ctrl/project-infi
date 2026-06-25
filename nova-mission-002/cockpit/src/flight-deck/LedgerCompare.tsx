import { useClusterStore } from "../state/clusterStore";

interface LedgerCompareProps {
  leftAgentId?: string;
  rightAgentId?: string;
}

export function LedgerCompare({ leftAgentId, rightAgentId }: LedgerCompareProps) {
  const agents = useClusterStore((s) => s.agents);
  const left = leftAgentId ? agents[leftAgentId] : undefined;
  const right = rightAgentId ? agents[rightAgentId] : undefined;

  return (
    <div
      className="ledger-compare"
      style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, padding: 16, height: "100%" }}
    >
      <div>
        <h3 style={{ fontSize: 13, margin: "0 0 8px" }}>{leftAgentId ?? "—"}</h3>
        <pre style={{ fontSize: 11, overflow: "auto" }}>
          {JSON.stringify(left?.receipts ?? [], null, 2)}
        </pre>
      </div>
      <div>
        <h3 style={{ fontSize: 13, margin: "0 0 8px" }}>{rightAgentId ?? "—"}</h3>
        <pre style={{ fontSize: 11, overflow: "auto" }}>
          {JSON.stringify(right?.receipts ?? [], null, 2)}
        </pre>
      </div>
    </div>
  );
}
