import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiGet, apiPost, getApiErrorMessage } from '../lib/api';
import './WorkflowApprovals.css';

const DECISIONS = [
  'rollback_to_checkpoint',
  'quarantine_archive',
  'safe_mode_reanchor',
  'accept_containment',
  'constitutional_amendment',
];

function OperatorCeilingRecovery() {
  const [status, setStatus] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scopeId, setScopeId] = useState('global');

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiGet('/api/operator/ceiling');
      setStatus(res.data?.ceiling || res.data || null);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not load ceiling status.'));
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const invokeCeiling = async () => {
    try {
      const res = await apiPost('/api/operator/ceiling/invoke', {
        summary: 'operator UI ceiling invoke',
        scope_id: scopeId,
      });
      setStatus(res.data || null);
      setPreview(null);
      toast.success('Ceiling invocation recorded.');
      await refresh();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not invoke ceiling.'));
    }
  };

  const runPreview = async (decision) => {
    try {
      const res = await apiPost('/api/operator/ceiling/preview', {
        decision,
        scope_id: scopeId,
      });
      setPreview(res.data || null);
      toast.success(`Preview: ${decision}`);
      await refresh();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Preview failed.'));
    }
  };

  const applyDecision = async (decision) => {
    try {
      const res = await apiPost('/api/operator/ceiling/apply', {
        decision,
        scope_id: scopeId,
        operator_id: 'operator-ui',
      });
      setPreview(null);
      setStatus((prev) => ({ ...(prev || {}), ...(res.data || {}) }));
      toast.success(`Applied: ${decision}`);
      await refresh();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Apply failed.'));
    }
  };

  return (
    <div className="workflow-page" data-testid="operator-ceiling-page">
      <div className="page-intro">
        <h1>OTEM Ceiling Recovery</h1>
        <p>
          Sovereign band (level 20) constitutional recovery — diagnostic bundle, preview, explicit
          operator decision, ODL closure, and post-decision hardening.
        </p>
      </div>
      <div className="workflow-page-actions">
        <Link className="workflow-page-link" to="/operator">Console</Link>
        <Link className="workflow-page-link" to="/operator/ledger">Decision Ledger</Link>
      </div>

      <div className="workflow-card page-panel">
        <label>
          Scope ID
          <input
            value={scopeId}
            onChange={(e) => setScopeId(e.target.value)}
            style={{ marginLeft: '0.5rem', width: '40%' }}
          />
        </label>
        <button type="button" className="workflow-secondary-btn" onClick={invokeCeiling} style={{ marginLeft: '0.5rem' }}>
          Invoke containment
        </button>
        <button type="button" className="workflow-secondary-btn" onClick={refresh} style={{ marginLeft: '0.5rem' }}>
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="workflow-card workflow-empty-card">Loading ceiling status...</div>
      ) : (
        <div className="workflow-card page-panel" data-testid="ceiling-status-panel">
          <strong>Pipeline status</strong>
          <div className="workflow-step-type">
            Band: {status?.authority_band || '—'} · Level: {status?.numeric_level ?? '—'}
          </div>
          <div className="workflow-step-type">
            Containment: {String(status?.containment_mode ?? false)} · Ceiling active:{' '}
            {String(status?.ceiling_active ?? false)}
          </div>
          <div className="workflow-step-type">
            Pipeline: {status?.pipeline_state || 'idle'} · Pending: {status?.pending_decision || 'none'}
          </div>
          <div className="workflow-approval-reason">
            Triggers: {(status?.activation_triggers || []).join(', ') || 'none'}
          </div>
        </div>
      )}

      <div className="workflow-card page-panel">
        <strong>Constitutional decisions</strong>
        <div className="workflow-page-actions" style={{ flexWrap: 'wrap' }}>
          {DECISIONS.map((decision) => (
            <span key={decision} style={{ display: 'inline-flex', gap: '0.25rem', margin: '0.25rem' }}>
              <button type="button" className="workflow-secondary-btn" onClick={() => runPreview(decision)}>
                Preview {decision}
              </button>
              <button type="button" className="workflow-primary-btn" onClick={() => applyDecision(decision)}>
                Apply
              </button>
            </span>
          ))}
        </div>
      </div>

      {preview ? (
        <div className="workflow-card page-panel" data-testid="ceiling-preview-panel">
          <strong>Latest preview</strong>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem' }}>
            {JSON.stringify(preview, null, 2)}
          </pre>
        </div>
      ) : null}
    </div>
  );
}

export default OperatorCeilingRecovery;
