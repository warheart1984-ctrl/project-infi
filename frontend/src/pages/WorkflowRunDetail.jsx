import React, { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { apiGet, getApiErrorMessage } from '../lib/api';
import './WorkflowRuns.css';

function statusClasses(status) {
  switch (status) {
    case 'completed':
      return 'connected';
    case 'queued':
      return 'warning';
    case 'running':
      return 'warning';
    case 'recovering':
      return 'warning';
    case 'awaiting_approval':
      return 'warning';
    case 'stale':
      return 'error';
    case 'failed':
      return 'error';
    default:
      return '';
  }
}

function WorkflowRunDetail() {
  const { runId } = useParams();
  const [run, setRun] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const runStatus = run?.status;

  useEffect(() => {
    if (!runId) {
      setRun(null);
      setError('Missing workflow run id.');
      setLoading(false);
      return undefined;
    }

    let mounted = true;

    const refresh = async () => {
      try {
        const response = await apiGet(`/workflows/runs/${runId}`, {
          headers: { 'Cache-Control': 'no-store' },
        });
        if (mounted) {
          setRun(response.data.run || null);
          setError('');
        }
      } catch (err) {
        if (mounted) {
          const statusCode = err?.response?.status;
          setRun(null);
          setError(
            statusCode === 404
              ? 'This workflow run no longer exists.'
              : getApiErrorMessage(err, 'Could not load workflow run.'),
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    refresh();
    const shouldPoll = ['queued', 'running', 'awaiting_approval', 'stale', 'recovering'].includes(runStatus || '');
    if (!shouldPoll) {
      return () => {
        mounted = false;
      };
    }

    const interval = window.setInterval(refresh, 2000);
    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, [runId, runStatus]);

  const output = run?.output || {};
  const plannedSteps = useMemo(
    () => (Array.isArray(output.plannedSteps) ? output.plannedSteps : []),
    [output.plannedSteps],
  );
  const steps = useMemo(
    () => (Array.isArray(output.steps) ? output.steps : []),
    [output.steps],
  );
  const totalSteps = output.totalSteps || plannedSteps.length || 0;
  const currentStep = output.currentStep || 0;
  const isFakeModeRun = useMemo(
    () =>
      steps.some((step) => step?.data?.deliveryMode === 'fake' || step?.data?.mode === 'fake')
      || plannedSteps.some((step) => `${step?.output || ''}`.toLowerCase().includes('simulated'))
      || output?.currentData?.deliveryMode === 'fake'
      || output?.currentData?.mode === 'fake',
    [output?.currentData, plannedSteps, steps],
  );
  const progress = useMemo(() => {
    if (!totalSteps) return 0;
    return Math.max(0, Math.min(100, Math.round((currentStep / totalSteps) * 100)));
  }, [currentStep, totalSteps]);

  if (loading) {
    return <div className="workflow-page"><div className="workflow-card workflow-empty-card">Loading run...</div></div>;
  }

  if (error) {
    return (
      <div className="workflow-page">
        <div className="workflow-card workflow-error-card">
          <p>{error}</p>
          <div className="workflow-page-actions">
            <Link className="workflow-page-link" to="/workflows/runs">
              Back to runs
            </Link>
            <Link className="workflow-page-link" to="/workflows">
              Open builder
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!run) {
    return <div className="workflow-page"><div className="workflow-card workflow-empty-card">Run not found.</div></div>;
  }

  return (
    <div className="workflow-page">
      <div className="workflow-detail-header">
        <div>
          <Link className="workflow-page-link workflow-inline-link" to="/workflows/runs">
            Back to runs
          </Link>
          <div className="page-intro workflow-detail-intro">
            <h1>{run.workflow?.name || 'Workflow Run'}</h1>
            <p>Track progress, approvals, and step output as this run moves through the queue.</p>
          </div>
        </div>
        <span className={`status-pill ${statusClasses(run.status)}`}>{run.status}</span>
      </div>

      <div className="workflow-detail-grid">
        <div className="workflow-detail-main">
          <section className="workflow-card page-panel">
            <h2>Progress</h2>
            <div className="workflow-progress-meta">
              <span>{output.message || 'Waiting for updates...'}</span>
              <span>{currentStep}/{totalSteps || '?'}</span>
            </div>
            <div className="workflow-progress-bar">
              <div className="workflow-progress-fill" style={{ width: `${progress}%` }} />
            </div>
            {output.currentStepLabel ? (
              <p className="workflow-muted-copy">
                Current step: <strong>{output.currentStepLabel}</strong>
              </p>
            ) : null}
            {run.status === 'stale' ? (
              <p className="workflow-muted-copy">
                The worker lease expired. AAIS is waiting to recover this run safely.
              </p>
            ) : null}
            {run.status === 'recovering' ? (
              <p className="workflow-muted-copy">
                Recovery has been queued. Completed steps will be preserved and the next incomplete step will resume.
              </p>
            ) : null}
            {isFakeModeRun ? (
              <p className="workflow-muted-copy">
                Safe fake mode is active for this run. External side effects are being simulated, not sent live.
              </p>
            ) : null}
            {output.error ? <div className="workflow-inline-error">{output.error}</div> : null}
          </section>

          <section className="workflow-card page-panel">
            <h2>Planned Steps</h2>
            {plannedSteps.length === 0 ? (
              <p className="workflow-muted-copy">No planned steps found yet.</p>
            ) : (
              <div className="workflow-step-list">
                {plannedSteps.map((step) => (
                  <article key={step.stepId} className="workflow-step-card">
                    <div className="workflow-step-header">
                      <div>
                        <strong>{step.order}. {step.label}</strong>
                        <div className="workflow-step-type">{step.type}</div>
                      </div>
                      <span className={`status-pill ${statusClasses(step.status)}`}>{step.status}</span>
                    </div>
                    {step.output ? <p>{step.output}</p> : null}
                    {step.error ? <div className="workflow-inline-error">{step.error}</div> : null}
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="workflow-card page-panel">
            <h2>Completed Step Data</h2>
            {steps.length === 0 ? (
              <p className="workflow-muted-copy">No completed step output yet.</p>
            ) : (
              <div className="workflow-step-list">
                {steps.map((step, index) => (
                  <article key={step.stepId || index} className="workflow-step-card">
                    <div className="workflow-step-header">
                      <div>
                        <strong>{index + 1}. {step.label || 'Step'}</strong>
                        <div className="workflow-step-type">{step.type || 'unknown'}</div>
                      </div>
                      <span className={`status-pill ${step.ok ? 'connected' : 'error'}`}>
                        {step.ok ? 'ok' : 'failed'}
                      </span>
                    </div>
                    <p>{step.output}</p>
                    <details>
                      <summary>View step data</summary>
                      <pre>{JSON.stringify(step.data, null, 2)}</pre>
                    </details>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>

        <aside className="workflow-detail-side">
          <section className="workflow-card page-panel">
            <h2>Run Info</h2>
            <div className="workflow-info-list">
              <div><span>Workflow:</span> {run.workflow?.name || 'Untitled'}</div>
              <div><span>Status:</span> {run.status}</div>
              <div><span>Created:</span> {new Date(run.created_at).toLocaleString()}</div>
            </div>
          </section>

          <section className="workflow-card page-panel">
            <h2>Raw Output</h2>
            <pre>{JSON.stringify(output, null, 2)}</pre>
          </section>
        </aside>
      </div>
    </div>
  );
}

export default WorkflowRunDetail;
