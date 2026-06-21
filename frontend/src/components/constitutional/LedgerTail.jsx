import React from 'react';

export function LedgerTail({ title, entries = [] }) {
  return (
    <div className="constitutional-panel">
      <h3>{title}</h3>
      {entries.length === 0 ? (
        <p className="constitutional-muted">No entries yet.</p>
      ) : (
        <ul className="constitutional-muted">
          {entries.slice(-6).map((entry) => (
            <li key={entry.entry_id}>
              {entry.entry_type} · {entry.law_id || entry.evidence_id || entry.object_id} · epoch {entry.epoch}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
