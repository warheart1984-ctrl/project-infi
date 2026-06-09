import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FiActivity, FiArrowLeft, FiRefreshCw } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { apiGet, getApiErrorMessage } from '../lib/api';
import { UGRCloudForgeConsoleCard } from '../components/UGRCloudForgeConsoleCard';
import { SeamStressPanel } from '../components/operator/SeamStressPanel';
import { WorkflowStackPanel } from '../components/operator/WorkflowStackPanel';
import { LedgerDigestCompact } from '../components/operator/LedgerDigestCompact';
import { BrainQueueCompact } from '../components/operator/BrainQueueCompact';
import { MonitoringAlertsPanel } from '../components/operator/MonitoringAlertsPanel';
import '../pages/Dashboard.css';
import './OperatorConsole.css';

const MESH_POLL_MS = 15000;
const SEAM_POLL_MS = 15000;

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

function UGRRewardsCompact({ rewards }) {
  const data = rewards || {};
  return (
    <div className="workbench-chip-row" data-testid="ugr-rewards-compact">
      <span className={`workbench-chip ${data.enabled ? 'aligned' : 'missing'}`}>
        rewards={data.enabled ? 'on' : 'off'}
      </span>
      <span className={`workbench-chip ${data.shadow_only ? 'warning' : 'aligned'}`}>
        shadow={data.shadow_only ? 'yes' : 'no'}
      </span>
      <span className="workbench-chip aligned">
        purchase_max={data.purchase?.max_per_purchase ?? '—'}
      </span>
    </div>
  );
}

