import { nova } from "nova-sdk";
import { useCockpitState } from "../state/store";
import { Panel } from "../components/Panel";
import styles from "./DiffInspector.module.css";

export function DiffInspector() {
  const diff = useCockpitState((s) => s.workspace.selectedDiff);

  async function applyPatch() {
    if (!diff) return;
    try {
      await nova.applyPatch({ diff: diff.text, reason: "User applied patch from cockpit" });
    } catch (err) {
      console.error(err);
    }
  }

  if (!diff) {
    return (
      <Panel title="Diff Inspector">
        <div className={styles.empty}>No diff selected — generate code or refactor to inspect.</div>
      </Panel>
    );
  }

  return (
    <Panel title="Diff Inspector">
      <div className={styles.columns}>
        <div className={styles.col}>— before —</div>
        <div className={styles.col}>{diff.text}</div>
      </div>
      <div className={styles.meta}>
        <div>Action: {diff.metadata.action}</div>
        <div>Invariants: [{diff.metadata.invariantsChecked.join(", ")}]</div>
        <div>Continuity Hash: {diff.metadata.continuityHash}</div>
        <div>Receipt: {diff.metadata.receiptId ?? "—"}</div>
      </div>
      <div className={styles.actions}>
        <button type="button" className={styles.btnPrimary} onClick={() => void applyPatch()}>
          Apply Patch
        </button>
      </div>
    </Panel>
  );
}
