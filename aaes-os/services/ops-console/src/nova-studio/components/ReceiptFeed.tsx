import type { SkillzMcgeeReceipt } from '../state/studioState.js';

export function ReceiptFeed({ receipts }: { receipts: SkillzMcgeeReceipt[] }) {
  return (
    <table>
      <thead><tr><th>Receipt</th><th>Slice</th><th>Actor</th><th>Status</th></tr></thead>
      <tbody>
        {receipts.map((receipt) => (
          <tr key={receipt.id}>
            <td>{receipt.id}</td>
            <td>{receipt.slice}</td>
            <td>{receipt.actor}</td>
            <td>{receipt.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
