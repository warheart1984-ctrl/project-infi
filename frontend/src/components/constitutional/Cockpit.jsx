import React from 'react';
import { ComprehensionHealth } from './ComprehensionHealth';
import { EvidenceFitnessHealth } from './EvidenceFitnessHealth';
import { MeaningHealth } from './MeaningHealth';
import { LedgerTail } from './LedgerTail';

export function Cockpit({
  summary,
  epochPulse,
  busy,
  stewardMode,
  onRunEpoch,
  onToggleSteward,
}) {
  const health = summary?.comprehension_health;
  const spineBlocked = summary?.spine_commit_blocked;
  const blockReasons = summary?.spine_block_reasons || [];

  return (
    <div className="constitutional-grid">
      <div className="constitutional-panel">
        <h2>Constitutional Cockpit</h2>
        <p className="constitutional-muted">
          Governance substrate — Law, Evidence, Comprehension, Meaning, and EIT-2 fitness.
        </p>
        <div className={`cockpit-epoch ${epochPulse ? 'epoch-updated' : ''}`}>
          Epoch {summary?.epoch ?? '—'} · Laws {summary?.law_count ?? 0} · avg F=
          {Number(summary?.avg_fitness || 0).toFixed(3)}
        </div>
        {spineBlocked ? (
          <p className="constitutional-warning">
            Epoch blocked: {(blockReasons.length ? blockReasons : ['SPINE-BLOCK']).join(', ')}
          </p>
        ) : null}
        <div className="constitutional-actions">
          <button
            type="button"
            className="constitutional-btn constitutional-btn-primary"
            disabled={busy || spineBlocked || health?.epoch_commit_blocked}
            onClick={onRunEpoch}
          >
            {busy ? 'Running…' : 'Run Epoch Simulation'}
          </button>
          <button type="button" className="constitutional-btn constitutional-btn-secondary" onClick={onToggleSteward}>
            {stewardMode ? 'Exit Steward Mode' : 'Steward Mode'}
          </button>
        </div>
      </div>

      <ComprehensionHealth health={health} />
      <MeaningHealth health={summary?.meaning_health} />
      <EvidenceFitnessHealth health={summary?.evidence_fitness_health} />

      <LedgerTail title="Law Ledger Tail" entries={summary?.law_ledger_tail || []} />
      <LedgerTail title="Evidence Ledger Tail" entries={summary?.evidence_ledger_tail || []} />
    </div>
  );
}
