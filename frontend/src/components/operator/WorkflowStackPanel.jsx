import React from 'react';

export function WorkflowStackPanel({ workflowStack }) {
  const stack = workflowStack || {};
  const gates = stack.gates || [];

  return (
    <section className="workbench-section page-panel" data-testid="infinity1-workflow-stack">
      <div className="workbench-section-head">
        <div>
          <span>Infinity 1</span>
          <h2>Workflow stack</h2>
        </div>
        <span className={`workbench-chip ${stack.claim_label === 'proven' ? 'aligned' : 'warning'}`}>
          {stack.claim_label || 'asserted'}
        </span>
      </div>
      <p className="workbench-muted">{stack.verification_command || 'make operator-workflow-stack-gate'}</p>
      <div className="workbench-chip-row">
        {gates.map((gate) => (
          <span key={gate.id} className="workbench-chip aligned" title={gate.id}>
            {gate.label}
          </span>
        ))}
      </div>
    </section>
  );
}
