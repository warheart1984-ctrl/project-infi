import {
  deriveCanonicalReplayEvidenceContract,
  validateCanonicalReplayEvidenceContract,
} from './crec.js';

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

export type ProofSurfaceArtifactType =
  | 'repository'
  | 'runtime'
  | 'specification'
  | 'implementation'
  | 'benchmark'
  | 'product-tier'
  | 'partner-certification';

export interface ProofSurfaceIdentity {
  id: string;
  name: string;
  type: ProofSurfaceArtifactType;
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

export function deriveProofLevel(surface: ProofSurface): ProofLevel {
  let highest: ProofLevel = 'P0';
  for (const claim of surface.claims) {
    const claimLevel = claim.proofLevel ?? minProofLevelForClaimType(claim.type);
    if (compareProofLevel(claimLevel, highest) > 0) {
      highest = claimLevel;
    }
  }
  for (const evidence of surface.evidence) {
    if (compareProofLevel(evidence.proofLevel, highest) > 0) {
      highest = evidence.proofLevel;
    }
  }
  return highest;
}

export function createProofSurface(surface: ProofSurface): ProofSurface {
  return structuredClone(surface);
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

  const derivedLevel = deriveProofLevel(surface);
  if (compareProofLevel(surface.proofLevel, derivedLevel) < 0) {
    issues.push(issue('proofLevel', `surface proof level ${surface.proofLevel} is below derived level ${derivedLevel}`, 'error'));
  }

  if (surface.replayStatus === 'NotAvailable' && surface.evidence.some((evidence) => evidence.replayable)) {
    issues.push(issue('replayStatus', 'replayable evidence exists but replay status is NotAvailable', 'warn'));
  }

  if (!surface.nextRequiredEvidence.length) {
    issues.push(issue('nextRequiredEvidence', 'next evidence required should be declared', 'warn'));
  }

  const crec = deriveCanonicalReplayEvidenceContract(surface);
  const crecIssues = validateCanonicalReplayEvidenceContract(crec);
  for (const crecIssue of crecIssues) {
    issues.push(crecIssue);
  }

  return {
    passed: !issues.some((entry) => entry.severity === 'error'),
    issues,
  };
}

export class ProofSurfaceRegistry {
  private readonly surfaces = new Map<string, ProofSurface>();

  publish(surface: ProofSurface): ProofSurfaceValidationResult {
    const validation = validateProofSurface(surface);
    if (validation.passed) {
      this.surfaces.set(surface.identity.id, createProofSurface(surface));
    }
    return validation;
  }

  get(identity: string): ProofSurface | undefined {
    const surface = this.surfaces.get(identity);
    return surface ? structuredClone(surface) : undefined;
  }

  list(): ProofSurface[] {
    return [...this.surfaces.values()].map((surface) => structuredClone(surface));
  }

  remove(identity: string): boolean {
    return this.surfaces.delete(identity);
  }
}
