import React, { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiGet, getApiErrorMessage } from '../lib/api';
import './WorkflowApprovals.css';

function DiffPanel({ diff }) {
  if (!diff) return null;
  const fields = diff.field_changes || diff.changes || [];
  const list = Array.isArray(fields) ? fields : Object.entries(diff).map(([k, v]) => ({ field: k, ...v }));
  return (
    <div className="workflow-card page-panel" data-testid="operator-ledger-diff">
      <strong>Decision diff</strong>
      {list.length === 0 ? (
        <p className="workflow-muted">No field changes between selected events.</p>
      ) : (
        <ul className="workflow-approval-list">
          {list.map((item, idx) => (
            <li key={item.field || idx} className="workflow-step-type">
              <strong>{item.field || item.name}</strong>
              {item.before !== undefined ? ` · ${JSON.stringify(item.before)} → ${JSON.stringify(item.after)}` : null}
            </li>
          ))}
        </ul>
      )}
      {diff.risk_level_change ? <div className="workflow-step-type">Risk: {diff.risk_level_change}</div> : null}
    </div>
  );
}

function OperatorLedger() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [digest, setDigest] = useState(null);
  const [events, setEvents] = useState([]);
  const [compareIds, setCompareIds] = useState([]);
  const [diff, setDiff] = useState(null);
  const [sessionId, setSessionId] = useState(searchParams.get('session_id') || '');

  const scopeId = sessionId.trim() || 'global';
  const query = `?session_id=${encodeURIComponent(scopeId)}`;
  const replayPath = `/operator/replay/operator_session/${encodeURIComponent(scopeId)}`;

  useEffect(() => {
    const fromUrl = searchParams.get('session_id');
    if (fromUrl !== null && fromUrl !== sessionId) {
      setSessionId(fromUrl);
    }
  }, [searchParams, sessionId]);

  const refresh = useCallback(async () => {
    try {
      const [digestRes, listRes] = await Promise.all([
        apiGet(`/api/operator/ledger/digest${query}`),
        apiGet(`/api/operator/ledger${query}`),
      ]);
      setDigest(digestRes.data?.digest || null);
      setEvents(Array.isArray(listRes.data?.events) ? listRes.data.events : []);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not load operator ledger.'));
      setDigest(null);
      setEvents([]);
    }
  }, [query]);

  useEffect(() => {
    refresh();
    const interval = window.setInterval(refresh, 5000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  const applyScope = () => {
    const next = sessionId.trim() || 'global';
    setSearchParams(next === 'global' ? {} : { session_id: next });
  };

  const toggleCompare = (decisionId) => {
    setCompareIds((prev) => {
      if (prev.includes(decisionId)) return prev.filter((id) => id !== decisionId);
      if (prev.length >= 2) return [prev[1], decisionId];
      return [...prev, decisionId];
    });
    setDiff(null);
  };

  const runCompare = async () => {
    if (compareIds.length !== 2) {
      toast.error('Select exactly two events.');
      return;
    }
    try {
      const [fromId, toId] = compareIds;
      const res = await apiGet(
        `/api/operator/ledger/diff?session_id=${encodeURIComponent(scopeId)}&from_id=${encodeURIComponent(fromId)}&to_id=${encodeURIComponent(toId)}`,
      );
      setDiff(res.data?.diff || null);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Compare failed.'));
    }
  };

  return (
    <div className="workflow-page">
      <div className="page-intro">
        <h1>Operator Decision Ledger</h1>
        <p>Cross-plane accountability for pipeline, OTEM, URG, and operator decisions.</p>
      </div>
      <div className="workflow-page-actions">
        <input value={sessionId} onChange={(e) => setSessionId(e.target.value)} placeholder="session scope" />
        <button type="button" className="workflow-secondary-btn" onClick={applyScope}>Apply scope</button>
        <Link className="workflow-page-link" to={replayPath}>Open in Replay</Link>
        <Link className="workflow-page-link" to="/operator/ledger/graph">Graph view</Link>
        <Link className="workflow-page-link" to="/operator">Console</Link>
        {compareIds.length === 2 ? (
          <button type="button" className="workflow-secondary-btn" onClick={runCompare}>Compare</button>
        ) : null}
      </div>
      {digest ? (
        <div className="workflow-card page-panel" data-testid="operator-ledger-digest">
          <div>Entries: {digest.entry_count}</div>
          <div>Pending: {digest.pending_count}</div>
          <div>Cannot undo: {digest.cannot_undo_count}</div>
          <div>Cross-tenant: {digest.cross_tenant_decisions_count}</div>
        </div>
      ) : null}
      <div className="workflow-approval-list">
        {events.length === 0 ? (
          <div className="workflow-card workflow-empty-card">No events.</div>
        ) : (
          events.slice().reverse().map((event) => (
            <article key={event.decision_id} className="workflow-card page-panel">
              <strong>{event.decision_kind}</strong>
              <div className="workflow-step-type">{event.decision} · {event.summary}</div>
              <label><input type="checkbox" checked={compareIds.includes(event.decision_id)} onChange={() => toggleCompare(event.decision_id)} /> Compare</label>
            </article>
          ))
        )}
      </div>
      <DiffPanel diff={diff} />
    </div>
  );
}

export default OperatorLedger;
