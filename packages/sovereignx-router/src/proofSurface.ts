export type ProofLevel = 'P0' | 'P1' | 'P2' | 'P3' | 'P4' | 'P5';

export type ProofSurfaceVerificationStatus =
  | 'Designed'
  | 'Implemented'
  | 'Build Verified'
  | 'Test Verified'
  | 'Replay Verified'
  | 'Independently Verified';

export type ProofSurfaceReplayStatus = 'NotAvailable' | 'Replayable' | 'Replayed';

export type ProofSurfaceOperationalStatus =
  | 'Scaffold'
  | 'Prototype'
  | 'Verified Prototype'
  | 'Reference Implementation'
  | 'Production Candidate'
  | 'Production';

export type ClaimType =
  | 'Aspirational'
  | 'Architectural'
  | 'Specification'
  | 'Implementation'
  | 'Verification'
  | 'Operational'
  | 'Commercial';

export interface ProofSurfaceIdentity {
  id: string;
  name: string;
  type: 'repository' | 'runtime' | 'specification' | 'implementation' | 'benchmark' | 'product-tier' | 'partner-certification';
  version?: string;
}

export interface ProofSurfaceConstitutionalProfile {
  purpose: string;
  authority: string;
  evidenceModel: string;
  verificationProcess: string;
  complianceRequirements: string[];
  truthBoundary: string;
  constitutionalScope: string;
  constitutionalLimits: string;
  dependencies: string[];
  stewardship: string;
  replayPath: string;
  failurePath: string;
  currentMaturity: ProofSurfaceOperationalStatus;
}

export interface ProofSurfaceClaim {
  id: string;
  type: ClaimType;
  statement: string;
  evidenceIds: string[];
  proofLevel?: ProofLevel;
  verificationStatus?: ProofSurfaceVerificationStatus;
  replayStatus?: ProofSurfaceReplayStatus;
  operationalStatus?: ProofSurfaceOperationalStatus;
}

export interface ProofSurfaceEvidence {
  id: string;
  statement: string;
  proofLevel: ProofLevel;
  verificationStatus: ProofSurfaceVerificationStatus;
  replayable: boolean;
  verifiedBy?: string;
  timestamp?: string;
}

export interface ProofSurfaceReadiness {
  redTeam: string;
  blueTeam: string;
  purpleTeam: string;
  greenTeam: string;
  yellowTeam: string;
  whiteTeam: string;
}

export interface ProofSurfaceCommercialReadiness {
  targetTier: string;
  intendedCustomer: string;
  primaryUseCase: string;
  valueProposition: string;
  currentReadiness: string;
  revenueState?: string;
}

export interface ProofSurface {
  identity: ProofSurfaceIdentity;
  purpose: string;
  claims: ProofSurfaceClaim[];
  evidence: ProofSurfaceEvidence[];
  verificationStatus: ProofSurfaceVerificationStatus;
  proofLevel: ProofLevel;
  replayStatus: ProofSurfaceReplayStatus;
  operationalStatus: ProofSurfaceOperationalStatus;
  truthBoundary: string;
  constitutionalProfile: ProofSurfaceConstitutionalProfile;
  blindspots: string[];
  battleScars: string[];
  adversarialClaims: string[];
  colorTeamReadiness: ProofSurfaceReadiness;
  commercialReadiness: ProofSurfaceCommercialReadiness;
  nextRequiredEvidence: string[];
}

export interface ProofSurfaceValidationIssue {
  field: string;
  message: string;
  severity: 'info' | 'warn' | 'error';
}

export interface ProofSurfaceValidationResult {
  passed: boolean;
  issues: ProofSurfaceValidationIssue[];
}

export const PROOF_SURFACE_LAW =
  'No constitutional, engineering, operational, scientific, or commercial claim may exceed the evidence presented by its Proof Surface.';

const PROOF_LEVEL_RANK: Record<ProofLevel, number> = {
  P0: 0,
  P1: 1,
  P2: 2,
  P3: 3,
  P4: 4,
  P5: 5,
};

