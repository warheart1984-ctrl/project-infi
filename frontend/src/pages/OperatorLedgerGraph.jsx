import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiGet, getApiErrorMessage } from '../lib/api';
import './WorkflowApprovals.css';

function OperatorLedgerGraph() {
  const [sessionId, setSessionId] = useState('global');
  const [grantId, setGrantId] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [federationGraph, setFederationGraph] = useState(null);
  const [loading, setLoading] = useState(false);

  const scopeId = sessionId.trim() || 'global';

  const loadQuery = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiGet(`/api/operator/ledger/query?session_id=${encodeURIComponent(scopeId)}&limit=50`);
      setQueryResult(res.data || null);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Query failed.'));
      setQueryResult(null);
    } finally {
      setLoading(false);
    }
  }, [scopeId]);

  const loadFederation = useCallback(async () => {
    const gid = grantId.trim();
    if (!gid) {
      toast.error('Grant id required for federation graph.');
      return;
    }
    setLoading(true);
    try {
      const res = await apiGet(`/api/operator/ledger/federation/${encodeURIComponent(gid)}/graph?session_id=${encodeURIComponent(scopeId)}`);
      setFederationGraph(res.data || null);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Federation graph failed.'));
      setFederationGraph(null);
    } finally {
      setLoading(false);
    }
  }, [grantId, scopeId]);

  useEffect(() => {
    loadQuery();
  }, [loadQuery]);

  const nodes = federationGraph
    ? [...(federationGraph.home_nodes || []), ...(federationGraph.peer_nodes || [])]
    : (queryResult?.entries || []);

  const edges = federationGraph?.edges || [];

  return (
    <div className="workflow-page">
      <div className="page-intro">
        <h1>ODL Graph</h1>
        <p>Causal index and federation graph for operator decision ledger.</p>
      </div>
      <div className="workflow-page-actions">
        <input value={sessionId} onChange={(e) => setSessionId(e.target.value)} placeholder="session scope" />
        <button type="button" className="workflow-secondary-btn" onClick={loadQuery}>Refresh query</button>
        <input value={grantId} onChange={(e) => setGrantId(e.target.value)} placeholder="federation grant id" />
        <button type="button" className="workflow-secondary-btn" onClick={loadFederation}>Load federation</button>
        <Link className="workflow-page-link" to="/operator/ledger">Ledger list</Link>
        <Link className="workflow-page-link" to="/operator">Console</Link>
      </div>
      {loading ? <div className="workflow-card workflow-empty-card">Loading...</div> : null}
      <div className="workflow-card page-panel" data-testid="odl-graph-canvas">
        <strong>Nodes ({nodes.length})</strong>
        <ul className="workflow-approval-list">
          {nodes.map((node) => (
            <li key={node.decision_id || node.id}>
              {node.decision_kind || node.kind || 'node'} · {node.decision_id || node.id} · {node.summary || ''}
            </li>
          ))}
        </ul>
        {edges.length > 0 ? (
          <>
            <strong>Edges ({edges.length})</strong>
            <ul>{edges.map((edge, idx) => <li key={idx}>{edge.from} → {edge.to}</li>)}</ul>
          </>
        ) : null}
        {federationGraph ? (
          <div className="workflow-step-type">
            digest_verified={String(federationGraph.digest_verified)} · peer_scope={federationGraph.peer_scope || '—'}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default OperatorLedgerGraph;
