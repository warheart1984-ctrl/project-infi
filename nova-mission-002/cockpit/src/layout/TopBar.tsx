import styles from "./TopBar.module.css";
import { useCockpitState } from "../state/store";
import { useKernelStore } from "../state/kernelStore";

export function TopBar() {
  const kernelStatus = useCockpitState((s) => s.kernel.status);
  const invariants = useCockpitState((s) => s.governance.invariants);
  const kernelVersion = useKernelStore((s) => s.kernelVersion);
  const pitBand = useKernelStore((s) => s.pitBand);

  const nominal =
    kernelStatus.invariantEngine === "ok" &&
    kernelStatus.ledger === "ok" &&
    kernelStatus.continuity === "ok";

  return (
    <header className={styles.topBar}>
      <div className={styles.left}>
        <div className={styles.brand}>Nova</div>
        <div className={styles.sub}>Constitutional Coding Agent</div>
      </div>
      <div className={styles.center}>
        <span className={styles.kernelLabel}>{kernelVersion} · PIT-{pitBand}</span>
        <span className={nominal ? styles.kernelStatusOk : styles.kernelStatusWarn}>
          {nominal ? "All systems nominal" : "Attention required"}
        </span>
      </div>
      <div className={styles.right}>
        <span className={styles.invariantsCount}>
          {invariants.length} invariants active
        </span>
      </div>
    </header>
  );
}