const CLAIM_TYPE_MIN_LEVEL: Record<ClaimType, ProofLevel> = {
  Aspirational: 'P0',
  Architectural: 'P1',
  Specification: 'P1',
  Implementation: 'P1',
  Verification: 'P2',
  Operational: 'P3',
  Commercial: 'P4',
};

function compareProofLevel(left: ProofLevel, right: ProofLevel): number {
  return PROOF_LEVEL_RANK[left] - PROOF_LEVEL_RANK[right];
}

function hasValue(value: string | undefined | null): boolean {
  return typeof value === 'string' && value.trim().length > 0;
}

function issue(field: string, message: string, severity: ProofSurfaceValidationIssue['severity']): ProofSurfaceValidationIssue {
  return { field, message, severity };
}

export function minProofLevelForClaimType(type: ClaimType): ProofLevel {
  return CLAIM_TYPE_MIN_LEVEL[type];
}

export function validateProofSurface(surface: ProofSurface): ProofSurfaceValidationResult {
  const issues: ProofSurfaceValidationIssue[] = [];

  if (!hasValue(surface.identity.id)) {
    issues.push(issue('identity.id', 'missing identity id', 'error'));
  }
  if (!hasValue(surface.identity.name)) {
    issues.push(issue('identity.name', 'missing identity name', 'error'));
  }
  if (!hasValue(surface.purpose)) {
    issues.push(issue('purpose', 'missing purpose', 'error'));
  }
  if (!hasValue(surface.truthBoundary)) {
    issues.push(issue('truthBoundary', 'missing truth boundary', 'error'));
  }
  if (!hasValue(surface.constitutionalProfile.purpose)) {
    issues.push(issue('constitutionalProfile.purpose', 'missing constitutional purpose', 'error'));
  }
  if (!hasValue(surface.constitutionalProfile.authority)) {
    issues.push(issue('constitutionalProfile.authority', 'missing constitutional authority', 'error'));
  }
  if (surface.claims.length === 0) {
    issues.push(issue('claims', 'at least one claim is required', 'error'));
  }

  const evidenceById = new Map(surface.evidence.map((evidence) => [evidence.id, evidence] as const));
  for (const claim of surface.claims) {
    const expectedLevel = minProofLevelForClaimType(claim.type);
    const claimLevel = claim.proofLevel ?? expectedLevel;

    if (compareProofLevel(claimLevel, expectedLevel) < 0) {
      issues.push(issue(`claims.${claim.id}.proofLevel`, `claim proof level ${claimLevel} is below the minimum ${expectedLevel} for ${claim.type}`, 'error'));
    }

    if (claim.evidenceIds.length === 0) {
      issues.push(issue(`claims.${claim.id}.evidenceIds`, 'claim must reference supporting evidence', 'error'));
    }

    for (const evidenceId of claim.evidenceIds) {
      const evidence = evidenceById.get(evidenceId);
      if (!evidence) {
        issues.push(issue(`claims.${claim.id}.evidenceIds`, `missing evidence reference: ${evidenceId}`, 'error'));
        continue;
      }
      if (compareProofLevel(evidence.proofLevel, claimLevel) < 0) {
        issues.push(issue(`claims.${claim.id}.evidenceIds`, `evidence ${evidenceId} is below claim level ${claimLevel}`, 'error'));
      }
      if (!evidence.replayable && claim.type !== 'Aspirational') {
        issues.push(issue(`claims.${claim.id}.evidenceIds`, `evidence ${evidenceId} is not replayable`, 'warn'));
      }
    }
  }

  const derivedLevel = surface.evidence.reduce<ProofLevel>((highest, evidence) => (compareProofLevel(evidence.proofLevel, highest) > 0 ? evidence.proofLevel : highest), 'P0');
  if (compareProofLevel(surface.proofLevel, derivedLevel) < 0) {
    issues.push(issue('proofLevel', `surface proof level ${surface.proofLevel} is below derived level ${derivedLevel}`, 'error'));
  }

  if (surface.replayStatus === 'NotAvailable' && surface.evidence.some((evidence) => evidence.replayable)) {
    issues.push(issue('replayStatus', 'replayable evidence exists but replay status is NotAvailable', 'warn'));
  }

  if (!surface.nextRequiredEvidence.length) {
    issues.push(issue('nextRequiredEvidence', 'next evidence required should be declared', 'warn'));
  }

  return {
    passed: !issues.some((entry) => entry.severity === 'error'),
    issues,
  };
}

