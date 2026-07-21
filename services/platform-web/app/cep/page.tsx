import Link from 'next/link';

import { CepArtifactsClient } from './CepArtifactsClient';

export const metadata = {
  title: 'CEP Artifact Surface',
  description: 'Customer-facing artifact export and view-state mirror for CEP',
};

export default function CepPage() {
  return (
    <main style={pageStyle}>
      <div style={shellStyle}>
        <div style={heroStyle}>
          <div style={eyebrowStyle}>Customer proof surface</div>
          <h1 style={titleStyle}>See the same CEP artifact and view-state surface the ops console uses</h1>
          <p style={ledeStyle}>
            This page mirrors the exported promotion requests, replay jobs, and decisions from the ops-console CEP store, then lets the orchestrator client publish and select artifacts through the same API contract. The viewer can default to your current organization or expand to all visible orgs.
          </p>
          <div style={heroActionsStyle}>
            <Link href="/account" style={heroLinkStyle}>Back to account workspace</Link>
            <Link href="/pricing" style={heroSecondaryLinkStyle}>Open pricing evaluator</Link>
          </div>
        </div>
        <CepArtifactsClient />
      </div>
    </main>
  );
}

const pageStyle: React.CSSProperties = {
  minHeight: '100vh',
  background: 'radial-gradient(circle at top left, rgba(15, 118, 110, 0.18), transparent 28%), radial-gradient(circle at top right, rgba(2, 132, 199, 0.12), transparent 24%), linear-gradient(180deg, #f8fafc 0%, #eef6f5 44%, #ffffff 100%)',
  color: '#0f172a',
  padding: '40px 20px 64px',
};

const shellStyle: React.CSSProperties = {
  maxWidth: 1320,
  margin: '0 auto',
  display: 'grid',
  gap: 24,
};

const heroStyle: React.CSSProperties = {
  padding: '8px 4px',
};

const eyebrowStyle: React.CSSProperties = {
  display: 'inline-flex',
  padding: '8px 12px',
  borderRadius: 999,
  background: 'rgba(15, 118, 110, 0.12)',
  color: '#115e59',
  fontSize: 12,
  fontWeight: 800,
  letterSpacing: '0.12em',
  textTransform: 'uppercase',
};

const titleStyle: React.CSSProperties = {
  margin: '14px 0 0',
  fontSize: 'clamp(2.2rem, 4vw, 4.2rem)',
  lineHeight: 0.98,
  letterSpacing: '-0.06em',
};

const ledeStyle: React.CSSProperties = {
  maxWidth: 900,
  margin: '14px 0 0',
  color: '#475569',
  lineHeight: 1.7,
  fontSize: '1.05rem',
};

const heroActionsStyle: React.CSSProperties = {
  display: 'flex',
  gap: 12,
  flexWrap: 'wrap',
  marginTop: 20,
};

const heroLinkStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '12px 18px',
  borderRadius: 999,
  textDecoration: 'none',
  background: '#0f172a',
  color: '#fff',
  fontWeight: 700,
  boxShadow: '0 12px 30px rgba(15, 23, 42, 0.18)',
};

const heroSecondaryLinkStyle: React.CSSProperties = {
  ...heroLinkStyle,
  background: '#fff',
  color: '#0f172a',
  border: '1px solid #cbd5e1',
  boxShadow: 'none',
};
