import { continuity } from "nova-sdk";
import { useCockpitState } from "../state/store";
import { Panel } from "../components/Panel";
import styles from "./ContinuityTimeline.module.css";

export function ContinuityTimeline() {
  const timeline = useCockpitState((s) => s.continuity.timeline);
  const selectedId = useCockpitState((s) => s.continuity.selectedSnapshotId);
  const selectSnapshot = useCockpitState((s) => s.actions.selectSnapshot);

  const selected = timeline.find((n) => n.id === selectedId);

  async function handleReplay(id: string) {
    selectSnapshot(id);
    const replay = await continuity.replay(id);
    console.log("Replay result:", replay);
  }

  return (
    <Panel title="Continuity Timeline">
      <div className={styles.track}>
        {timeline.map((node, i) => (
          <span key={node.id} style={{ display: "contents" }}>
            {i > 0 ? <span className={styles.connector} /> : null}
            <button
              type="button"
              title={node.label ?? node.type}
              className={`${styles.node} ${
                node.type === "snapshot"
                  ? styles.nodeSnapshot
                  : node.type === "receipt"
                  ? styles.nodeReceipt
                  : styles.nodeViolation
              } ${node.id === selectedId ? styles.nodeSelected : ""}`}
              onClick={() => void handleReplay(node.id)}
            />
          </span>
        ))}
      </div>
      {selected ? (
        <div className={styles.detail}>
          <div>ID: {selected.id}</div>
          <div>Type: {selected.type}</div>
          <div>Time: {new Date(selected.timestamp).toLocaleString()}</div>
          <div>State Hash: {selected.stateHash}</div>
          <button type="button" className={styles.btn} onClick={() => void handleReplay(selected.id)}>
            Replay
          </button>
        </div>
      ) : (
        <div>Select a timeline node</div>
      )}
    </Panel>
  );
}
