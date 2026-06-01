import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { platformGet, platformPost } from '../lib/platformApi';
import './PlatformConsole.css';

const DEFAULT_STEPS = [
  { subsystem: 'mechanic', kind: 'mechanic.scan' },
  { subsystem: 'slingshot', kind: 'slingshot.preload' },
  { subsystem: 'lab', kind: 'lab.session' },
];

export default function PlatformWorkflow() {
  const [orgId, setOrgId] = useState(localStorage.getItem('platform_org_id') || '');
  const [name, setName] = useState('e2e-pipeline');
  const [stepsJson, setStepsJson] = useState(JSON.stringify(DEFAULT_STEPS, null, 2));
  const [workflows, setWorkflows] = useState([]);
  const [lastRun, setLastRun] = useState(null);
  const [error, setError] = useState('');

  async function loadWorkflows() {
    try {
      const data = await platformGet(`/v1/workflows?org_id=${encodeURIComponent(orgId)}`);
      setWorkflows(data.workflows || []);
    } catch (err) {
      setError(err.message);
    }
  }

  async function onCreate(e) {
    e.preventDefault();
    setError('');
    try {
      const steps = JSON.parse(stepsJson);
      const wf = await platformPost(`/v1/workflows?org_id=${encodeURIComponent(orgId)}`, { name, steps });
      setWorkflows((prev) => [wf, ...prev]);
    } catch (err) {
      setError(err.message || 'Create failed');
    }
  }

  async function onRun(workflowId) {
    setError('');
    try {
      const data = await platformPost(
        `/v1/workflows/${workflowId}/run?org_id=${encodeURIComponent(orgId)}`,
        {},
      );
      setLastRun(data.workflow_run);
    } catch (err) {
      setError(err.message || 'Run failed');
    }
  }

  return (
    <div className="platform-console page-shell">
      <header className="platform-console__header">
        <h1>Platform Workflows</h1>
        <p className="platform-console__subtitle">Declarative DAG of platform jobs (v14).</p>
        <nav className="platform-console__nav">
          <Link to="/platform">Console</Link>
          <Link to="/platform/assistant">Assistant</Link>
        </nav>
      </header>
      <form className="platform-console__form" onSubmit={onCreate}>
        <label>
          Org ID
          <input value={orgId} onChange={(e) => setOrgId(e.target.value)} required />
        </label>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          Steps (JSON)
          <textarea value={stepsJson} onChange={(e) => setStepsJson(e.target.value)} rows={8} />
        </label>
        <button type="submit">Create workflow</button>
        <button type="button" onClick={loadWorkflows}>
          Refresh list
        </button>
      </form>
      {error && <p className="platform-console__error">{error}</p>}
      <section className="platform-console__panel">
        <h2>Workflows</h2>
        <ul>
          {workflows.map((w) => (
            <li key={w.workflow_id}>
              {w.name} ({w.workflow_id}){' '}
              <button type="button" onClick={() => onRun(w.workflow_id)}>
                Run
              </button>
            </li>
          ))}
        </ul>
      </section>
      {lastRun && (
        <section className="platform-console__panel">
          <h2>Last run</h2>
          <p>
            Job:{' '}
            <Link to={`/platform/jobs/${lastRun.job_id}?org_id=${orgId}`}>{lastRun.job_id}</Link>
          </p>
          <pre>{JSON.stringify(lastRun.metadata, null, 2)}</pre>
        </section>
      )}
    </div>
  );
}
