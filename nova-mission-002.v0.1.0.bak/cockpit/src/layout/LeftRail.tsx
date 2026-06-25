import styles from "./LeftRail.module.css";
import { useCockpitState } from "../state/store";
import { AgentConsole } from "../panels/AgentConsole";
import type { CenterMode } from "../types";

const modes: { id: CenterMode; label: string }[] = [
  { id: "plan", label: "Plan" },
  { id: "diff", label: "Diff" },
  { id: "receipts", label: "Receipts" },
  { id: "continuity", label: "Continuity" },
  { id: "invariants", label: "Invariants" },
  { id: "kernel", label: "Kernel" },
  { id: "flight-deck", label: "Flight Deck" },
  { id: "ledger-compare", label: "Ledger Compare" },
  { id: "continuity-matrix", label: "Continuity Matrix" },
  { id: "drift", label: "Drift Map" },
];

export function LeftRail() {
  const centerMode = useCockpitState((s) => s.ui.centerMode);
  const setCenterMode = useCockpitState((s) => s.actions.setCenterMode);

  return (
    <aside className={styles.leftRail}>
      <nav className={styles.nav}>
        {modes.map((m) => (
          <button
            key={m.id}
            type="button"
            className={centerMode === m.id ? styles.navItemActive : styles.navItem}
            onClick={() => setCenterMode(m.id)}
          >
            {m.label}
          </button>
        ))}
      </nav>
      <div className={styles.consoleWrapper}>
        <AgentConsole />
      </div>
    </aside>
  );
}