export default function OperatorConsolePage() {
  const [snapshot, setSnapshot] = useState(null);
  const [meshHealth, setMeshHealth] = useState(null);
  const [seamHealth, setSeamHealth] = useState(null);
  const [monitoring, setMonitoring] = useState(null);
  const [somaticHealth, setSomaticHealth] = useState(null);
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

  const loadSeamHealth = useCallback(async () => {
    try {
      const response = await apiGet('/api/operator/dashboard/seam-health');
      setSeamHealth(response.data || null);
    } catch {
      setSeamHealth(null);
    }
  }, []);

  const loadMonitoring = useCallback(async () => {
    try {
      const response = await apiGet('/api/operator/dashboard/monitoring');
      setMonitoring(response.data || null);
    } catch {
      setMonitoring(null);
    }
  }, []);

  const loadSomaticHealth = useCallback(async () => {
    try {
      const response = await apiGet('/api/operator/dashboard/somatic-health');
      setSomaticHealth(response.data || null);
    } catch {
      setSomaticHealth(null);
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
    loadSeamHealth();
    loadMonitoring();
    loadSomaticHealth();
    const meshTimer = window.setInterval(loadMeshHealth, MESH_POLL_MS);
    const seamTimer = window.setInterval(loadSeamHealth, SEAM_POLL_MS);
    const monitoringTimer = window.setInterval(loadMonitoring, MESH_POLL_MS);
    const somaticTimer = window.setInterval(loadSomaticHealth, MESH_POLL_MS);
    return () => {
      window.clearInterval(meshTimer);
      window.clearInterval(seamTimer);
      window.clearInterval(monitoringTimer);
      window.clearInterval(somaticTimer);
    };
  }, [loadMeshHealth, loadSeamHealth, loadMonitoring, loadSomaticHealth]);

  const infinity1 = {
    ...(snapshot?.infinity1 || {}),
    ...(seamHealth
      ? {
          health: seamHealth.health,
          seam_stress: seamHealth.seam_stress,
        }
      : {}),
    ...(monitoring ? { monitoring } : {}),
  };
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
  const operatorRewards = snapshot?.operator_rewards || {};

  return (
    <section className="workbench operator-console-page" data-testid="operator-console-page">
      <header className="workbench-hero">
        <div className="workbench-hero-copy">
          <p className="eyebrow">Infinity-1 Operator Dashboard</p>
          <h1>Seam health + accountability</h1>
          <p>
            Unified operator landing for SEAM_LAW runtime closure, workflow stack gates,
            decision ledger and Brain proposal readouts, plus UGR + Cloud Forge advisory panels below.
            All surfaces are read-only evidence — no execution authority.
          </p>
          <div className="workbench-hero-actions">
            <Link to="/jarvis" className="workbench-button ghost">
              <FiArrowLeft /> Back to Console
            </Link>
            <Link to="/operator/plugins" className="workbench-button ghost">Plugins</Link>
            <Link to="/operator/brain" className="workbench-button ghost">Brain</Link>
            <Link to="/operator/ceiling" className="workbench-button ghost">Ceiling</Link>
            <Link to="/operator/ledger" className="workbench-button ghost">Ledger</Link>
            <Link to="/operator/replay/operator_session/global" className="workbench-button ghost">Replay</Link>
            <button type="button" className="workbench-button primary" onClick={loadSnapshot} disabled={loading}>
              <FiRefreshCw /> Refresh
            </button>
          </div>
        </div>
        <div className="workbench-hero-side page-panel">
          <div className="workbench-health-row">
            <span>Infinity-1 claim</span>
            <strong className={`operator-claim-${toneForClaim(infinity1?.claim_status)}`}>
              {infinity1?.claim_status || 'asserted'}
            </strong>
          </div>
          <div className="workbench-health-row">
            <span>Seam closure</span>
            <strong>{infinity1?.seam_stress?.closure_status || 'unknown'}</strong>
          </div>
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

      <div className="operator-console-grid infinity1-dashboard-grid" data-testid="infinity1-dashboard-grid">
        <SeamStressPanel infinity1={infinity1} />
        <WorkflowStackPanel workflowStack={infinity1?.workflow_stack} />
        <LedgerDigestCompact ledgerDigest={infinity1?.ledger_digest} />
        <BrainQueueCompact brain={infinity1?.brain} />
        <MonitoringAlertsPanel monitoring={infinity1?.monitoring} />

        <section className="workbench-section page-panel" data-testid="operator-somatic-health">
          <h2>Somatic health</h2>
          <p className="section-lead">Unified operator/system posture map.</p>
          <div className="workbench-chip-row">
            <span className={`workbench-chip ${toneForPollStatus(somaticHealth?.overall_posture === 'nominal' ? 'ok' : 'partial')}`}>
              overall={somaticHealth?.overall_posture || 'unknown'}
            </span>
            <span className="workbench-chip aligned">
              pending_otem={somaticHealth?.substrate_posture?.pending_otem_approvals ?? '—'}
            </span>
            <span className="workbench-chip missing">
              stale_otem={somaticHealth?.substrate_posture?.stale_otem_approvals ?? '—'}
            </span>
            <span className={`workbench-chip ${somaticHealth?.doctor?.healthy ? 'aligned' : 'missing'}`}>
              doctor={somaticHealth?.doctor?.healthy ? 'ok' : 'check'}
            </span>
            <span className="workbench-chip aligned">
              active_mesh={somaticHealth?.active_mesh_runs ?? somaticHealth?.organ_mesh_posture?.active_mesh_runs ?? '—'}
            </span>
            <span className="workbench-chip missing">
              blocked_handoffs={somaticHealth?.blocked_handoffs ?? somaticHealth?.organ_mesh_posture?.blocked_handoffs ?? '—'}
            </span>
            <span className="workbench-chip aligned">
              adopted_habits={somaticHealth?.adopted_habits ?? somaticHealth?.culture_posture?.adopted_habits ?? '—'}
            </span>
            <span className="workbench-chip missing">
              habit_candidates={somaticHealth?.habit_candidates ?? somaticHealth?.culture_posture?.candidate_habits ?? '—'}
            </span>
            <span className="workbench-chip aligned">
              adopted_claims={somaticHealth?.adopted_claims ?? somaticHealth?.identity_posture?.adopted_claims ?? '—'}
            </span>
            <span className="workbench-chip missing">
              identity_drift={somaticHealth?.identity_drift_events ?? somaticHealth?.identity_posture?.identity_drift_events ?? '—'}
            </span>
            <span className="workbench-chip aligned">
              adopted_beats={somaticHealth?.adopted_beats ?? somaticHealth?.narrative_posture?.adopted_beats ?? '—'}
            </span>
            <span className="workbench-chip missing">
              narrative_drift={somaticHealth?.narrative_drift_events ?? somaticHealth?.narrative_posture?.narrative_drift_events ?? '—'}
            </span>
            <span className="workbench-chip aligned">
              adopted_episodes={somaticHealth?.adopted_episodes ?? somaticHealth?.autobiographical_posture?.adopted_episodes ?? '—'}
            </span>
            <span className="workbench-chip missing">
              autobiographical_drift={somaticHealth?.autobiographical_drift_events ?? somaticHealth?.autobiographical_posture?.autobiographical_drift_events ?? '—'}
            </span>
            <span className="workbench-chip aligned">
              ongoing_work={somaticHealth?.ongoing_work_count ?? somaticHealth?.autobiographical_posture?.ongoing_work_count ?? '—'}
            </span>
            <span className="workbench-chip aligned">
              adopted_bonds={somaticHealth?.adopted_bonds ?? somaticHealth?.social_posture?.adopted_bonds ?? '—'}
            </span>
            <span className="workbench-chip missing">
              social_drift={somaticHealth?.social_drift_events ?? somaticHealth?.social_posture?.social_drift_events ?? '—'}
            </span>
            <span className="workbench-chip aligned">
              federated_peers={somaticHealth?.federated_peer_count ?? somaticHealth?.social_posture?.federated_peer_count ?? '—'}
            </span>
            <span className="workbench-chip aligned">
              adopted_pacts={somaticHealth?.adopted_pacts ?? somaticHealth?.multi_being_posture?.adopted_pacts ?? '—'}
            </span>
            <span className="workbench-chip missing">
              multi_being_drift={somaticHealth?.multi_being_drift_events ?? somaticHealth?.multi_being_posture?.multi_being_drift_events ?? '—'}
            </span>
            <span className="workbench-chip aligned">
              cross_organism_peers={somaticHealth?.cross_organism_peer_count ?? somaticHealth?.multi_being_posture?.cross_organism_peer_count ?? '—'}
            </span>
            <span className="workbench-chip aligned">
              adopted_norms={somaticHealth?.adopted_norms ?? somaticHealth?.culture_of_beings_posture?.adopted_norms ?? '—'}
            </span>
            <span className="workbench-chip aligned">
              adopted_charters={somaticHealth?.adopted_charters ?? somaticHealth?.ecosystem_posture?.adopted_charters ?? '—'}
            </span>
            <span className="workbench-chip aligned">
              membrane_policies={somaticHealth?.adopted_membrane_policies ?? somaticHealth?.governance_membrane_posture?.adopted_policies ?? '—'}
            </span>
          </div>
        </section>
      </div>

      <h2 className="operator-console-section-title">UGR + Cloud Forge (advisory)</h2>
      <div className="operator-console-grid">
        <UGRCloudForgeConsoleCard compact meshHealth={mesh} />
        <UGRRewardsCompact rewards={operatorRewards} />

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
