import { useCockpitState } from "../state/store";
import { Panel } from "../components/Panel";
import styles from "./ReceiptViewer.module.css";

export function ReceiptViewer() {
  const receipts = useCockpitState((s) => s.governance.receipts);
  const selectedId = useCockpitState((s) => s.governance.selectedReceiptId);
  const selectReceipt = useCockpitState((s) => s.actions.selectReceipt);

  const selected = receipts.find((r) => r.id === selectedId);

  return (
    <Panel title="Receipt Viewer">
      <table className={styles.table}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Action</th>
            <th>Invariants</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {receipts.map((r) => (
            <tr
              key={r.id}
              className={r.id === selectedId ? styles.rowSelected : ""}
              onClick={() => selectReceipt(r.id)}
            >
              <td>{r.id.slice(0, 12)}…</td>
              <td>{r.action.type}</td>
              <td>{r.invariantsChecked.length}</td>
              <td>{new Date(r.timestamp).toLocaleTimeString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {selected ? (
        <pre className={styles.detail}>{JSON.stringify(selected, null, 2)}</pre>
      ) : null}
    </Panel>
  );
}
