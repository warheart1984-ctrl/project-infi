import { useKernelStore } from "../state/kernelStore";
import { useCockpitState } from "../state/store";

export function KernelStatusRail() {
  const kernel = useKernelStore((s) => s);
  const status = useCockpitState((s) => s.kernel.status);

  const rows = [
    ["Kernel", kernel.kernelVersion],
    ["PIT Band", String(kernel.pitBand)],
    ["Invariant Engine", status.invariantEngine],
    ["Ledger", status.ledger],
    ["Continuity", status.continuity],
    ["Receipts", String(status.receiptCount)],
    ["Snapshots", String(status.snapshotCount)],
  ];

  return (
    <div style={{ padding: 12, fontSize: 13 }}>
      <h3 style={{ margin: "0 0 8px" }}>Kernel Status</h3>
      {rows.map(([label, value]) => (
        <div key={label} style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ opacity: 0.75 }}>{label}</span>
          <span>{value}</span>
        </div>
      ))}
    </div>
  );
}
