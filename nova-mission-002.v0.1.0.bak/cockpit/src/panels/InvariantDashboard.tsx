import { useCockpitState } from "../state/store";
import { Panel } from "../components/Panel";
import styles from "./InvariantDashboard.module.css";

export function InvariantDashboard() {
  const invariants = useCockpitState((s) => s.governance.invariants);
  const violations = useCockpitState((s) => s.governance.violations);

  return (
    <Panel title="Invariant Dashboard">
      <div>ACTIVE ({invariants.length})</div>
      <ul className={styles.list}>
        {invariants.map((inv) => (
          <li key={inv.id} className={styles.item}>
            <span className={inv.severity === "error" ? styles.badgeE : styles.badgeW}>
              [{inv.severity === "error" ? "E" : "W"}]
            </span>
            <span>{inv.id}</span>
          </li>
        ))}
      </ul>
      <div className={styles.violations}>
        <strong>Recent Violations</strong>
        {violations.length === 0 ? (
          <div>None</div>
        ) : (
          violations.slice(0, 8).map((v) => (
            <div key={v.id} className={styles.violationRow}>
              [{new Date().toLocaleTimeString()}] {v.invariantId}
            </div>
          ))
        )}
      </div>
    </Panel>
  );
}
