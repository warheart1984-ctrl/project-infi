import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FiRefreshCw } from 'react-icons/fi';
import toast from 'react-hot-toast';
import {
  getPlatformApiBaseUrl,
  getPlatformApiKey,
  platformGet,
  platformPost,
  platformPut,
  setPlatformApiKey,
} from '../lib/platformApi';
import './PlatformConsole.css';

export default function PlatformConsole() {
  const [orgId, setOrgId] = useState(localStorage.getItem('platform_active_org') || 'default-org');
  const [orgs, setOrgs] = useState([]);
  const [apiKeyInput, setApiKeyInput] = useState(getPlatformApiKey());
  const [jobs, setJobs] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [audit, setAudit] = useState([]);
  const [signoffItems, setSignoffItems] = useState([]);
  const [driftJobs, setDriftJobs] = useState([]);
  const [onlineCount, setOnlineCount] = useState(0);
  const [tenantId, setTenantId] = useState('');
  const [tenantSummary, setTenantSummary] = useState(null);
  const [webhooks, setWebhooks] = useState([]);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [sovereignMode, setSovereignMode] = useState('hosted');
  const [sovereignResidency, setSovereignResidency] = useState('us');
  const [sovereignRunner, setSovereignRunner] = useState('');
  const [filterSubsystem, setFilterSubsystem] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterProof, setFilterProof] = useState('');
  const [loading, setLoading] = useState(false);

  const persistOrg = (id) => {
    setOrgId(id);
    localStorage.setItem('platform_active_org', id);
  };

  const refresh = useCallback(async () => {
    if (!getPlatformApiKey()) {
      toast.error('Set a Platform API key first.');
      return;
    }
    setLoading(true);
    try {
      const orgResp = await platformGet('/v1/orgs').catch(() => ({ orgs: [] }));
      const orgList = orgResp?.orgs || [];
      setOrgs(orgList);
      const tenants = [...new Set(orgList.map((o) => o.ugr_tenant_id).filter(Boolean))];
      if (tenants.length >= 1 && !tenantId) {
        setTenantId(tenants[0]);
      }
      if (tenantId) {
        try {
          const ts = await platformGet(`/v1/tenants/${encodeURIComponent(tenantId)}/summary`);
          setTenantSummary(ts);
        } catch {
          setTenantSummary(null);
        }
      }
      if (orgList.length === 1 && orgList[0]?.org_id) {
        persistOrg(orgList[0].org_id);
      }
      const params = new URLSearchParams({ org_id: orgId });
      if (filterSubsystem) params.set('subsystem', filterSubsystem);
      if (filterStatus) params.set('status', filterStatus);
      if (filterProof) params.set('proof_status', filterProof);
      const [jobResp, artResp, auditResp, driftResp, opsResp] = await Promise.all([
        platformGet(`/v1/jobs?${params}`),
        platformGet(`/v1/artifacts?org_id=${encodeURIComponent(orgId)}`),
        platformGet(`/v1/audit?org_id=${encodeURIComponent(orgId)}&limit=20`),
        platformGet(`/v1/orgs/${encodeURIComponent(orgId)}/drift/jobs`).catch(() => ({ jobs: [] })),
        platformGet(`/v1/orgs/${encodeURIComponent(orgId)}/mesh/operators`).catch(() => ({ operators: [] })),
      ]);
      const jobList = jobResp?.jobs || [];
      setJobs(jobList);
      setArtifacts(artResp?.artifacts || []);
      setAudit(auditResp?.events || []);
      const signoffs = jobList
        .filter((j) => {
          const meta = j.metadata?.result || {};
          return meta.launch_blocked || (meta.scan?.drifts || []).some((d) => d.ma13_class === 'II' || d.ma13_class === 'III');
        })
        .map((j) => ({ job_id: j.job_id, subsystem: j.subsystem, status: j.status, kind: j.kind }));
      setSignoffItems(signoffs);
      setDriftJobs(driftResp?.jobs || []);
      setOnlineCount((opsResp?.operators || []).length);
      const whResp = await platformGet(`/v1/orgs/${encodeURIComponent(orgId)}/webhooks`).catch(() => ({ subscriptions: [] }));
      setWebhooks(whResp?.subscriptions || []);
      const sovResp = await platformGet(`/v1/orgs/${encodeURIComponent(orgId)}/sovereign/profile`).catch(() => null);
      const sp = sovResp?.sovereign_profile || {};
      setSovereignMode(sp.mode || 'hosted');
      setSovereignResidency(sp.data_residency || 'us');
      setSovereignRunner(sp.runner_endpoint || '');
    } catch (error) {
      toast.error(error?.data?.detail || error.message || 'Platform API failed');
    } finally {
      setLoading(false);
    }
  }, [orgId, filterSubsystem, filterStatus, filterProof, tenantId]);

  useEffect(() => {
    if (getPlatformApiKey()) refresh();
  }, [refresh]);

  const saveKey = () => {
    setPlatformApiKey(apiKeyInput.trim());
    toast.success('API key saved');
    refresh();
  };

  return (
    <div className="platform-console">
      <header className="platform-console__header">
        <div>
          <Link to="/jarvis">← Jarvis</Link>
          <h1>Platform Ops</h1>
          <p className="platform-console__meta">Operators online: {onlineCount}</p>
          <p className="platform-console__meta">
            API: {getPlatformApiBaseUrl()} · <Link to="/platform/getting-started">Getting started</Link>
            {' · '}<Link to="/platform/artifacts">Artifacts</Link>
            {' · '}<Link to="/platform/assistant">Assistant</Link>
            {' · '}<Link to="/platform/workflows">Workflows</Link>
            {' · '}<Link to="/platform/mesh">Mesh</Link>
            {' · '}<Link to="/platform/marketplace">Marketplace</Link>
          </p>
        </div>
        <button type="button" onClick={refresh} disabled={loading}>
          <FiRefreshCw /> Refresh
        </button>
      </header>

      <div className="platform-console__controls">
        <input type="password" placeholder="X-Api-Key" value={apiKeyInput} onChange={(e) => setApiKeyInput(e.target.value)} />
        <button type="button" onClick={saveKey}>Save key</button>
        {[...new Set(orgs.map((o) => o.ugr_tenant_id).filter(Boolean))].length > 1 ? (
          <select value={tenantId} onChange={(e) => setTenantId(e.target.value)} aria-label="tenant">
            {[...new Set(orgs.map((o) => o.ugr_tenant_id).filter(Boolean))].map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        ) : null}
        {orgs.length > 1 ? (
          <select value={orgId} onChange={(e) => persistOrg(e.target.value)}>
            {orgs
              .filter((o) => !tenantId || o.ugr_tenant_id === tenantId)
              .map((o) => (
                <option key={o.org_id} value={o.org_id}>{o.label || o.org_id}</option>
              ))}
          </select>
        ) : (
          <input type="text" placeholder="org_id" value={orgId} onChange={(e) => persistOrg(e.target.value)} />
        )}
        <select value={filterSubsystem} onChange={(e) => setFilterSubsystem(e.target.value)}>
          <option value="">all subsystems</option>
          {['mechanic', 'slingshot', 'lab', 'ai_factory', 'forgekeeper'].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">all statuses</option>
          {['queued', 'running', 'complete', 'failed'].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select value={filterProof} onChange={(e) => setFilterProof(e.target.value)}>
          <option value="">all proof</option>
          {['asserted', 'proven', 'disputed'].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <section className="platform-console__panel">
        <h3>Webhooks</h3>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            await platformPost(`/v1/orgs/${orgId}/webhooks`, {
              url: webhookUrl,
              event_types: ['job.status', 'proof.status'],
            });
            setWebhookUrl('');
            refresh();
          }}
        >
          <input value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} placeholder="https://..." />
          <button type="submit">Add webhook</button>
        </form>
        <ul className="platform-console__list">
          {webhooks.map((w) => (
            <li key={w.subscription_id}>{w.url} — {(w.event_types || []).join(', ')}</li>
          ))}
        </ul>
      </section>

      {tenantSummary && (
        <section className="platform-console__panel">
          <h3>Tenant summary ({tenantId})</h3>
          <p>
            Orgs: {tenantSummary.org_count} · Jobs: {tenantSummary.total_jobs} · Drift open:{' '}
            {tenantSummary.drift_open} · Disputed proof: {tenantSummary.proof_disputed}
            {tenantSummary.sovereign_mode_breakdown
              ? ` · Sovereign: ${JSON.stringify(tenantSummary.sovereign_mode_breakdown)}`
              : ''}
          </p>
        </section>
      )}

      <section className="platform-console__panel">
        <h3>Sovereign runtime</h3>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            await platformPut(`/v1/orgs/${orgId}/sovereign/profile`, {
              mode: sovereignMode,
              data_residency: sovereignResidency,
              runner_endpoint: sovereignRunner,
            });
            toast.success('Sovereign profile saved');
            refresh();
          }}
        >
          <select value={sovereignMode} onChange={(e) => setSovereignMode(e.target.value)} aria-label="sovereign mode">
            <option value="hosted">hosted</option>
            <option value="self_hosted">self_hosted</option>
          </select>
          <input
            value={sovereignResidency}
            onChange={(e) => setSovereignResidency(e.target.value)}
            placeholder="data_residency (us, eu, ...)"
          />
          <input
            value={sovereignRunner}
            onChange={(e) => setSovereignRunner(e.target.value)}
            placeholder="runner_endpoint"
          />
          <button type="submit">Save profile</button>
        </form>
        <button
          type="button"
          onClick={async () => {
            const base = getPlatformApiBaseUrl().replace(/\/+$/, '');
            const key = getPlatformApiKey();
            const headers = key ? { 'X-Api-Key': key } : {};
            const resp = await fetch(`${base}/v1/orgs/${encodeURIComponent(orgId)}/sovereign/export-pack`, {
              method: 'POST',
              headers,
            });
            if (!resp.ok) {
              toast.error('Export pack failed');
              return;
            }
            const blob = await resp.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${orgId}-sovereign-pack.zip`;
            a.click();
            URL.revokeObjectURL(url);
            toast.success('Export pack downloaded');
          }}
        >
          Download export pack
        </button>
      </section>

      <div className="platform-console__grid">
        <section className="platform-console__panel platform-console__panel--wide">
          <h3>Jobs</h3>
          <table className="platform-table">
            <thead>
              <tr>
                <th>Subsystem</th>
                <th>Kind</th>
                <th>Status</th>
                <th>Proof</th>
                <th>Required</th>
                <th>Assignee</th>
                <th>ID</th>
              </tr>
            </thead>
            <tbody>
              {jobs.length === 0 && <tr><td colSpan={7}>No jobs</td></tr>}
              {jobs.map((job) => (
                <tr key={job.job_id}>
                  <td>{job.subsystem}</td>
                  <td>{job.kind}</td>
                  <td>{job.status}</td>
                  <td>{job.proof_status || 'asserted'}</td>
                  <td>{job.proof_required ? 'yes' : '—'}</td>
                  <td>{job.assignee_principal_id || '—'}</td>
                  <td><Link to={`/platform/jobs/${job.job_id}`}>{job.job_id}</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="platform-console__panel">
          <h3>Artifacts (org)</h3>
          <ul className="platform-console__list">
            {artifacts.slice(0, 15).map((ref) => (
              <li key={ref.ref_id}>{ref.subsystem}: {ref.logical_path}</li>
            ))}
          </ul>
        </section>

        <section className="platform-console__panel">
          <h3>Drift queue</h3>
          <ul className="platform-console__list">
            {driftJobs.length === 0 && <li>No drift jobs</li>}
            {driftJobs.map((j) => (
              <li key={j.job_id}>
                <Link to={`/platform/jobs/${j.job_id}`}>{j.kind} — {j.status}</Link>
              </li>
            ))}
          </ul>
        </section>

        <section className="platform-console__panel">
          <h3>Signoff queue</h3>
          <ul className="platform-console__list">
            {signoffItems.map((item) => (
              <li key={item.job_id}>
                <Link to={`/platform/jobs/${item.job_id}`}>{item.subsystem} — review</Link>
              </li>
            ))}
          </ul>
        </section>

        <section className="platform-console__panel">
          <h3>Audit</h3>
          <ul className="platform-console__list">
            {audit.map((ev, idx) => (
              <li key={`${ev.action}-${idx}`}>{ev.action}</li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
