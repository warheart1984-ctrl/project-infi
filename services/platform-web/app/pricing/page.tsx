import { PricingEvaluatorClient } from './PricingEvaluatorClient';
import Link from 'next/link';

export const metadata = {
  title: 'Sovereign Router X Pricing',
  description: 'Customer-authenticated pricing evaluator and routed-request economics dashboard',
};

export default function PricingPage() {
  return (
    <main style={pageStyle}>
      <div style={heroStyle}>
        <div style={eyebrowStyle}>Constitutional pricing evaluator</div>
        <h1 style={titleStyle}>Authenticate the customer. Route the request. Record the margin.</h1>
        <p style={ledeStyle}>
          Sovereign Router X evaluates the customer segment after login, chooses the commercial shape, routes the request through the constitutional policy layer, and writes the resulting economics into the ops-console ledger.
        </p>
        <div style={heroMetricsStyle}>
          <div style={heroMetricStyle}>
            <span style={heroMetricLabelStyle}>Model routing</span>
            <span style={heroMetricValueStyle}>Sovereign Router X</span>
          </div>
          <div style={heroMetricStyle}>
            <span style={heroMetricLabelStyle}>Ledger target</span>
            <span style={heroMetricValueStyle}>ops-console</span>
          </div>
          <div style={heroMetricStyle}>
            <span style={heroMetricLabelStyle}>Commercial logic</span>
            <span style={heroMetricValueStyle}>Subscription, usage, assurance, bundle</span>
          </div>
        </div>
        <div style={heroActionsStyle}>
          <Link href="/account" style={heroLinkStyle}>Open account workspace</Link>
          <Link href="/cep" style={heroSecondaryLinkStyle}>Open CEP artifact surface</Link>
          <Link href="/usage" style={heroSecondaryLinkStyle}>Open usage and quota</Link>
        </div>
      </div>

      <div style={contentStyle}>
        <PricingEvaluatorClient />
      </div>
    </main>
  );
}

const pageStyle: React.CSSProperties = {
  minHeight: '100vh',
  background: 'radial-gradient(circle at top left, rgba(15, 118, 110, 0.18), transparent 34%), radial-gradient(circle at top right, rgba(2, 132, 199, 0.14), transparent 30%), linear-gradient(180deg, #f8fafc 0%, #eef6f5 48%, #ffffff 100%)',
  color: '#0f172a',
  padding: '48px 24px 64px',
};

const heroStyle: React.CSSProperties = {
  maxWidth: 1240,
  margin: '0 auto 32px',
  padding: '24px 4px 8px',
};

const eyebrowStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 8,
  borderRadius: 999,
  padding: '8px 14px',
  background: 'rgba(15, 118, 110, 0.12)',
  color: '#115e59',
  fontSize: 12,
  fontWeight: 700,
  letterSpacing: '0.12em',
  textTransform: 'uppercase',
};

const titleStyle: React.CSSProperties = {
  margin: '16px 0 0',
  maxWidth: 980,
  fontSize: 'clamp(2.5rem, 5vw, 5rem)',
  lineHeight: 0.95,
  letterSpacing: '-0.06em',
};

const ledeStyle: React.CSSProperties = {
  maxWidth: 840,
  margin: '18px 0 0',
  fontSize: '1.1rem',
  lineHeight: 1.7,
  color: '#475569',
};

const heroMetricsStyle: React.CSSProperties = {
  display: 'grid',
  gap: 14,
  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
  marginTop: 28,
};

const heroMetricStyle: React.CSSProperties = {
  padding: '18px 20px',
  borderRadius: 20,
  background: 'rgba(255,255,255,0.75)',
  border: '1px solid rgba(15, 23, 42, 0.08)',
  boxShadow: '0 20px 48px rgba(15, 23, 42, 0.06)',
};

const heroMetricLabelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  color: '#64748b',
  marginBottom: 8,
};

const heroMetricValueStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 17,
  fontWeight: 700,
  color: '#0f172a',
};

const contentStyle: React.CSSProperties = {
  maxWidth: 1240,
  margin: '0 auto',
};

const heroActionsStyle: React.CSSProperties = {
  marginTop: 24,
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
