import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FiActivity, FiArrowLeft, FiRefreshCw } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { apiGet, getApiErrorMessage } from '../lib/api';
import { UGRCloudForgeConsoleCard } from '../components/operator/UGRCloudForgeConsoleCard';
import '../pages/Dashboard.css';
import './OperatorConsole.css';

const MESH_POLL_MS = 15000;

function toneForClaim(value) {
  const normalized = String(value || '').toLowerCase();
  if (normalized === 'proven') {
    return 'connected';
  }
  if (normalized === 'rejected') {
    return 'error';
  }
  return 'warning';
}

function toneForPollStatus(value) {
  const normalized = String(value || '').toLowerCase();
  if (normalized === 'ok') {
    return 'aligned';
  }
  if (normalized === 'partial') {
    return 'missing';
  }
  return 'missing';
}

export default function OperatorConsolePage() {
  const [snapshot, setSnapshot] = useState(null);
  const [meshHealth, setMeshHealth] = useState(null);
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadSnapshot = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiGet('/api/operator/console');
      setSnapshot(response.data || null);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not load operator console.'));
      setSnapshot(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadMeshHealth = useCallback(async () => {
    try {
      const response = await apiGet('/api/operator/console/mesh-health');
      setMeshHealth(response.data || null);
    } catch {
      setMeshHealth(null);
    }
  }, []);

  const loadTraceDetail = useCallback(async (traceId) => {
    if (!traceId) {
      setSelectedTrace(null);
      return;
    }
    try {
      const response = await apiGet(`/api/operator/console/traces?trace_id=${encodeURIComponent(traceId)}`);
      const traces = response.data?.traces || [];
      setSelectedTrace(traces[0] || null);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not load trace detail.'));
      setSelectedTrace(null);
    }
  }, []);

  useEffect(() => {
    loadSnapshot();
  }, [loadSnapshot]);

  useEffect(() => {
    loadMeshHealth();
    const timer = window.setInterval(loadMeshHealth, MESH_POLL_MS);
    return () => window.clearInterval(timer);
  }, [loadMeshHealth]);

  const debtItems = snapshot?.debt_register?.items || [];
  const gates = snapshot?.gates || [];
  const trust = snapshot?.trust_bundle || {};
  const ugr = snapshot?.ugr || {};
  const flags = ugr.feature_flags || {};
  const mesh = meshHealth || snapshot?.mesh_health || {};
  const meshServices = mesh.services || [];
  const traceSummaries = snapshot?.deliberation_traces?.summaries || [];
  const forgePlatform = snapshot?.forge_platform || {};
  const platformDashboard = forgePlatform.dashboard || {};
  const platformGates = platformDashboard.gates || [];
  const platformSubstrates = platformDashboard.substrates || {};

  return (
    <section className="workbench operator-console-page" data-testid="operator-console-page">
      <header className="workbench-hero">
        <div className="workbench-hero-copy">
          <p className="eyebrow">Operator Console</p>
          <h1>UGR + Cloud Forge</h1>
          <p>
            Jarvis-style advisory surface for governed runtime health, Cloud Forge rails,
            trust bundle status, and program debt. Readouts are evidence-first and do not mutate runtime state.
          </p>
          <div className="workbench-hero-actions">
            <Link to="/jarvis" className="workbench-button ghost">
              <FiArrowLeft /> Back to Console
            </Link>
            <Link to="/operator/replay" className="workbench-button ghost">
              Temporal Replay
            </Link>
            <button type="button" className="workbench-button primary" onClick={loadSnapshot} disabled={loading}>
              <FiRefreshCw /> Refresh
            </button>
          </div>
        </div>
        <div className="workbench-hero-side page-panel">
          <div className="workbench-health-row">
            <span>Console claim</span>
            <strong className={`operator-claim-${toneForClaim(snapshot?.claim_status)}`}>
              {snapshot?.claim_status || 'asserted'}
            </strong>
          </div>
          <div className="workbench-health-row">
            <span>UGR deployment</span>
            <strong>{ugr.deployment_mode || 'monolith'}</strong>
          </div>
          <div className="workbench-health-row">
            <span>Mesh poll</span>
            <strong>{mesh.poll_status || 'unknown'}</strong>
          </div>
          <div className="workbench-health-row">
            <span>Trust bundle</span>
            <strong>{trust.overall_status || 'missing'}</strong>
          </div>
          <div className="workbench-health-row">
            <span>Open debt</span>
            <strong>{snapshot?.debt_register?.open ?? '—'}</strong>
          </div>
        </div>
      </header>

      <div className="operator-console-grid">
        <UGRCloudForgeConsoleCard compact meshHealth={mesh} />

        <section className="workbench-section page-panel" data-testid="operator-mesh-health">
          <div className="workbench-section-head">
            <div>
              <span>Live poll · {MESH_POLL_MS / 1000}s</span>
              <h2>Mesh health</h2>
            </div>
            <button type="button" className="workbench-button ghost" onClick={loadMeshHealth}>
              <FiRefreshCw /> Poll now
            </button>
          </div>
          <p className="workbench-muted">
            {mesh.healthy_count ?? 0}/{mesh.total_count ?? 0} healthy · polled {mesh.polled_at_utc || '—'}
          </p>
          <div className="workbench-history-list">
            {meshServices.map((service) => (
              <div key={service.name} className="workbench-history-item">
                <div className="workbench-list-title">
                  <strong>{service.name}</strong>
                  <span className={`workbench-chip ${toneForPollStatus(service.status === 'ok' ? 'ok' : 'partial')}`}>
                    {service.status}
                  </span>
                </div>
                <small>{service.base_url || service.error || JSON.stringify(service.health || {})}</small>
              </div>
            ))}
          </div>
        </section>

        <section className="workbench-section page-panel" data-testid="operator-traces">
          <div className="workbench-section-head">
            <div>
              <span>Deliberation</span>
              <h2>Trace viewer</h2>
            </div>
          </div>
          <p className="workbench-muted">
            {snapshot?.deliberation_traces?.trace_count ?? 0} traces in ledger · showing {traceSummaries.length}
          </p>
          <div className="workbench-history-list">
            {traceSummaries.map((trace) => (
              <button
                key={trace.trace_id}
                type="button"
                className="workbench-history-item operator-trace-button"
                onClick={() => loadTraceDetail(trace.trace_id)}
              >
                <div className="workbench-list-title">
                  <strong>{trace.trace_id}</strong>
                  <span className="workbench-chip aligned">{trace.status}</span>
                </div>
                <p>{trace.intent || '—'}</p>
                <small>
                  lanes={trace.lane_count ?? 0} beliefs={trace.accepted_beliefs ?? 0} rail={trace.rail || '—'}
                </small>
              </button>
            ))}
          </div>
          {selectedTrace ? (
            <div className="workbench-code">
              <pre>{JSON.stringify(selectedTrace, null, 2)}</pre>
            </div>
          ) : null}
        </section>

        <section className="workbench-section page-panel" data-testid="operator-forge-platform">
          <div className="workbench-section-head">
            <div>
              <span>Cloud Forge</span>
              <h2>Platform dashboard</h2>
            </div>
          </div>
          <p className="workbench-muted">{forgePlatform.summary || 'Forge platform dashboard not loaded.'}</p>
          <div className="workbench-chip-row">
            <span className="workbench-chip aligned">
              substrates={platformSubstrates.substrate_count ?? 0}
            </span>
            <span className="workbench-chip aligned">gates={platformGates.length}</span>
          </div>
          <div className="workbench-history-list">
            {platformGates.slice(0, 8).map((gate) => (
              <div key={gate.id || gate.name} className="workbench-history-item">
                <div className="workbench-list-title">
                  <strong>{gate.id || gate.name}</strong>
                  <span className={`workbench-chip ${gate.level === 'green' ? 'aligned' : 'missing'}`}>
                    {gate.level || gate.status}
                  </span>
                </div>
                <p>{gate.summary || gate.description || '—'}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="workbench-section page-panel" data-testid="operator-feature-flags">
          <div className="workbench-section-head">
            <div>
              <span>Feature flags</span>
              <h2>UGR enablement</h2>
            </div>
          </div>
          <div className="workbench-chip-row">
            {Object.entries(flags).map(([key, value]) => (
              <span key={key} className={`workbench-chip ${value ? 'aligned' : 'missing'}`}>
                {key}={String(value)}
              </span>
            ))}
          </div>
        </section>

        <section className="workbench-section page-panel" data-testid="operator-debt-register">
          <div className="workbench-section-head">
            <div>
              <span>Program debt</span>
              <h2>UGR + Forge register</h2>
            </div>
          </div>
          <div className="workbench-history-list">
            {debtItems.map((item) => (
              <div key={item.id} className="workbench-history-item">
                <div className="workbench-list-title">
                  <strong>{item.id}</strong>
                  <span className={`workbench-chip ${item.status === 'closed' ? 'aligned' : 'missing'}`}>
                    {item.status}
                  </span>
                </div>
                <p>{item.item}</p>
                <small>
                  {item.severity} · {item.owner} · claim {item.claim_status}
                </small>
              </div>
            ))}
          </div>
        </section>

        <section className="workbench-section page-panel" data-testid="operator-gates">
          <div className="workbench-section-head">
            <div>
              <span>Verification</span>
              <h2>Governance gates</h2>
            </div>
          </div>
          <div className="workbench-code">
            <pre>{gates.join('\n')}</pre>
          </div>
          <p className="workbench-muted">
            Primary bundle command: {snapshot?.verification_command || 'make ugr-operator-console-gate'}
          </p>
        </section>

        <section className="workbench-section page-panel" data-testid="operator-readout-json">
          <div className="workbench-section-head">
            <div>
              <span>Readout</span>
              <h2>Advisory payload</h2>
            </div>
            <FiActivity />
          </div>
          <div className="workbench-code">
            <pre>{JSON.stringify(snapshot?.readout || {}, null, 2)}</pre>
          </div>
        </section>
      </div>
    </section>
  );
}
