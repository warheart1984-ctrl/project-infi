import React, { useCallback, useEffect, useState } from 'react';
import { FiActivity, FiCloud, FiRefreshCw, FiShield } from 'react-icons/fi';
import { apiGet, getApiErrorMessage } from '../lib/api';

function claimTone(claimStatus) {
  const normalized = String(claimStatus || '').toLowerCase();
  if (normalized === 'proven') {
    return 'success';
  }
  if (normalized === 'rejected') {
    return 'danger';
  }
  return 'warning';
}

function statusTone(status) {
  const normalized = String(status || '').toLowerCase();
  if (['ok', 'pass', 'healthy', 'closed', 'proven'].includes(normalized)) {
    return 'success';
  }
  if (['fail', 'error', 'missing', 'open'].includes(normalized)) {
    return 'warning';
  }
  return 'ghost';
}

export function UGRCloudForgeConsoleCard({ compact = false, meshHealth = null }) {
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiGet('/api/operator/console');
      setSnapshot(response.data || null);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Could not load operator console.'));
      setSnapshot(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const ugr = snapshot?.ugr || {};
  const forge = snapshot?.cloud_forge || {};
  const trust = snapshot?.trust_bundle || {};
  const debt = snapshot?.debt_register || {};
  const readout = snapshot?.readout || {};
  const mesh = meshHealth || snapshot?.mesh_health || {};
  const debtItems = debt.items || [];

  return (
    <div className="jarvis-side-card page-panel" data-testid="ugr-cloud-forge-console-card">
      <div className="jarvis-side-title">
        <FiActivity />
        <h3>{compact ? 'UGR / Forge' : 'UGR + Cloud Forge'}</h3>
        <button type="button" className="jarvis-icon-button" onClick={refresh} disabled={loading} aria-label="Refresh operator console">
          <FiRefreshCw />
        </button>
      </div>

      <details className="jarvis-collapsible-panel" open={!compact}>
        <summary className="jarvis-collapsible-summary">
          <div className="jarvis-collapsible-copy">
            <span>Organ health, rails, trust bundle, debt</span>
            <strong>{readout.summary || 'Operator readout loading…'}</strong>
          </div>
        </summary>
        <div className="jarvis-collapsible-body">
          {error ? <p className="session-empty">{error}</p> : null}
          {!error && (
            <>
              <div className="jarvis-inline-meta">
                <span className={`inline-meta-chip ${claimTone(snapshot?.claim_status)}`}>
                  console {snapshot?.claim_status || 'asserted'}
                </span>
                <span className={`inline-meta-chip ${statusTone(ugr.status)}`}>
                  ugr {ugr.deployment_mode || 'monolith'}
                </span>
                <span className={`inline-meta-chip ${statusTone(mesh.poll_status === 'ok' ? 'ok' : 'missing')}`}>
                  mesh {mesh.poll_status || 'unknown'}
                </span>
                <span className={`inline-meta-chip ${statusTone(trust.overall_status)}`}>
                  trust {trust.overall_status || 'missing'}
                </span>
                <span className={`inline-meta-chip ${statusTone(forge.rail)}`}>
                  rail {forge.rail || 'NORMAL'}
                </span>
              </div>

              <div className="v8-event-list">
                <div className="v8-event-item">
                  <div className="v8-event-header">
                    <strong><FiCloud /> Mesh</strong>
                    <span>{ugr.mesh_cluster_id || 'local'}</span>
                  </div>
                  <p>{(ugr.mesh_services || []).slice(0, 8).join(', ')}{(ugr.mesh_services || []).length > 8 ? '…' : ''}</p>
                  <p>
                    live poll: {mesh.healthy_count ?? 0}/{mesh.total_count ?? 0} healthy
                    {mesh.polled_at_utc ? ` · ${mesh.polled_at_utc}` : ''}
                  </p>
                </div>

                <div className="v8-event-item">
                  <div className="v8-event-header">
                    <strong><FiShield /> Trust bundle</strong>
                    <span>{trust.overall_status || 'missing'}</span>
                  </div>
                  <p>
                    {trust.summary
                      || 'Run make ugr-trust-bundle-gate to emit proof_bundle.json'}
                  </p>
                </div>
              </div>

              {!compact && debtItems.length > 0 ? (
                <div className="v8-event-list">
                  {debtItems.slice(0, 6).map((item) => (
                    <div key={item.id} className="v8-event-item" data-testid={`debt-${item.id}`}>
                      <div className="v8-event-header">
                        <strong>{item.id}</strong>
                        <span>{item.status}</span>
                      </div>
                      <p>{item.item}</p>
                    </div>
                  ))}
                </div>
              ) : null}

              <p className="session-empty">{snapshot?.runtime_effect === 'readout_only' ? 'Advisory readout only — no runtime mutation.' : ''}</p>
            </>
          )}
        </div>
      </details>
    </div>
  );
}

export default UGRCloudForgeConsoleCard;
