import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { platformGet, getPlatformApiKey } from '../lib/platformApi';
import './PlatformConsole.css';

const SUBSYSTEMS = ['', 'mechanic', 'slingshot', 'lab', 'ai_factory', 'forgekeeper'];

export default function PlatformArtifacts() {
  const [orgId, setOrgId] = useState(localStorage.getItem('platform_active_org') || 'default-org');
  const [subsystem, setSubsystem] = useState('');
  const [artifacts, setArtifacts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [lineage, setLineage] = useState(null);

  const load = useCallback(async () => {
    if (!getPlatformApiKey()) return;
    const q = new URLSearchParams({ org_id: orgId });
    if (subsystem) q.set('subsystem', subsystem);
    const resp = await platformGet(`/v1/artifacts?${q}`);
    setArtifacts(resp?.artifacts || []);
  }, [orgId, subsystem]);

  useEffect(() => {
    load();
  }, [load]);

  const showLineage = async (ref) => {
    setSelected(ref);
    const data = await platformGet(`/v1/artifacts/${ref.ref_id}/lineage?org_id=${encodeURIComponent(orgId)}`);
    setLineage(data);
  };

  return (
    <div className="platform-console">
      <header className="platform-console__header">
        <Link to="/platform">← Platform</Link>
        <h1>Artifacts</h1>
      </header>
      <div className="platform-console__controls">
        <input value={orgId} onChange={(e) => setOrgId(e.target.value)} placeholder="org_id" />
        <select value={subsystem} onChange={(e) => setSubsystem(e.target.value)}>
          {SUBSYSTEMS.map((s) => (
            <option key={s || 'all'} value={s}>{s || 'all subsystems'}</option>
          ))}
        </select>
      </div>
      <div className="platform-console__grid">
        <section className="platform-console__panel">
          <ul className="platform-console__list">
            {artifacts.map((ref) => (
              <li key={ref.ref_id}>
                <button type="button" onClick={() => showLineage(ref)}>
                  {ref.subsystem}: {ref.logical_path}
                </button>
              </li>
            ))}
          </ul>
        </section>
        <section className="platform-console__panel">
          <h3>Lineage</h3>
          {selected && <p className="platform-console__meta">Job: {selected.job_id || '—'}</p>}
          <pre className="platform-console__pre">{lineage ? JSON.stringify(lineage, null, 2) : 'Select an artifact'}</pre>
        </section>
      </div>
    </div>
  );
}
