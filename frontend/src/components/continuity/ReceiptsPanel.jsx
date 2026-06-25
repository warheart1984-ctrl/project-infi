import React from 'react';
import { FiCheckCircle } from 'react-icons/fi';

export default function ReceiptsPanel({
  selectedEventId,
  receipts,
  receiptStatus,
  receiptDetails,
  onReceiptStatusChange,
  onReceiptDetailsChange,
  onIssueReceipt,
  busyAction,
}) {
  return (
    <section className="nova-coding-agent__panel">
      <div className="nova-coding-agent__panel-header">
        <h2>Receipts</h2>
        <span>{selectedEventId || 'unanchored'}</span>
      </div>
      <div className="nova-coding-agent__receipt-controls">
        <label className="nova-coding-agent__field">
          <span>Status</span>
          <select value={receiptStatus} onChange={(event) => onReceiptStatusChange(event.target.value)}>
            <option value="PASS">PASS</option>
            <option value="FAIL">FAIL</option>
          </select>
        </label>
        <label className="nova-coding-agent__field">
          <span>Receipt details</span>
          <textarea value={receiptDetails} onChange={(event) => onReceiptDetailsChange(event.target.value)} />
        </label>
        <button type="button" onClick={onIssueReceipt} disabled={!selectedEventId || busyAction === 'receipt'}>
          <FiCheckCircle aria-hidden="true" />
          <span>{busyAction === 'receipt' ? 'Issuing...' : 'Issue receipt'}</span>
        </button>
      </div>
      <div className="nova-coding-agent__receipts">
        {receipts.length ? receipts.map((receipt) => (
          <article key={receipt.id} className="nova-coding-agent__receipt">
            <strong>{receipt.status}</strong>
            <p>{receipt.details || 'No receipt details recorded.'}</p>
          </article>
        )) : (
          <p className="nova-coding-agent__empty">No receipts for the selected event.</p>
        )}
      </div>
    </section>
  );
}
