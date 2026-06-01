import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { platformGet, platformPost } from '../lib/platformApi';
import './PlatformConsole.css';

const TABS = [
  { id: '', label: 'All visible' },
  { id: 'org', label: 'Org' },
  { id: 'tenant', label: 'Tenant' },
  { id: 'public', label: 'Curated' },
];

export default function PlatformMarketplace() {
  const [orgId, setOrgId] = useState(localStorage.getItem('platform_active_org') || '');
  const [tab, setTab] = useState('');
  const [listings, setListings] = useState([]);
  const [name, setName] = useState('pipeline');
  const [visibility, setVisibility] = useState('org');
  const [stepsJson, setStepsJson] = useState(
    JSON.stringify(
      [
        { subsystem: 'mechanic', kind: 'mechanic.scan' },
        { subsystem: 'slingshot', kind: 'slingshot.preload' },
        { subsystem: 'lab', kind: 'lab.session' },
      ],
      null,
      2,
    ),
  );
  const [analytics, setAnalytics] = useState(null);
  const [catalogQ, setCatalogQ] = useState('');
  const [error, setError] = useState('');

  async function load() {
    setError('');
    try {
      const q = new URLSearchParams({ org_id: orgId });
      if (tab) q.set('visibility', tab);
      const data = await platformGet(`/v1/marketplace/listings?${q}`);
      setListings(data.listings || []);
      const a = await platformGet(`/v1/orgs/${orgId}/marketplace/analytics`);
      setAnalytics(a);
    } catch (err) {
      setError(err.message);
    }
  }

  async function publish(e) {
    e.preventDefault();
    try {
      const steps = JSON.parse(stepsJson);
      await platformPost(`/v1/orgs/${orgId}/marketplace/listings`, {
        org_id: orgId,
        name,
        visibility,
        curated: visibility === 'public',
        steps,
      });
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function install(listingId) {
    await platformPost(`/v1/marketplace/listings/${listingId}/install?org_id=${encodeURIComponent(orgId)}`, {});
    load();
  }

  async function runListing(listingId) {
    const data = await platformPost(`/v1/marketplace/listings/${listingId}/run?org_id=${encodeURIComponent(orgId)}`, {});
    const jid = data.workflow_run?.job_id;
    if (jid) window.location.href = `/platform/jobs/${jid}?org_id=${orgId}`;
  }

  return (
    <div className="platform-console page-shell">
      <header className="platform-console__header">
        <h1>Workflow Marketplace</h1>
        <p className="platform-console__subtitle">Listings, approval lifecycle, and analytics (v23–v24).</p>
        <nav className="platform-console__nav">
          <Link to="/platform">Console</Link>
          <Link to="/platform/workflows">Workflows</Link>
          <Link to="/platform/mesh">Mesh</Link>
        </nav>
      </header>
      <div className="platform-console__controls">
        <input value={orgId} onChange={(e) => setOrgId(e.target.value)} placeholder="org_id" />
        {TABS.map((t) => (
          <button key={t.id} type="button" className={tab === t.id ? 'active' : ''} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
        <input value={catalogQ} onChange={(e) => setCatalogQ(e.target.value)} placeholder="catalog search" />
        <button
          type="button"
          onClick={async () => {
            const data = await platformGet(
              `/v1/marketplace/catalog?org_id=${encodeURIComponent(orgId)}&q=${encodeURIComponent(catalogQ)}`,
            );
            setListings(data.listings || []);
          }}
        >
          Search catalog
        </button>
        <button type="button" onClick={load}>Load</button>
      </div>
      {error && <p className="platform-console__error">{error}</p>}
      {analytics && (
        <section className="platform-console__panel">
          <h2>Analytics</h2>
          <p>
          Installs: {analytics.marketplace_installs} · Runs: {analytics.workflow_runs_from_listing}
          {analytics.review_count != null && ` · Reviews: ${analytics.review_count} (avg ${analytics.average_rating})`}
        </p>
        </section>
      )}
      <form className="platform-console__form" onSubmit={publish}>
        <h2>Publish listing</h2>
        <input value={name} onChange={(e) => setName(e.target.value)} />
        <select value={visibility} onChange={(e) => setVisibility(e.target.value)}>
          <option value="org">org</option>
          <option value="tenant">tenant</option>
          <option value="public">public (curated, admin)</option>
        </select>
        <textarea value={stepsJson} onChange={(e) => setStepsJson(e.target.value)} rows={6} />
        <button type="submit">Publish</button>
      </form>
      <section className="platform-console__panel">
        <h2>Listings</h2>
        <ul>
          {listings.map((l) => (
            <li key={l.listing_id}>
              {l.name} ({l.visibility}) v{l.semver}{' '}
              <span className="platform-badge">{l.approval_status || 'published'}</span>{' '}
              <button type="button" onClick={() => install(l.listing_id)}>Install</button>
              <button type="button" onClick={() => runListing(l.listing_id)}>Run</button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
