import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { platformGet, platformPost, platformPut } from '../lib/platformApi';
import './PlatformConsole.css';

export default function PlatformMesh() {
  const [orgId, setOrgId] = useState(localStorage.getItem('platform_active_org') || '');
  const [onCallIds, setOnCallIds] = useState('oncall-1,oncall-2');
  const [handoffTo, setHandoffTo] = useState('');
  const [handoffNotes, setHandoffNotes] = useState('');
  const [currentOnCall, setCurrentOnCall] = useState(null);
  const [lastHandoff, setLastHandoff] = useState(null);
  const [operators, setOperators] = useState([]);
  const [liveEvents, setLiveEvents] = useState([]);
  const [retentionDays, setRetentionDays] = useState('30');
  const [error, setError] = useState('');
  const eventSourceRef = useRef(null);

  async function refresh() {
    setError('');
    try {
      await platformPost(`/v1/orgs/${orgId}/mesh/presence`, { status: 'online' });
      const ops = await platformGet(`/v1/orgs/${orgId}/mesh/operators`);
      setOperators(ops.operators || []);
      const oc = await platformGet(`/v1/orgs/${orgId}/on-call/current`);
      setCurrentOnCall(oc.principal_id);
    } catch (err) {
      setError(err.message);
    }
  }

  async function saveOnCall(e) {
    e.preventDefault();
    const ids = onCallIds.split(',').map((s) => s.trim()).filter(Boolean);
    await platformPut(`/v1/orgs/${orgId}/on-call`, { principal_ids: ids });
    refresh();
  }

  async function doHandoff(e) {
    e.preventDefault();
    const data = await platformPost(`/v1/orgs/${orgId}/mesh/handoff`, {
      to_principal_id: handoffTo,
      notes: handoffNotes,
      runbook_ref: 'docs/subsystems/platform/OPERATIONAL_RUNBOOK.md',
    });
    setLastHandoff(data);
  }

  useEffect(() => {
    if (!orgId) return undefined;
    const base = import.meta.env.VITE_PLATFORM_API_URL || '';
    const key = localStorage.getItem('platform_api_key') || '';
    const url = `${base}/v1/orgs/${encodeURIComponent(orgId)}/mesh/events/stream`;
    try {
      const es = new EventSource(url, { withCredentials: false });
      eventSourceRef.current = es;
      es.onmessage = (ev) => {
        try {
          const parsed = JSON.parse(ev.data);
          setLiveEvents((prev) => [parsed, ...prev].slice(0, 30));
        } catch {
          /* ignore parse errors */
        }
      };
      return () => {
        es.close();
        eventSourceRef.current = null;
      };
    } catch {
      const t = setInterval(async () => {
        try {
          const data = await platformGet(`/v1/orgs/${orgId}/mesh/events?limit=10`);
          setLiveEvents(data.events || []);
        } catch {
          /* polling fallback */
        }
      }, 3000);
      return () => clearInterval(t);
    }
  }, [orgId]);

  return (
    <div className="platform-console page-shell">
      <header className="platform-console__header">
        <h1>Operator Mesh</h1>
        <p className="platform-console__subtitle">Presence, on-call, handoff, and live mesh events (v21).</p>
        <nav className="platform-console__nav">
          <Link to="/platform">Console</Link>
          <Link to="/platform/marketplace">Marketplace</Link>
        </nav>
      </header>
      <div className="platform-console__controls">
        <input value={orgId} onChange={(e) => setOrgId(e.target.value)} placeholder="org_id" />
        <input value={retentionDays} onChange={(e) => setRetentionDays(e.target.value)} placeholder="retention days" />
        <button
          type="button"
          onClick={async () => {
            const pol = await platformGet(`/v1/orgs/${orgId}/mesh/policy`);
            const meshPolicy = { ...(pol.mesh_policy || {}), event_retention_days: Number(retentionDays) || 30 };
            await platformPut(`/v1/orgs/${orgId}/mesh/policy`, meshPolicy);
            await platformPost(`/v1/orgs/${orgId}/mesh/compact`, {});
          }}
        >
          Save retention &amp; compact
        </button>
        <button type="button" onClick={refresh}>Refresh</button>
      </div>
      {error && <p className="platform-console__error">{error}</p>}
      <section className="platform-console__panel">
        <h2>Live mesh events ({liveEvents.length})</h2>
        <ul>
          {liveEvents.map((ev) => (
            <li key={ev.event_id || `${ev.event_type}-${ev.created_at}`}>
              {ev.event_type} — {ev.actor_principal_id || '—'}
            </li>
          ))}
        </ul>
      </section>
      <section className="platform-console__panel">
        <h2>Online operators ({operators.length})</h2>
        <ul>
          {operators.map((o) => (
            <li key={o.principal_id}>{o.principal_id} — {o.status}</li>
          ))}
        </ul>
        <p>Current on-call: {currentOnCall || '—'}</p>
      </section>
      <form className="platform-console__form" onSubmit={saveOnCall}>
        <h2>On-call rotation</h2>
        <input value={onCallIds} onChange={(e) => setOnCallIds(e.target.value)} placeholder="principal ids, comma-separated" />
        <button type="submit">Save on-call</button>
      </form>
      <form className="platform-console__form" onSubmit={doHandoff}>
        <h2>Handoff</h2>
        <input value={handoffTo} onChange={(e) => setHandoffTo(e.target.value)} placeholder="to principal id" required />
        <textarea value={handoffNotes} onChange={(e) => setHandoffNotes(e.target.value)} rows={2} placeholder="notes" />
        <button type="submit">Create handoff bundle</button>
      </form>
      {lastHandoff && (
        <pre className="platform-console__panel">{JSON.stringify(lastHandoff, null, 2)}</pre>
      )}
    </div>
  );
}
