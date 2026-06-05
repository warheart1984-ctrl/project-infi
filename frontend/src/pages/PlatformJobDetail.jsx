import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { FiRefreshCw } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { getPlatformApiKey, platformGet } from '../lib/platformApi';
import './PlatformConsole.css';

function proofBadge(status) {
  const s = status || 'asserted';
  return <span className={`platform-badge platform-badge--${s}`}>{s}</span>;
}

export default function PlatformJobDetail() {
  const { jobId } = useParams();
  const [orgId, setOrgId] = useState(localStorage.getItem('platform_active_org') || 'default-org');
  const [tab, setTab] = useState('overview');
  const [job, setJob] = useState(null);
  const [graph, setGraph] = useState(null);
  const [artifacts, setArtifacts] = useState([]);
  const [attestations, setAttestations] = useState([]);
  const [federation, setFederation] = useState(null);

  const load = useCallback(async () => {
    if (!getPlatformApiKey()) return;
    try {
      const [j, g, a, att, fed] = await Promise.all([
        platformGet(`/v1/jobs/${jobId}`),
        platformGet(`/v1/jobs/${jobId}/graph?org_id=${encodeURIComponent(orgId)}`),
        platformGet(`/v1/artifacts?org_id=${encodeURIComponent(orgId)}&job_id=${encodeURIComponent(jobId)}`),
        platformGet(`/v1/jobs/${jobId}/attestations`).catch(() => ({ attestations: [] })),
        platformGet(`/v1/proof/federation/${jobId}`).catch(() => null),
      ]);
      setJob(j);
      setGraph(g);
      setArtifacts(a?.artifacts || []);
      setAttestations(att?.attestations || []);
      setFederation(fed);
    } catch (error) {
      toast.error(error?.data?.detail || error.message);
    }
  }, [jobId, orgId]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="platform-console">
      <header className="platform-console__header">
        <div>
          <Link to="/platform">← Platform</Link>
          <h1>Job {jobId}</h1>
          {job && proofBadge(job.proof_status)}
        </div>
        <div className="platform-console__header-actions">
          <Link to={`/operator/replay/platform_job/${encodeURIComponent(jobId)}`}>Replay Machine</Link>
          <button type="button" onClick={load}><FiRefreshCw /> Refresh</button>
        </div>
      </header>
      <div className="platform-console__controls">
        <input value={orgId} onChange={(e) => setOrgId(e.target.value)} placeholder="org_id" />
      </div>
      <div className="platform-tabs">
        {['overview', 'graph', 'artifacts', 'proof'].map((t) => (
          <button key={t} type="button" className={tab === t ? 'active' : ''} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>
      {tab === 'overview' && job && (
        <pre className="platform-console__pre">{JSON.stringify(job, null, 2)}</pre>
      )}
      {tab === 'graph' && graph && (
        <div className="platform-graph">
          <ul>
            {(graph.nodes || []).map((n) => (
              <li key={n.job_id}>
                <Link to={`/platform/jobs/${n.job_id}`}>{n.subsystem} · {n.kind} · {n.status}</Link>
              </li>
            ))}
          </ul>
          <p className="platform-console__meta">{(graph.edges || []).length} edges</p>
        </div>
      )}
      {tab === 'artifacts' && (
        <ul className="platform-console__list">
          {artifacts.map((ref) => (
            <li key={ref.ref_id}>{ref.logical_path} — {ref.sha256?.slice(0, 12)}</li>
          ))}
        </ul>
      )}
      {tab === 'proof' && (
        <section className="platform-console__panel">
          <p>
            Proof required: {job?.proof_required ? 'yes' : 'no'} · Quorum met:{' '}
            {federation?.quorum_met ? 'yes' : 'no'}
          </p>
          {job?.proof_required && job?.proof_status !== 'proven' && (
            <p className="platform-console__error">Signoff blocked until federation quorum is proven.</p>
          )}
          <table className="platform-table">
            <thead>
              <tr>
                <th>Runner</th>
                <th>Hash</th>
                <th>Region</th>
              </tr>
            </thead>
            <tbody>
              {attestations.map((a) => (
                <tr key={a.attestation_id}>
                  <td>{a.runner_id}</td>
                  <td>{(a.result_hash || '').slice(0, 16)}</td>
                  <td>{a.region}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
