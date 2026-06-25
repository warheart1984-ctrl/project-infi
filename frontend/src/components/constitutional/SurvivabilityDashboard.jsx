import React, { useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { FiAlertTriangle, FiCheckCircle, FiRefreshCw, FiShield } from 'react-icons/fi';
import { getApiErrorMessage } from '../lib/api';
import {
  fetchSurvivabilityDashboard,
  formatScore,
  zoneTone,
} from '../lib/survivabilityApi';
import '../styles/constitutional/survivability.css';

function ZoneBadge({ zone }) {
  const tone = zoneTone(zone);
  return <span className={`surv-zone surv-zone--${tone}`}>{zone || '—'}</span>;
}

function MetricCard({ label, value, zone, invert = false }) {
  const display = invert ? formatScore(value) : formatScore(value);
  return (
    <div className={`surv-metric surv-metric--${zoneTone(zone)}`}>
      <div className="surv-metric-label">{label}</div>
      <div className="surv-metric-value">{display}</div>
      <ZoneBadge zone={zone} />
    </div>
  );
}

function ChecklistSection({ title, items }) {
  const entries = Object.entries(items || {});
  const passed = entries.filter(([, ok]) => ok).length;
  return (
    <section className="constitutional-panel surv-checklist-section">
      <header className="surv-checklist-header">
        <h3>{title}</h3>
        <span className="constitutional-muted">
          {passed}/{entries.length} pass
        </span>
      </header>
      <ul className="surv-checklist">
        {entries.map(([key, ok]) => (
          <li key={key} className={ok ? 'surv-checklist-pass' : 'surv-checklist-fail'}>
            {ok ? <FiCheckCircle aria-hidden /> : <FiAlertTriangle aria-hidden />}
            <span>{key.replace(/_/g, ' ')}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function AmendmentPanel({ markdown, record, complete }) {
  if (!markdown && !record) {
    return (
      <section className="constitutional-panel">
        <h3>Survivability Amendment</h3>
        <p className="constitutional-muted">No open survivability remediation amendment.</p>
      </section>
    );
  }
  return (
    <section className="constitutional-panel surv-amendment">
      <header className="surv-amendment-header">
        <h3>UGR-AMENDMENT-S-SURVIVABILITY-v0</h3>
        <span className={`surv-amendment-status ${complete ? 'surv-amendment-status--ok' : 'surv-amendment-status--open'}`}>
          {complete ? 'Criteria met' : record?.status || 'open'}
        </span>
      </header>
      {record?.triggers?.length ? (
        <div className="surv-triggers">
          {record.triggers.map((trigger) => (
            <span key={trigger} className="surv-trigger-pill">{trigger}</span>
          ))}
        </div>
      ) : null}
      <pre className="surv-amendment-markdown">{markdown}</pre>
    </section>
  );
}

export function SurvivabilityDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (refresh = false) => {
    if (refresh) setRefreshing(true);
    else setLoading(true);
    try {
      const payload = await fetchSurvivabilityDashboard({ refresh });
      setData(payload);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Failed to load survivability dashboard.'));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load(false);
  }, [load]);

  if (loading && !data) {
    return <div className="constitutional-panel">Loading survivability dashboard…</div>;
  }

  if (!data) {
    return <div className="constitutional-panel">Survivability dashboard unavailable.</div>;
  }

  const dashboard = data.dashboard || {};
  const zones = data.zones || {};
  const articleS1 = data.article_s1 || {};
  const succession = data.succession || {};
  const governance = data.governance || {};
  const checklist = data.checklist || {};

  return (
    <div className="surv-dashboard">
      <section className="constitutional-panel surv-hero">
        <div className="surv-hero-top">
          <div>
            <h2>
              <FiShield aria-hidden /> Survivability Dashboard
            </h2>
            <p className="constitutional-muted">
              Article S constitutional cockpit — survivability, steward independence, founder dependency,
              and Article S-2 succession readiness.
            </p>
          </div>
          <button
            type="button"
            className="constitutional-btn constitutional-btn-primary"
            disabled={refreshing}
            onClick={() => load(true)}
          >
            <FiRefreshCw aria-hidden className={refreshing ? 'surv-spin' : ''} />
            {refreshing ? 'Refreshing…' : 'Refresh snapshot'}
          </button>
        </div>
        <div className="surv-meta">
          <span>Snapshot v{dashboard.version ?? '—'}</span>
          <span>{dashboard.snapshot_at ? new Date(dashboard.snapshot_at).toLocaleString() : '—'}</span>
          <span className={articleS1.compliant ? 'surv-ok' : 'surv-breach'}>
            {articleS1.compliant ? 'Constitutionally compliant' : 'Constitutional breach'}
          </span>
          <span className={governance.allow ? 'surv-ok' : 'surv-breach'}>
            Governance: {governance.level || '—'}
          </span>
        </div>
        {!articleS1.compliant && articleS1.breach_reasons?.length ? (
          <p className="constitutional-warning">
            Breach: {articleS1.breach_reasons.join(', ')}
          </p>
        ) : null}
      </section>

      <div className="surv-metrics-grid">
        <MetricCard
          label="System Survivability"
          value={dashboard.system_survivability_score}
          zone={zones.system_survivability_score}
        />
        <MetricCard
          label="Steward Independence"
          value={dashboard.steward_independence_score}
          zone={zones.steward_independence_score}
        />
        <MetricCard
          label="Founder Dependency"
          value={dashboard.founder_dependency_index}
          zone={zones.founder_dependency_index}
        />
        <MetricCard
          label="Reconstructability Fitness"
          value={dashboard.reconstructability_fitness_score}
          zone={zones.reconstructability_fitness_score}
        />
        <MetricCard
          label="Succession Readiness"
          value={articleS1.succession_readiness_score}
          zone={zones.succession_readiness_score}
        />
        <MetricCard
          label="Cold-Start Assumptions"
          value={dashboard.implicit_assumptions_required}
          zone={zones.cold_start_steward_assumptions}
        />
        <MetricCard
          label="Active R-F Threats"
          value={(dashboard.active_threats || []).length}
          zone={zones.active_rf_threat_surfaces}
        />
        <MetricCard
          label="Constitutional Debt"
          value={dashboard.constitutional_debt_score}
          zone="yellow"
        />
      </div>

      <section className="constitutional-panel surv-s2">
        <h3>Article S-2 — Succession Protocol</h3>
        <div className="surv-s2-grid">
          <div>
            <strong>Ready</strong>
            <p>{succession.ready ? 'Yes' : 'No'}</p>
          </div>
          <div>
            <strong>Blocked</strong>
            <p>{succession.blocked ? 'Yes' : 'No'}</p>
          </div>
          <div>
            <strong>Mandatory succession</strong>
            <p>{succession.mandatory_succession_required ? 'Triggered' : 'Not required'}</p>
          </div>
          <div>
            <strong>High-founder cycles</strong>
            <p>{succession.consecutive_high_founder_cycles ?? 0}</p>
          </div>
        </div>
        {succession.block_reasons?.length ? (
          <p className="constitutional-warning">
            Block reasons: {succession.block_reasons.join(', ')}
          </p>
        ) : null}
        {succession.process ? (
          <p className="constitutional-muted">
            Open succession process since {new Date(succession.process.opened_at).toLocaleString()}
          </p>
        ) : null}
      </section>

      <div className="surv-checklist-grid">
        <ChecklistSection title="Reconstructability" items={checklist.reconstructability} />
        <ChecklistSection title="Steward Capability" items={checklist.steward_capability} />
        <ChecklistSection title="Authority Transfer" items={checklist.authority_transfer} />
        <ChecklistSection title="Knowledge Transfer" items={checklist.knowledge_transfer} />
        <ChecklistSection title="Constitutional Health" items={checklist.constitutional_health} />
      </div>

      <AmendmentPanel
        markdown={data.amendment_template_markdown}
        record={data.survivability_amendment}
        complete={data.amendment_complete}
      />

      {(dashboard.active_threats || []).length ? (
        <section className="constitutional-panel">
          <h3>Active R-F Threat Surfaces</h3>
          <ul className="surv-threat-list">
            {dashboard.active_threats.map((threat) => (
              <li key={threat}>{threat}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
