import { useEffect, useState, type FormEvent } from 'react';

import { Editor } from './Editor';
import { AgentPanel } from './AgentPanel';
import { GovernancePanel } from './GovernancePanel';
import { LedgerPanel } from './LedgerPanel';
import { RuntimePanel } from './RuntimePanel';
import {
  DEFAULT_PROOF_SURFACE_CATALOG_URL,
  LOCAL_PROOF_SURFACE_CATALOG_URL,
  PROOF_SURFACE_CATALOG_STORAGE_KEY,
  resolveInitialProofSurfaceCatalogUrl,
  normalizeProofSurfaceCatalogUrl,
  isLocalProofSurfaceCatalogUrl,
} from '../catalogConfig';
import { loadNovaStudioProofSurfaces, type LoadedNovaStudioProofSurfaces } from '../proofSurfaces';

export function StudioApp() {
  const initialCatalogUrl = resolveInitialProofSurfaceCatalogUrl(
    typeof window === 'undefined' ? '' : window.location.search,
    typeof window === 'undefined' ? null : window.localStorage.getItem(PROOF_SURFACE_CATALOG_STORAGE_KEY),
  );
  const [activeCatalogUrl, setActiveCatalogUrl] = useState(initialCatalogUrl);
  const [catalogUrlInput, setCatalogUrlInput] = useState(initialCatalogUrl);
  const [proofSurfaceCatalog, setProofSurfaceCatalog] = useState<LoadedNovaStudioProofSurfaces | null>(null);

  useEffect(() => {
    let cancelled = false;
    void loadNovaStudioProofSurfaces(activeCatalogUrl).then((catalog) => {
      if (!cancelled) {
        setProofSurfaceCatalog(catalog);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [activeCatalogUrl]);

  const applyCatalogUrl = (nextCatalogUrl: string) => {
    const normalizedCatalogUrl = normalizeProofSurfaceCatalogUrl(nextCatalogUrl);
    setActiveCatalogUrl(normalizedCatalogUrl);
    setCatalogUrlInput(normalizedCatalogUrl);

    if (typeof window !== 'undefined') {
      window.localStorage.setItem(PROOF_SURFACE_CATALOG_STORAGE_KEY, normalizedCatalogUrl);
      const nextLocation = new URL(window.location.href);
      nextLocation.searchParams.set('catalogUrl', normalizedCatalogUrl);
      window.history.replaceState({}, '', `${nextLocation.pathname}${nextLocation.search}${nextLocation.hash}`);
    }
  };

  const handleCatalogSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    applyCatalogUrl(catalogUrlInput);
  };

  const useLocalRegistry = () => {
    applyCatalogUrl(LOCAL_PROOF_SURFACE_CATALOG_URL);
  };

  const resetToDefaultCatalog = () => {
    applyCatalogUrl(DEFAULT_PROOF_SURFACE_CATALOG_URL);
  };

  return (
    <main style={{ fontFamily: 'Inter, system-ui, sans-serif', padding: 24, background: 'linear-gradient(180deg, #f7f9fc 0%, #ffffff 30%)', color: '#102033' }}>
      <h1>Nova Studio</h1>
      <section style={{ border: '1px solid #d8dde6', borderRadius: 14, padding: 16, marginBottom: 20, background: '#ffffff', boxShadow: '0 12px 30px rgba(16, 32, 51, 0.04)' }}>
        <h2 style={{ marginTop: 0 }}>Catalog Control</h2>
        <p style={{ marginTop: 0, color: '#556070' }}>
          Point Nova Studio at any proof-surface backend with the URL, or switch back to the local registry for offline use.
        </p>
        <form onSubmit={handleCatalogSubmit} style={{ display: 'grid', gap: 12 }}>
          <label style={{ display: 'grid', gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Proof-surface catalog URL</span>
            <input
              value={catalogUrlInput}
              onChange={(event) => setCatalogUrlInput(event.target.value)}
              spellCheck={false}
              placeholder={DEFAULT_PROOF_SURFACE_CATALOG_URL}
              style={{
                border: '1px solid #b8c2cf',
                borderRadius: 10,
                padding: '10px 12px',
                fontSize: 14,
                fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
              }}
            />
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <button
              type="submit"
              style={buttonStyle}
            >
              Load catalog
            </button>
            <button
              type="button"
              onClick={useLocalRegistry}
              style={secondaryButtonStyle}
            >
              Use local registry
            </button>
            <button
              type="button"
              onClick={resetToDefaultCatalog}
              style={secondaryButtonStyle}
            >
              Reset to default
            </button>
          </div>
        </form>
        <div style={{ marginTop: 14, color: '#556070', fontSize: 13, display: 'grid', gap: 4 }}>
          <div>Active source: {proofSurfaceCatalog?.source ?? 'loading'}</div>
          <div>Active catalog: {proofSurfaceCatalog?.catalogUrl ?? activeCatalogUrl}</div>
          <div>Query string: <code>?catalogUrl=...</code> or <code>?catalogUrl=local-registry</code></div>
          {isLocalProofSurfaceCatalogUrl(activeCatalogUrl) ? (
            <div>Current mode: local registry</div>
          ) : null}
        </div>
      </section>
      <section>
        <h2>Proof Surface Registry</h2>
        <p style={{ color: '#556070', marginTop: 0 }}>
          Source: {proofSurfaceCatalog?.source ?? 'loading'} {proofSurfaceCatalog?.source ? `(${proofSurfaceCatalog.catalogUrl})` : ''}
        </p>
        {!proofSurfaceCatalog ? <p style={{ color: '#556070' }}>Loading proof surfaces...</p> : null}
        <GraphSummaryCard graph={proofSurfaceCatalog?.graph ?? null} />
        <RouterProofSurfaceHighlight surfaces={proofSurfaceCatalog?.surfaces ?? []} />
        <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
          {(proofSurfaceCatalog?.surfaces ?? []).map((surface) => (
            <ProofSurfaceCard key={surface.identity.id} surface={surface} />
          ))}
        </div>
      </section>
      <Editor />
      <AgentPanel />
      <GovernancePanel />
      <LedgerPanel />
      <RuntimePanel />
    </main>
  );
}

const buttonStyle = {
  border: '1px solid #23405f',
  borderRadius: 10,
  padding: '10px 14px',
  background: '#23405f',
  color: '#ffffff',
  fontWeight: 600,
  cursor: 'pointer',
};

const secondaryButtonStyle = {
  ...buttonStyle,
  background: '#ffffff',
  color: '#23405f',
};

function ProofSurfaceCard({ surface }: { surface: LoadedNovaStudioProofSurfaces['surfaces'][number] }) {
  return (
    <article style={{ border: '1px solid #d8dde6', borderRadius: 10, padding: 12 }}>
      <div style={{ fontSize: 12, color: '#556070', textTransform: 'uppercase' }}>{surface.identity.type}</div>
      <h3 style={{ margin: '6px 0' }}>{surface.identity.name}</h3>
      <div>{surface.identity.id}</div>
      <div>Proof level: {surface.proofLevel}</div>
      <div>CREC level: {surface.crec?.proofSurfaceLevel ?? 'unavailable'}</div>
      <div>Verification: {surface.verificationStatus}</div>
      <div>Replay: {surface.replayStatus}</div>
      <div>Operational: {surface.operationalStatus}</div>
      <div>Maturity: {surface.crec?.constitutionalMaturity ?? 'unavailable'}</div>
      <div>Commercial: {surface.crec?.commercialReadiness.currentReadiness ?? 'unavailable'}</div>
      <div style={{ marginTop: 8, color: '#556070' }}>{surface.truthBoundary}</div>
      <div style={{ marginTop: 8, fontSize: 13 }}>Next evidence: {surface.nextRequiredEvidence.join(', ')}</div>
    </article>
  );
}

function RouterProofSurfaceHighlight({ surfaces }: { surfaces: LoadedNovaStudioProofSurfaces['surfaces'] }) {
  const routerSurface = surfaces.find((surface) => surface.identity.id === '@aaes-os/sovereignx-router');
  if (!routerSurface) {
    return null;
  }

  return (
    <section style={{ border: '1px solid #9db4cc', borderRadius: 12, padding: 16, marginBottom: 16, background: 'linear-gradient(180deg, #f3f8ff 0%, #ffffff 100%)' }}>
      <h3 style={{ marginTop: 0 }}>SovereignX Router</h3>
      <p style={{ marginTop: 0, color: '#556070' }}>
        CPU governs scheduling, continuity, and policy. GPU receives only allowed workloads for matmul, attention,
        render passes, and physics.
      </p>
      <div style={{ display: 'grid', gap: 8, gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        <MiniMetric label="Proof level" value={routerSurface.proofLevel} />
        <MiniMetric label="Verification" value={routerSurface.verificationStatus} />
        <MiniMetric label="Replay" value={routerSurface.replayStatus} />
        <MiniMetric label="Operational" value={routerSurface.operationalStatus} />
      </div>
      <p style={{ marginBottom: 0, color: '#556070' }}>{routerSurface.truthBoundary}</p>
    </section>
  );
}

function GraphSummaryCard({ graph }: { graph: LoadedNovaStudioProofSurfaces['graph'] | null }) {
  return (
    <section style={{ border: '1px solid #9db4cc', borderRadius: 12, padding: 16, marginBottom: 16, background: 'linear-gradient(180deg, #eff6ff 0%, #ffffff 100%)' }}>
      <h3 style={{ marginTop: 0 }}>Constitutional Evidence Graph</h3>
      <p style={{ marginTop: 0, color: '#556070' }}>
        The release receipt now sits at the root of the graph that drives every public view.
      </p>
      <div style={{ display: 'grid', gap: 8, gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        <MiniMetric label="Graph ID" value={graph?.graphId ?? 'loading'} />
        <MiniMetric label="Root Receipt" value={graph?.rootReceiptId ?? 'loading'} />
        <MiniMetric label="Claims" value={String(graph?.claimCount ?? 0)} />
        <MiniMetric label="Unresolved" value={String(graph?.unresolvedClaims.length ?? 0)} />
      </div>
    </section>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ border: '1px solid #d8dde6', borderRadius: 10, padding: 10, background: '#ffffff' }}>
      <div style={{ fontSize: 12, color: '#556070', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontWeight: 700 }}>{value}</div>
    </div>
  );
}
