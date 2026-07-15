import React, { useEffect, useState } from 'react';

import type { ConstitutionalEvidenceGraphSummary } from '@aaes-os/aaes-governance';

type ProofSurfaceSummary = {
  identity: { id: string; name: string; type: string; version?: string };
  proofLevel: string;
  verificationStatus: string;
  replayStatus: string;
  operationalStatus: string;
  truthBoundary: string;
  currentMaturity?: string;
  commercialReadiness?: { targetTier?: string; currentReadiness?: string };
  nextRequiredEvidence?: string[];
};

type LiveProofSurfacesState = {
  status: 'loading' | 'loaded' | 'error';
  source: 'live-backend' | 'fallback-docs';
  error?: string;
  surfaces: ProofSurfaceSummary[];
  graph?: ConstitutionalEvidenceGraphSummary;
};

export function LiveProofSurfaces() {
  const [state, setState] = useState<LiveProofSurfacesState>({
    status: 'loading',
    source: 'fallback-docs',
    surfaces: [],
  });

  useEffect(() => {
    const controller = new AbortController();

    const load = async () => {
      try {
        const [catalogResponse, graphResponse] = await Promise.all([
          fetch('/proof-surfaces', {
            signal: controller.signal,
            headers: { accept: 'application/json' },
          }),
          fetch('/evidence-graph', {
            signal: controller.signal,
            headers: { accept: 'application/json' },
          }),
        ]);
        if (!catalogResponse.ok) {
          throw new Error(`request failed with ${catalogResponse.status}`);
        }

        const payload = (await catalogResponse.json()) as {
          summaries?: ProofSurfaceSummary[];
          catalog?: { surfaces?: Array<{ surface?: unknown }> };
        };

        const summaries = Array.isArray(payload.summaries)
          ? payload.summaries
          : Array.isArray(payload.catalog?.surfaces)
            ? payload.catalog.surfaces.map((entry) => entry.surface).filter(isProofSurfaceSummary)
            : [];

        const graphPayload = graphResponse.ok
          ? ((await graphResponse.json()) as { summary?: ConstitutionalEvidenceGraphSummary; graph?: { summary?: ConstitutionalEvidenceGraphSummary } })
          : null;

        setState({
          status: 'loaded',
          source: 'live-backend',
          surfaces: summaries,
          graph: graphPayload?.summary ?? graphPayload?.graph?.summary,
        });
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        setState({
          status: 'error',
          source: 'fallback-docs',
          error: error instanceof Error ? error.message : String(error),
          surfaces: [],
        });
      }
    };

    void load();
    return () => controller.abort();
  }, []);

  return (
    <section className="docs-home__card">
      <h2>Live Proof & Challenge Surfaces</h2>
      <p style={{ marginTop: 0 }}>
        The docs site tries the live <code>/proof-surfaces</code> backend first and falls back to the static docs
        model when the backend is unavailable. The surface list is meant to keep supporting and invalidating
        evidence visible together.
      </p>
      <div style={{ color: '#5f6b7a', fontSize: 13, display: 'grid', gap: 4, marginBottom: 12 }}>
        <div>Status: {state.status}</div>
        <div>Source: {state.source}</div>
        <div>Graph root: {state.graph?.rootReceiptId ?? 'fallback-docs'}</div>
        <div>Graph claims: {state.graph?.claimCount ?? 0}</div>
        {state.error ? <div>Error: {state.error}</div> : null}
      </div>
      <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
        {state.surfaces.map((surface) => (
          <article key={surface.identity.id} style={{ border: '1px solid #dfe3e8', borderRadius: 8, padding: 12 }}>
            <div style={{ color: '#5f6b7a', fontSize: 12, textTransform: 'uppercase' }}>{surface.identity.type}</div>
            <h3 style={{ margin: '6px 0' }}>{surface.identity.name}</h3>
            <div>{surface.identity.id}</div>
            <div>Proof level: {surface.proofLevel}</div>
            <div>Verification: {surface.verificationStatus}</div>
            <div>Replay: {surface.replayStatus}</div>
            <div>Operational: {surface.operationalStatus}</div>
            <div style={{ marginTop: 8, color: '#5f6b7a' }}>{surface.truthBoundary}</div>
          </article>
        ))}
      </div>
    </section>
  );
}

function isProofSurfaceSummary(value: unknown): value is ProofSurfaceSummary {
  return Boolean(
    value &&
      typeof value === 'object' &&
      'identity' in value &&
      'proofLevel' in value &&
      'verificationStatus' in value &&
      'replayStatus' in value &&
      'operationalStatus' in value,
  );
}
