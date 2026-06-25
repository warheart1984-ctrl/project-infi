import type { Plan } from "../types";
import { useCockpitState } from "../state/store";
import { Panel } from "../components/Panel";
import styles from "./PlanVisualizer.module.css";

export function PlanVisualizer() {
  const plan = useCockpitState((s) => s.agent.currentPlan);

  if (!plan) {
    return (
      <Panel title="Plan Visualizer">
        <div className={styles.empty}>No plan yet — use Agent Console to generate one.</div>
      </Panel>
    );
  }

  return (
    <Panel title="Plan Visualizer">
      <div className={styles.graph}>
          {plan.steps.map((step: Plan["steps"][number], i: number) => (
          <span key={step.id} style={{ display: "contents" }}>
            {i > 0 ? <span className={styles.arrow}>→</span> : null}
            <div className={styles.step}>{step.description}</div>
          </span>
        ))}
      </div>
      <div className={styles.justification}>{plan.justification}</div>
    </Panel>
  );
}