export function createProofSurface(surface: ProofSurface): ProofSurface {
  return structuredClone(surface);
}

export const sovereignxRouterProofSurface: ProofSurface = {
  identity: {
    id: 'sovereignx-router',
    name: 'SovereignX Router',
    type: 'implementation',
    version: '0.1.0',
  },
  purpose: 'Route governed compute work across CPU and GPU under CIEMS constraints.',
  claims: [
    {
      id: 'claim-router-cpu-governs-gpu',
      type: 'Architectural',
      statement: 'CPU governs scheduling, continuity, and policy while GPU receives only allowed workloads.',
      evidenceIds: ['evidence-router-tests', 'evidence-router-proof-surface'],
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayStatus: 'Replayable',
      operationalStatus: 'Verified Prototype',
    },
    {
      id: 'claim-router-ciems-policy',
      type: 'Specification',
      statement: 'CIEMS decisions can throttle, quarantine, kill, or allow governed compute tasks.',
      evidenceIds: ['evidence-ciems-tests'],
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayStatus: 'Replayable',
      operationalStatus: 'Verified Prototype',
    },
    {
      id: 'claim-router-verification',
      type: 'Verification',
      statement: 'The package includes tests that validate routing, measurement health, and evidence generation.',
      evidenceIds: ['evidence-router-tests'],
      proofLevel: 'P2',
      verificationStatus: 'Test Verified',
      replayStatus: 'Replayable',
      operationalStatus: 'Verified Prototype',
    },
    {
      id: 'claim-router-hardware-governance',
      type: 'Architectural',
      statement: 'The package models the SovereignX hardware governor as a constitutional telemetry router with promotion and retraction logic.',
      evidenceIds: ['evidence-hardware-governor-tests', 'evidence-hardware-governor-contract'],
      proofLevel: 'P2',
      verificationStatus: 'Test Verified',
      replayStatus: 'Replayable',
      operationalStatus: 'Verified Prototype',
    },
    {
      id: 'claim-router-cluster-routing',
      type: 'Architectural',
      statement: 'The package deterministically assigns governed work to the best eligible cluster node while preserving the CPU or GPU routing decision.',
      evidenceIds: ['evidence-cluster-routing-tests', 'evidence-router-tests'],
      proofLevel: 'P2',
      verificationStatus: 'Test Verified',
      replayStatus: 'Replayable',
      operationalStatus: 'Verified Prototype',
    },
  ],
  evidence: [
    {
      id: 'evidence-router-tests',
      statement: 'Vitest suite exercises CPU/GPU fallback, throttling, quarantine, and proof-surface validation.',
      proofLevel: 'P2',
      verificationStatus: 'Test Verified',
      replayable: true,
      verifiedBy: 'vitest',
    },
    {
      id: 'evidence-ciems-tests',
      statement: 'CIEMS policy brain evaluates intent registration, budgets, and measurement health deterministically.',
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayable: true,
      verifiedBy: 'vitest',
    },
    {
      id: 'evidence-router-proof-surface',
      statement: 'Proof surface artifact itself is machine-readable and validated with the local law.',
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayable: true,
      verifiedBy: 'validateProofSurface',
    },
    {
      id: 'evidence-hardware-governor-tests',
      statement: 'Hardware governor tests exercise telemetry validation, promotion/retraction bursts, and quarantine behavior.',
      proofLevel: 'P2',
      verificationStatus: 'Test Verified',
      replayable: true,
      verifiedBy: 'vitest',
    },
    {
      id: 'evidence-hardware-governor-contract',
      statement: 'The hardware governance contract is machine-readable and validated against its deterministic schema.',
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayable: true,
      verifiedBy: 'validateSovereignXHardwareGovernanceContract',
    },
    {
      id: 'evidence-cluster-routing-tests',
      statement: 'Cluster routing tests prove deterministic node selection, eligibility filtering, and delay fallbacks across multiple nodes.',
      proofLevel: 'P2',
      verificationStatus: 'Test Verified',
      replayable: true,
      verifiedBy: 'vitest',
    },
  ],
  verificationStatus: 'Implemented',
  proofLevel: 'P2',
  replayStatus: 'Replayable',
  operationalStatus: 'Verified Prototype',
  truthBoundary: 'Proves governed routing, telemetry validation, hardware promotion/retraction policy, and deterministic multi-node assignment, not production-scale membership control.',
  constitutionalProfile: {
    purpose: 'Govern CPU and GPU dispatch under constitutional constraints, including telemetry-driven hardware promotion and retraction.',
    authority: 'AAES governance law, proof-surface law, CIEMS policy contracts, and the SovereignX hardware governor contract.',
    evidenceModel: 'Routing decisions, CIEMS decisions, hardware telemetry evidence, replay records, and tests.',
    verificationProcess: 'Build, test, replay the router decisions, validate telemetry evidence, and validate the proof surface.',
    complianceRequirements: ['No claim may exceed evidence', 'CPU governs policy', 'GPU remains an accelerator', 'Telemetry must be validated before promotion'],
    truthBoundary: 'This package proves governed routing, hardware telemetry policy, and deterministic cluster assignment, not full cluster management.',
    constitutionalScope: 'Compute routing, hardware promotion/retraction, governance enforcement, measurement health, and multi-node work assignment.',
    constitutionalLimits: 'It does not claim full hardware management or live cluster membership control.',
    dependencies: ['local proof surface law'],
    stewardship: 'AAES-OS governance maintainers',
    replayPath: 'Replay the evidence log and routing decisions from the router history.',
    failurePath: 'Throttle, quarantine, delay, or drop work when invariants fail.',
    currentMaturity: 'Verified Prototype',
  },
  blindspots: [
    'No live cluster membership control yet',
    'No real GPU telemetry adapter yet',
    'No thermal sensor integration yet',
  ],
  battleScars: [
    'Router ideas can overclaim before telemetry exists',
    'Policy and acceleration layers can be confused without a proof surface',
  ],
  adversarialClaims: [
    'An attacker could claim GPU work was routed safely without evidence',
    'A stale measurement feed could be mistaken for trustworthy telemetry',
  ],
  colorTeamReadiness: {
    redTeam: 'Attack surface is bounded by explicit routing decisions and evidence records.',
    blueTeam: 'Policy decisions are logged, and live hardware telemetry now flows through the Hardware Console as constitutional evidence.',
    purpleTeam: 'Combined attack/defense tests are possible through deterministic router evaluation.',
    greenTeam: 'Build and test are expected to be stable within the workspace package.',
    yellowTeam: 'Operator messaging is clear, but the package is still a prototype.',
    whiteTeam: 'Constitutional authority is explicit and machine-readable.',
  },
  commercialReadiness: {
    targetTier: 'Builder',
    intendedCustomer: 'Developers and platform operators building governed compute runtimes.',
    primaryUseCase: 'Resource fairness and constitutional routing for agentic workloads.',
    valueProposition: 'Makes CPU policy and GPU acceleration auditable and governable.',
    currentReadiness: 'Prototype',
  },
  nextRequiredEvidence: [
    'Hardware console evidence artifacts',
    'Hardware replay artifacts',
    'Hardware benchmark artifacts',
  ],
};

export function validateSovereignXRouterProofSurface(): ProofSurfaceValidationResult {
  return validateProofSurface(sovereignxRouterProofSurface);
}

export function getSovereignXRouterProofSurfaceLaw(): string {
  return PROOF_SURFACE_LAW;
}
