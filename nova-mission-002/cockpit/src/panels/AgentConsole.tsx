import { useState } from "react";
import { nova, runtime } from "nova-sdk";
import { useCockpitState } from "../state/store";
import styles from "./AgentConsole.module.css";

export function AgentConsole() {
  const goal = useCockpitState((s) => s.agent.currentGoal);
  const plan = useCockpitState((s) => s.agent.currentPlan);
  const log = useCockpitState((s) => s.agent.log);
  const setGoal = useCockpitState((s) => s.actions.setGoal);
  const setCenterMode = useCockpitState((s) => s.actions.setCenterMode);
  const [busy, setBusy] = useState(false);

  async function handleGeneratePlan() {
    const input = prompt("Enter goal:", goal ?? "");
    if (!input) return;
    setGoal(input);
    setBusy(true);
    try {
      const context = await runtime.getContext();
      await nova.plan({ goal: input, context });
      setCenterMode("plan");
    } catch (err) {
      console.error(err);
    } finally {
      setBusy(false);
    }
  }

  async function handleGenerateCode() {
    const promptText = prompt("Generate code for:", goal ?? "utility function");
    if (!promptText) return;
    setBusy(true);
    try {
      const result = await nova.generateCode({ prompt: promptText });
      useCockpitState.getState().actions.selectDiff({
        text: result.code,
        metadata: {
          action: "generate",
          invariantsChecked: result.receipts[0]?.invariantsChecked ?? [],
          continuityHash: result.receipts[0]?.continuityHash ?? "",
          receiptId: result.receipts[0]?.id,
        },
      });
    } catch (err) {
      console.error(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={styles.console}>
      <header className={styles.header}>
        <h2 className={styles.title}>Agent Console</h2>
        <div className={styles.goal}>{goal ?? "No active goal"}</div>
      </header>
      <div className={styles.actions}>
        <button type="button" className={styles.btn} disabled={busy} onClick={handleGeneratePlan}>
          Generate Plan
        </button>
        <button type="button" className={styles.btn} disabled={busy} onClick={handleGenerateCode}>
          Generate Code
        </button>
      </div>
      {plan ? (
        <ul className={styles.planSteps}>
          {plan.steps.map((s: { id: string; description: string }) => (
            <li key={s.id}>{s.description}</li>
          ))}
        </ul>
      ) : null}
      <div className={styles.log}>
        {log.map((e) => (
          <div
            key={e.id}
            className={e.type === "violation" ? styles.logLineViolation : styles.logLine}
          >
            [{new Date(e.timestamp).toLocaleTimeString()}] {e.message}
          </div>
        ))}
      </div>
    </section>
  );
}
