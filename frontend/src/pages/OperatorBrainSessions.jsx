import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiGet, apiPost, getApiErrorMessage } from '../lib/api';
import './WorkflowApprovals.css';

function RankingsPanel({ proposal }) {
  if (!proposal) return null;
  const organs = proposal.organ_rankings || [];
  const chains = proposal.chain_rankings || [];
  return (
    <div className="workflow-card page-panel">
      <strong>Organ rankings</strong>
      <ul>{organs.map((o) => <li key={o.family_id || o.rank}>{o.rank}. {o.family_id} ({o.fitness_score})</li>)}</ul>
      <strong>Chain rankings</strong>
      <ul>{chains.map((c) => <li key={c.workflow_id || c.rank}>{c.rank}. {c.workflow_id} ({c.fitness_score})</li>)}</ul>
    </div>
  );
}

function OperatorBrainSessions() {
  const [sessions, setSessions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [text, setText] = useState('research a topic and draft a brief');
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiGet('/api/operator/brain/sessions');
      setSessions(Array.isArray(res.data?.sessions) ? res.data.sessions : []);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not load brain sessions.'));
      setSessions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const createSession = async () => {
    try {
      const res = await apiPost('/api/operator/brain/sessions', { text, include_deliberation: true });
      setSelected(res.data?.session || null);
      await refresh();
      toast.success('Brain session created.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not create session.'));
    }
  };

  const decide = async (decision) => {
    if (!selected?.session_id) return;
    try {
      const res = await apiPost(`/api/operator/brain/sessions/${encodeURIComponent(selected.session_id)}/decide`, { decision });
      setSelected(res.data?.session || null);
      await refresh();
      toast.success(`Decision: ${decision}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not record decision.'));
    }
  };

  const latestProposal = selected?.proposals?.[selected.proposals.length - 1];
  const latestDeliberation = selected?.deliberations?.[selected.deliberations.length - 1];

  return (
    <div className="workflow-page">
      <div className="page-intro">
        <h1>Brain Sessions</h1>
        <p>Proposal-only Nova Cortex routing — accept, reject, or defer.</p>
      </div>
      <div className="workflow-page-actions">
        <Link className="workflow-page-link" to="/operator">Console</Link>
        <Link className="workflow-page-link" to="/operator/plugins">Plugins</Link>
        <Link className="workflow-page-link" to="/operator/ledger">Decision Ledger</Link>
      </div>
      <div className="workflow-card page-panel">
        <label>
          Operator text
          <input value={text} onChange={(e) => setText(e.target.value)} style={{ marginLeft: '0.5rem', width: '60%' }} />
        </label>
        <button type="button" className="workflow-secondary-btn" onClick={createSession} style={{ marginLeft: '0.5rem' }}>
          New session
        </button>
      </div>
      {loading ? (
        <div className="workflow-card workflow-empty-card">Loading...</div>
      ) : (
        <div className="workflow-approval-list">
          {sessions.length === 0 ? (
            <div className="workflow-card workflow-empty-card">No brain sessions yet.</div>
          ) : (
            sessions.slice().reverse().map((session) => (
              <article key={session.session_id} className="workflow-card page-panel workflow-approval-card">
                <div className="workflow-approval-header">
                  <div>
                    <strong>{session.session_id.slice(0, 20)}</strong>
                    <div className="workflow-step-type">{session.operator_decision}</div>
                  </div>
                  <button type="button" className="workflow-secondary-btn" onClick={() => setSelected(session)}>
                    View
                  </button>
                </div>
                <div className="workflow-approval-reason">{session.operator_text}</div>
              </article>
            ))
          )}
        </div>
      )}
      {selected ? (
        <div data-testid="brain-session-detail">
          <div className="workflow-card page-panel">
            <strong>Session {selected.session_id}</strong>
            <div className="workflow-step-type">Status: {selected.status} · Decision: {selected.operator_decision}</div>
            <div className="workflow-page-actions">
              <button type="button" className="workflow-secondary-btn" onClick={() => decide('accept')}>Accept</button>
              <button type="button" className="workflow-secondary-btn" onClick={() => decide('reject')}>Reject</button>
              <button type="button" className="workflow-secondary-btn" onClick={() => decide('defer')}>Defer</button>
            </div>
          </div>
          <RankingsPanel proposal={latestProposal} />
          {latestDeliberation ? (
            <div className="workflow-card page-panel">
              <strong>Deliberation</strong>
              <div className="workflow-step-type">{latestDeliberation.status} · {latestDeliberation.deliberation_id}</div>
              <p>{latestDeliberation.summary || latestDeliberation.operator_text}</p>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export default OperatorBrainSessions;
