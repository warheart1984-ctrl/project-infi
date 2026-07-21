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

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(value);
}
