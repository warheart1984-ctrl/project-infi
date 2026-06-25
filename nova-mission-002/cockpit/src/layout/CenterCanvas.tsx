import styles from "./CenterCanvas.module.css";
import { useCockpitStore } from "../state/cockpitStore";
import { PlanVisualizer } from "../panels/PlanVisualizer";
import { DiffInspector } from "../panels/DiffInspector";
import { ReceiptViewer } from "../panels/ReceiptViewer";
import { ContinuityTimeline } from "../panels/ContinuityTimeline";
import { InvariantDashboard } from "../panels/InvariantDashboard";
import { KernelMonitor } from "../panels/KernelMonitor";
import { FlightDeck } from "../flight-deck/FlightDeck";
import { LedgerCompare } from "../flight-deck/LedgerCompare";
import { ContinuityMatrix } from "../flight-deck/ContinuityMatrix";
import { DriftVisualizer } from "../drift/DriftVisualizer";
import type { CenterMode } from "../types";

export function CenterCanvas() {
  const mode = useCockpitStore((s) => s.ui.centerMode);
  const selectedAgents = useCockpitStore((s) => s.ui.selectedAgents);
  const lastPlanId = useCockpitStore((s) => s.uiSignals.lastPlanId);

  const content = (() => {
    switch (mode as CenterMode) {
      case "plan":
        return <PlanVisualizer />;
      case "diff":
        return <DiffInspector />;
      case "receipts":
        return <ReceiptViewer />;
      case "continuity":
        return <ContinuityTimeline />;
      case "invariants":
        return <InvariantDashboard />;
      case "kernel":
        return <KernelMonitor />;
      case "flight-deck":
        return <FlightDeck />;
      case "ledger-compare":
        return (
          <LedgerCompare
            leftAgentId={selectedAgents[0]}
            rightAgentId={selectedAgents[1]}
          />
        );
      case "continuity-matrix":
        return <ContinuityMatrix />;
      case "drift":
        return <DriftVisualizer />;
      default:
        return <PlanVisualizer />;
    }
  })();

  return (
    <main className={`${styles.centerCanvas} ${lastPlanId && mode === "plan" ? styles.fadeIn : ""}`}>
      {content}
    </main>
  );
}
