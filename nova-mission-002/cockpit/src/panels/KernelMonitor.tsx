import { useCockpitState } from "../state/store";
import { Panel } from "../components/Panel";
import styles from "./KernelMonitor.module.css";

function StatusCard({
  label,
  value,
  status,
}: {
  label: string;
  value: string | number;
  status?: string;
}) {
  const cls =
    status === "ok" ? styles.ok : status === "warn" ? styles.warn : status === "error" ? styles.error : "";
  return (
    <div className={styles.card}>
      <div className={styles.cardLabel}>{label}</div>
      <div className={`${styles.cardValue} ${cls}`}>{value}</div>
    </div>
  );
}

export function KernelMonitor() {
  const status = useCockpitState((s) => s.kernel.status);

  const nominal =
    status.invariantEngine === "ok" &&
    status.ledger === "ok" &&
    status.continuity === "ok";

  return (
    <Panel title="CRK‑1 Kernel Monitor">
      <div className={styles.grid}>
        <StatusCard
          label="Invariant Engine"
          value={`${status.activeInvariants} active`}
          status={status.invariantEngine}
        />
        <StatusCard label="Pattern Ledger" value={`${status.receiptCount} receipts`} status={status.ledger} />
        <StatusCard
          label="Continuity Substrate"
          value={`${status.snapshotCount} snapshots`}
          status={status.continuity}
        />
        <StatusCard label="Violations (1m)" value={status.violationsLastMinute} />
      </div>
      <div className={styles.summary}>
        Replay Consistency: {nominal ? "PASS" : "CHECK"}
        <br />
        Kernel heartbeat: every 2s
      </div>
    </Panel>
  );
}
