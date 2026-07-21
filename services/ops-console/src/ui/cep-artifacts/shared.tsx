import type React from 'react';

export type CepTrustBand = 'low' | 'medium' | 'high';
export type CepTrustGovernanceLevel = 'basic' | 'enhanced' | 'full';
export type CepArtifactKind = 'promotion-request' | 'replay-job' | 'decision';

export type CepTrustPacket = {
  relationshipId?: string;
  revision?: number;
  subjectId?: string;
  objectId?: string;
  relationshipKind?: string;
  governanceLevel?: CepTrustGovernanceLevel;
  authorityChain?: string[];
  evidenceIds?: string[];
  score: number;
  band: CepTrustBand;
  authority?: {
    stewardId?: string;
    consentArtifactIds?: string[];
    delegationChainIds?: string[];
  };
  provenance?: {
    originSystem?: string;
    originActorId?: string;
    method?: string;
    createdAt?: string;
    standardsTraceabilityIds?: string[];
  };
  ledgerEntryId?: string;
  receiptId?: string;
  capturedAt?: string;
};

export type CepTrustPolicy = {
  governanceLevel: CepTrustGovernanceLevel;
  minTrustScore: number;
  minTrustBand?: CepTrustBand;
  preferHighTrustBand?: boolean;
};

export type CepTrustSummary = {
  available: boolean;
  trustedCount: number;
  untrustedCount: number;
  lowCount: number;
  mediumCount: number;
  highCount: number;
  averageTrustScore: number | null;
  governanceLevels: Record<CepTrustGovernanceLevel, number>;
};

export type CepArtifactFilters = {
  trustBand: CepTrustBand | null;
  minTrustScore: number | null;
  governanceLevel: CepTrustGovernanceLevel | null;
  includeUntrusted: boolean;
};

export type CepArtifactRecord = {
  id: string;
  kind: CepArtifactKind;
  title: string;
  source: string;
  relatedArtifactId?: string;
  recordedAt: string;
  payload: unknown;
  trust?: CepTrustPacket | null;
  trustPolicy?: CepTrustPolicy | null;
};

export type CepArtifactExport = {
  storePath: string;
  entryCount: number;
  countsByKind: Record<CepArtifactKind, number>;
  records: CepArtifactRecord[];
  recentRecords: CepArtifactRecord[];
  trustFilters?: CepArtifactFilters;
  trustSummary?: CepTrustSummary;
  viewState: {
    selectedKind: CepArtifactKind;
    selectedArtifactId: string | null;
    updatedAt: string;
    source: 'local' | 'remote';
  };
};

export interface CepRouteDecisionArtifact {
  decisionId: string;
  requestId: string;
  trustScore: number;
  trustBand: string;
  governanceResult: string;
  summary: string;
  payload: unknown;
}

export interface CepMetricProps {
  label: string;
  value: string;
}

export const sectionStyle: React.CSSProperties = {
  background: '#fff',
  border: '1px solid #dfe3e8',
  borderRadius: 8,
  padding: 16,
  marginBottom: 16,
};

export const gridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
  gap: 12,
  marginBottom: 16,
};

export const metricGridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
  gap: 12,
};

export const trustFilterStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
  alignItems: 'end',
  margin: '16px 0',
};

export const trustFieldStyle: React.CSSProperties = {
  display: 'grid',
  gap: 6,
};

export const trustLabelStyle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 600,
  color: '#1f2937',
};

export const trustInputStyle: React.CSSProperties = {
  border: '1px solid #b8c2cf',
  borderRadius: 10,
  padding: '10px 12px',
  fontSize: 14,
  background: '#fff',
  color: '#172026',
};

export const buttonStyle: React.CSSProperties = {
  border: '1px solid #23405f',
  borderRadius: 10,
  padding: '10px 14px',
  background: '#23405f',
  color: '#ffffff',
  fontWeight: 600,
  cursor: 'pointer',
};

export const secondaryButtonStyle: React.CSSProperties = {
  ...buttonStyle,
  background: '#ffffff',
  color: '#23405f',
};

export const panelStyle: React.CSSProperties = {
  background: '#f9fbfd',
  border: '1px solid #dfe3e8',
  borderRadius: 10,
  padding: 14,
};

export const subtleTextStyle: React.CSSProperties = {
  color: '#5f6b7a',
};

export const preStyle: React.CSSProperties = {
  margin: 0,
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
};

export function formatTrustScore(value: number | null): string {
  return value === null ? 'n/a' : value.toFixed(2);
}

export function extractRouteDecisionArtifact(payload: unknown): CepRouteDecisionArtifact | null {
  if (!payload || typeof payload !== 'object') {
    return null;
  }

  const record = payload as Record<string, unknown>;
  const routeDecisionArtifact = (record.routeDecisionArtifact ?? record.artifact ?? record) as Record<string, unknown>;
  if (!routeDecisionArtifact || typeof routeDecisionArtifact !== 'object' || !('trustPacket' in routeDecisionArtifact)) {
    return null;
  }

  const trustPacket = routeDecisionArtifact.trustPacket as Record<string, unknown> | undefined;
  const governance = routeDecisionArtifact.governance as Record<string, unknown> | undefined;
  const trust = trustPacket?.trust as Record<string, unknown> | undefined;
  const trustScore = typeof trust?.score === 'number' ? trust.score : 0;
  const trustBand = typeof trust?.band === 'string' ? trust.band : 'unknown';
  const governanceResult = typeof governance?.result === 'string' ? governance.result : 'unknown';

  return {
    decisionId: String(routeDecisionArtifact.artifactId ?? routeDecisionArtifact.decisionId ?? 'unknown'),
    requestId: String(routeDecisionArtifact.requestId ?? 'unknown'),
    trustScore,
    trustBand,
    governanceResult,
    summary: 'Router X produced a signed, governance-gated route decision artifact that can be replayed and audited from the same trust packet.',
    payload: routeDecisionArtifact,
  };
}

export const Metric: React.FC<CepMetricProps> = ({ label, value }) => (
  <div style={{ border: '1px solid #dfe3e8', borderRadius: 10, padding: 12, background: '#ffffff' }}>
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
