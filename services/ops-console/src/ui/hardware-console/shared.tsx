import type React from 'react';

export const sectionStyle: React.CSSProperties = {
  marginBottom: 24,
  padding: 16,
  background: '#fff',
  borderRadius: 12,
  border: '1px solid #d9e0ea',
  boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)',
};

export const gridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
};

export const subtleTextStyle: React.CSSProperties = {
  color: '#5f6b7a',
};

export const buttonStyle: React.CSSProperties = {
  border: 0,
  borderRadius: 8,
  padding: '8px 12px',
  background: '#1d4ed8',
  color: '#fff',
  cursor: 'pointer',
};

export const secondaryButtonStyle: React.CSSProperties = {
  ...buttonStyle,
  background: '#334155',
};

export const metricCardStyle: React.CSSProperties = {
  border: '1px solid #e3e7ed',
  borderRadius: 6,
  padding: 12,
};

export const panelStyle: React.CSSProperties = {
  border: '1px solid #e3e7ed',
  borderRadius: 6,
  padding: 12,
};

export const barTrackStyle: React.CSSProperties = {
  height: 8,
  background: '#e8edf2',
  borderRadius: 999,
  overflow: 'hidden',
  margin: '8px 0',
};

export const barFillStyle: React.CSSProperties = {
  display: 'block',
  height: '100%',
};

export const Metric: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div style={metricCardStyle}>
    <div style={{ color: '#5f6b7a', fontSize: 12, textTransform: 'uppercase' }}>{label}</div>
    <div style={{ fontSize: 20, fontWeight: 700 }}>{value}</div>
  </div>
);

export const Panel: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div style={panelStyle}>
    <h3 style={{ marginTop: 0 }}>{title}</h3>
    {children}
  </div>
);

export function formatHardwareTemperature(value: number | null | undefined): string {
  return typeof value === 'number' ? `${value.toFixed(1)} °C` : 'n/a';
}

export function formatHardwarePercent(value: number | null | undefined): string {
  return typeof value === 'number' ? `${value.toFixed(1)}%` : 'n/a';
}
