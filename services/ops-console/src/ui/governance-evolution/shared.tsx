import type React from 'react';

export const sectionStyle: React.CSSProperties = {
  background: '#fff',
  border: '1px solid #dfe3e8',
  borderRadius: 8,
  padding: 16,
  marginBottom: 16,
};

export const gridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
  marginBottom: 12,
};

export const panelStyle: React.CSSProperties = {
  border: '1px solid #dfe3e8',
  borderRadius: 10,
  padding: 14,
  background: '#ffffff',
};

export const metricStyle: React.CSSProperties = {
  border: '1px solid #dfe3e8',
  borderRadius: 10,
  padding: 12,
  background: '#f8fafc',
};

export const subtleTextStyle: React.CSSProperties = {
  color: '#64748b',
  lineHeight: 1.6,
};

export const secondaryButtonStyle: React.CSSProperties = {
  border: '1px solid #23405f',
  borderRadius: 10,
  padding: '10px 14px',
  background: '#ffffff',
  color: '#23405f',
  fontWeight: 600,
  cursor: 'pointer',
};

export const preStyle: React.CSSProperties = {
  margin: 0,
  padding: 12,
  borderRadius: 12,
  background: '#0f172a',
  color: '#e2e8f0',
  overflowX: 'auto',
};

export const Metric: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div style={metricStyle}>
    <div style={{ fontSize: 12, fontWeight: 700, color: '#5f6b7a', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
    <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{value}</div>
  </div>
);

export const Panel: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div style={panelStyle}>
    <h3 style={{ marginTop: 0 }}>{title}</h3>
    {children}
  </div>
);
