import styles from "./BottomBand.module.css";
import { useCockpitState } from "../state/store";

export function BottomBand() {
  const log = useCockpitState((s) => s.agent.log);
  const receipts = useCockpitState((s) => s.governance.receipts);
  const lastReceiptId = useCockpitState((s) => s.uiSignals.lastReceiptId);
  const selectReceipt = useCockpitState((s) => s.actions.selectReceipt);

  return (
    <footer className={styles.bottomBand}>
      <div className={styles.block}>
        <span className={styles.label}>Agent Cycle</span>
        <span className={styles.value}>{log.length} steps this session</span>
      </div>
      <div
        className={`${styles.block} ${lastReceiptId ? styles.pulseReceipt : ""}`}
      >
        <span className={styles.label}>Receipts</span>
        <span className={styles.value}>{receipts.length}</span>
      </div>
      <div className={styles.recent}>
        {receipts.slice(0, 5).map((r) => (
          <button
            key={r.id}
            type="button"
            className={styles.chip}
            onClick={() => selectReceipt(r.id)}
          >
            {r.id.slice(0, 8)}
          </button>
        ))}
      </div>
    </footer>
  );
}
