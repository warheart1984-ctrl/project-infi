import type {
  ProofLevel,
  ProofSurface,
  ProofSurfaceCommercialReadiness,
  ProofSurfaceOperationalStatus,
  ProofSurfaceValidationIssue,
} from './proofSurface.js';

export interface CanonicalReplayEvidenceContract {
  intent: string;
  authority: string;
  evidence: string[];
  verification: string;
  compliance: string[];
  truthBoundary: string;
  replayRecord: string;
  auditTrail: string;
  failurePath: string;
  proofSurfaceLevel: ProofLevel;
  constitutionalMaturity: ProofSurfaceOperationalStatus;
  commercialReadiness: ProofSurfaceCommercialReadiness;
}

export interface ReplayVerificationReport {
  passed: boolean;
  issues: ProofSurfaceValidationIssue[];
  inspectedSurfaces: number;
  replayableSurfaces: number;
}

function hasValue(value: string | undefined | null): boolean {
  return typeof value === 'string' && value.trim().length > 0;
}

function issue(field: string, message: string, severity: ProofSurfaceValidationIssue['severity']): ProofSurfaceValidationIssue {
  return { field, message, severity };
}

export function deriveCanonicalReplayEvidenceContract(surface: ProofSurface): CanonicalReplayEvidenceContract {
  return {
    intent: surface.purpose,
    authority: surface.constitutionalProfile.authority,
    evidence: [
      ...surface.claims.map((claim) => `${claim.id}: ${claim.statement}`),
      ...surface.evidence.map((entry) => `${entry.id}: ${entry.statement}`),
    ],
    verification: surface.constitutionalProfile.verificationProcess,
    compliance: [...surface.constitutionalProfile.complianceRequirements],
    truthBoundary: surface.truthBoundary,
    replayRecord: surface.constitutionalProfile.replayPath,
    auditTrail: `Claims: ${surface.claims.length}; evidence: ${surface.evidence.length}; registry: ${surface.identity.id}`,
    failurePath: surface.constitutionalProfile.failurePath,
    proofSurfaceLevel: surface.proofLevel,
    constitutionalMaturity: surface.constitutionalProfile.currentMaturity,
    commercialReadiness: surface.commercialReadiness,
  };
}

export function validateCanonicalReplayEvidenceContract(
  contract: CanonicalReplayEvidenceContract,
): ProofSurfaceValidationIssue[] {
  const issues: ProofSurfaceValidationIssue[] = [];

  if (!hasValue(contract.intent)) {
    issues.push(issue('crec.intent', 'missing intent', 'error'));
  }
  if (!hasValue(contract.authority)) {
    issues.push(issue('crec.authority', 'missing authority', 'error'));
  }
  if (contract.evidence.length === 0 || contract.evidence.every((value) => !hasValue(value))) {
    issues.push(issue('crec.evidence', 'missing evidence', 'error'));
  }
  if (!hasValue(contract.verification)) {
    issues.push(issue('crec.verification', 'missing verification', 'error'));
  }
  if (contract.compliance.length === 0 || contract.compliance.every((value) => !hasValue(value))) {
    issues.push(issue('crec.compliance', 'missing compliance requirements', 'error'));
  }
  if (!hasValue(contract.truthBoundary)) {
    issues.push(issue('crec.truthBoundary', 'missing truth boundary', 'error'));
  }
  if (!hasValue(contract.replayRecord)) {
    issues.push(issue('crec.replayRecord', 'missing replay record', 'error'));
  }
  if (!hasValue(contract.auditTrail)) {
    issues.push(issue('crec.auditTrail', 'missing audit trail', 'error'));
  }
  if (!hasValue(contract.failurePath)) {
    issues.push(issue('crec.failurePath', 'missing failure path', 'error'));
  }
  if (!hasValue(contract.constitutionalMaturity)) {
    issues.push(issue('crec.constitutionalMaturity', 'missing constitutional maturity', 'error'));
  }
  if (!hasValue(contract.commercialReadiness.currentReadiness)) {
    issues.push(issue('crec.commercialReadiness', 'missing commercial readiness', 'error'));
  }

  return issues;
}

export function verifyReplayCoverage(surfaces: readonly ProofSurface[]): ReplayVerificationReport {
  const issues: ProofSurfaceValidationIssue[] = [];
  let replayableSurfaces = 0;

  for (const surface of surfaces) {
    const contract = deriveCanonicalReplayEvidenceContract(surface);
    issues.push(...validateCanonicalReplayEvidenceContract(contract));

    if (surface.replayStatus !== 'NotAvailable' && surface.evidence.some((entry) => entry.replayable)) {
      replayableSurfaces += 1;
      continue;
    }

    issues.push(
      issue(
        `replay.${surface.identity.id}`,
        'surface does not expose replayable evidence',
        'error',
      ),
    );
  }

  return {
    passed: !issues.some((entry) => entry.severity === 'error'),
    issues,
    inspectedSurfaces: surfaces.length,
    replayableSurfaces,
  };
}
