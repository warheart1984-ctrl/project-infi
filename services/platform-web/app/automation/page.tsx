import Link from 'next/link';

import { DropboxAutomationConsole } from './DropboxAutomationConsole';

export const metadata = {
  title: 'Constitutional Operations Console',
  description: 'Local operator console for governed managed services',
};

export default function AutomationPage() {
  return (
    <main style={pageStyle}>
      <div style={heroStyle}>
        <div style={eyebrowStyle}>Local operator app</div>
        <h1 style={titleStyle}>Turn managed services into a constitutional operations platform.</h1>
        <p style={ledeStyle}>
          This console lets you inspect the Windows service, trigger governed operations, and keep receipts, evidence, and replay metadata in one place.
        </p>
        <div style={linkRowStyle}>
          <Link href="/developer" style={secondaryLinkStyle}>Developer dashboard</Link>
          <Link href="/pricing" style={secondaryLinkStyle}>Pricing surface</Link>
        </div>
      </div>

      <DropboxAutomationConsole />
    </main>
  );
}

const pageStyle: React.CSSProperties = {
  minHeight: '100vh',
  padding: '48px 24px 64px',
  color: '#0f172a',
  background: 'radial-gradient(circle at top left, rgba(2, 132, 199, 0.16), transparent 32%), radial-gradient(circle at top right, rgba(14, 165, 233, 0.12), transparent 28%), linear-gradient(180deg, #f8fbff 0%, #eef7fb 48%, #ffffff 100%)',
};

const heroStyle: React.CSSProperties = {
  maxWidth: 1240,
  margin: '0 auto 28px',
};

const eyebrowStyle: React.CSSProperties = {
  display: 'inline-flex',
  padding: '8px 12px',
  borderRadius: 999,
  background: 'rgba(2, 132, 199, 0.12)',
  color: '#075985',
  fontSize: 12,
  fontWeight: 800,
  letterSpacing: '0.12em',
  textTransform: 'uppercase',
};

const titleStyle: React.CSSProperties = {
  margin: '16px 0 0',
  maxWidth: 980,
  fontSize: 'clamp(2.6rem, 5vw, 5rem)',
  lineHeight: 0.94,
  letterSpacing: '-0.06em',
};

const ledeStyle: React.CSSProperties = {
  maxWidth: 820,
  margin: '16px 0 0',
  fontSize: '1.08rem',
  lineHeight: 1.7,
  color: '#475569',
};

const linkRowStyle: React.CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 12,
  marginTop: 22,
};

const secondaryLinkStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '12px 16px',
  borderRadius: 999,
  border: '1px solid rgba(15, 23, 42, 0.12)',
  color: '#0f172a',
  background: '#fff',
  textDecoration: 'none',
  fontWeight: 700,
};
