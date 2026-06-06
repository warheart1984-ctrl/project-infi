import React from 'react';
import { Link } from 'react-router-dom';

export function LedgerDigestCompact({ ledgerDigest }) {
  const block = ledgerDigest || {};
  const digest = block.digest || {};

  return (
    <section className="workbench-section page-panel" data-testid="infinity1-ledger-digest">
      <div className="workbench-section-head">
        <div>
          <span>Accountability</span>
          <h2>Decision ledger</h2>
        </div>
        <Link to="/operator/ledger" className="workbench-button ghost">
          Open ledger
        </Link>
      </div>
      <p className="workbench-muted">
        scope {digest.scope_id || 'global'} · entries {digest.entry_count ?? 0}
      </p>
      <div className="workbench-chip-row">
        <span className={`workbench-chip ${digest.pending_count ? 'warning' : 'aligned'}`}>
          pending={digest.pending_count ?? 0}
        </span>
        <span className="workbench-chip aligned">review={digest.needs_review_count ?? 0}</span>
        <span className="workbench-chip aligned">federation={digest.cross_tenant_decisions_count ?? 0}</span>
      </div>
    </section>
  );
}
