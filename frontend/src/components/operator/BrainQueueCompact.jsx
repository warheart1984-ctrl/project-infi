import React from 'react';
import { Link } from 'react-router-dom';

export function BrainQueueCompact({ brain }) {
  const data = brain || {};

  return (
    <section className="workbench-section page-panel" data-testid="infinity1-brain-queue">
      <div className="workbench-section-head">
        <div>
          <span>Nova Cortex</span>
          <h2>Brain queue</h2>
        </div>
        <Link to="/operator/brain" className="workbench-button ghost">
          Sessions
        </Link>
      </div>
      <p className="workbench-muted">
        {data.session_count ?? 0} sessions · {data.pending_decisions ?? 0} awaiting decide
      </p>
      <div className="workbench-chip-row">
        <span className="workbench-chip aligned">status={data.claim_label || 'proposal_only'}</span>
        <span className={`workbench-chip ${data.open_sessions ? 'warning' : 'aligned'}`}>
          open={data.open_sessions ?? 0}
        </span>
      </div>
      {data.latest_session_id ? (
        <small className="workbench-muted">
          latest {data.latest_session_id} · decision {data.latest_decision || 'pending'}
        </small>
      ) : null}
    </section>
  );
}
