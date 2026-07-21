import { describe, expect, it } from 'vitest';

import { createDemoProofSurfaceRegistry, listProofSurfaceSummaries } from './proofSurfaceCatalog.js';
import {
  PROOF_SURFACE_LAW,
  ProofSurfaceRegistry,
  deriveProofLevel,
  minProofLevelForClaimType,
  validateProofSurface,
  type ProofSurface,
} from './proofSurface.js';
import { deriveCanonicalReplayEvidenceContract, validateCanonicalReplayEvidenceContract, verifyReplayCoverage } from './crec.js';

function buildSurface(overrides: Partial<ProofSurface> = {}): ProofSurface {
  return {
    identity: {
      id: 'repo:example',
      name: 'Example Repository',
      type: 'repository',
    },
    purpose: 'Expose a governed proof surface for claims and evidence.',
    claims: [
      {
        id: 'claim-1',
        type: 'Implementation',
        statement: 'The repository implements a governed proof-surface API.',
        evidenceIds: ['evidence-1'],
        proofLevel: 'P1',
      },
      {
        id: 'claim-2',
        type: 'Verification',
        statement: 'The API is covered by validation tests.',
        evidenceIds: ['evidence-2'],
        proofLevel: 'P2',
      },
    ],
    evidence: [
      {
        id: 'evidence-1',
        statement: 'Source code exists for the API.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
      },
      {
        id: 'evidence-2',
        statement: 'A passing test suite validates the API.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
      },
    ],
    verificationStatus: 'Test Verified',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Prototype',
    truthBoundary: 'This surface proves a local governed API, not production deployment.',
    constitutionalProfile: {
      purpose: 'Governed proof-surface publication and inspection.',
      authority: 'AAES governance packages and the proof-surface law.',
      evidenceModel: 'Claims, evidence, and replayable validation results.',
      verificationProcess: 'Build, test, replay, and independent inspection where available.',
      complianceRequirements: ['No claim beyond evidence', 'Every claim references supporting evidence'],
      truthBoundary: 'The surface does not claim unsupported production readiness.',
      constitutionalScope: 'Repository-level proof-surface publication.',
      constitutionalLimits: 'Does not replace runtime-specific evidence or independent audits.',
      dependencies: ['aaes-governance', 'runledger'],
      stewardship: 'Governance maintainers.',
      replayPath: 'Replay from stored proof-surface records and validation output.',
      failurePath: 'Reject unsupported claims and require stronger evidence before publication.',
      currentMaturity: 'Prototype',
    },
    blindspots: ['Independent verification is not yet universal.'],
    battleScars: ['Docs once raced ahead of machine-readable evidence.'],
    adversarialClaims: ['A README can be mistaken for proof.'],
    colorTeamReadiness: {
      redTeam: 'Attack surface exists where claims outrun evidence.',
      blueTeam: 'Validation catches unsupported claims.',
      purpleTeam: 'Claim/evidence reconciliation is possible.',
      greenTeam: 'Build and test output can be consumed deterministically.',
      yellowTeam: 'Truth boundaries are explicit.',
      whiteTeam: 'Authority chain is documented.',
    },
    commercialReadiness: {
      targetTier: 'Builder',
      intendedCustomer: 'Developers and governance teams',
      primaryUseCase: 'Evidence-backed claim publication',
      valueProposition: 'Makes readiness machine-readable and auditable.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['Publish the registry API to downstream dashboards.'],
    ...overrides,
  };
}

describe('ProofSurface', () => {
  it('validates a supported surface', () => {
    const surface = buildSurface();
    const result = validateProofSurface(surface);

    expect(result.passed).toBe(true);
    expect(result.issues.filter((issue) => issue.severity === 'error')).toHaveLength(0);
  });

  it('derives the highest proof level from claims and evidence', () => {
    const surface = buildSurface();

    expect(deriveProofLevel(surface)).toBe('P2');
    expect(minProofLevelForClaimType('Commercial')).toBe('P4');
  });

  it('rejects claims that exceed their evidence', () => {
    const surface = buildSurface({
      claims: [
        {
          id: 'claim-1',
          type: 'Commercial',
          statement: 'This repository is commercially available.',
          evidenceIds: ['evidence-1'],
          proofLevel: 'P4',
        },
      ],
      proofLevel: 'P4',
    });

    const result = validateProofSurface(surface);

    expect(result.passed).toBe(false);
    expect(result.issues.some((issue) => issue.field.includes('evidenceIds'))).toBe(true);
  });

  it('publishes validated surfaces into the registry', () => {
    const registry = new ProofSurfaceRegistry();
    const surface = buildSurface();

    const result = registry.publish(surface);

    expect(result.passed).toBe(true);
    expect(registry.get(surface.identity.id)).toEqual(surface);
    expect(PROOF_SURFACE_LAW).toContain('No constitutional, engineering, operational, scientific, or commercial claim may exceed');
  });

  it('includes the governed runtime surface in the demo registry', () => {
    const registry = createDemoProofSurfaceRegistry();

    expect(registry.get('@aaes-os/ucr-runtime')).toBeDefined();
    expect(listProofSurfaceSummaries(registry).some((surface) => surface.identity.id === '@aaes-os/ucr-runtime')).toBe(true);
  });

  it('includes the CIS standards hierarchy surface in the demo registry', () => {
    const registry = createDemoProofSurfaceRegistry();

    expect(registry.get('@cis-core/standards-hierarchy')).toBeDefined();
    expect(listProofSurfaceSummaries(registry).some((surface) => surface.identity.id === '@cis-core/standards-hierarchy')).toBe(true);
  });

  it('includes the CIS standards traceability matrix surface in the demo registry', () => {
    const registry = createDemoProofSurfaceRegistry();

    expect(registry.get('@cis-core/standards-traceability-matrix')).toBeDefined();
    expect(listProofSurfaceSummaries(registry).some((surface) => surface.identity.id === '@cis-core/standards-traceability-matrix')).toBe(true);
  });

  it('includes the CIS companion spec registry surface in the demo registry', () => {
    const registry = createDemoProofSurfaceRegistry();

    expect(registry.get('@cis-core/companion-spec-registry')).toBeDefined();
    expect(listProofSurfaceSummaries(registry).some((surface) => surface.identity.id === '@cis-core/companion-spec-registry')).toBe(true);
  });

  it('includes the artifact governance surface in the demo registry', () => {
    const registry = createDemoProofSurfaceRegistry();

    expect(registry.get('@cis-core/artifact-governance')).toBeDefined();
    expect(listProofSurfaceSummaries(registry).some((surface) => surface.identity.id === '@cis-core/artifact-governance')).toBe(true);
  });

  it('includes the sovereign router pricing surface in the demo registry', () => {
    const registry = createDemoProofSurfaceRegistry();

    expect(registry.get('@cis-core/sovereign-router-pricing')).toBeDefined();
    expect(listProofSurfaceSummaries(registry).some((surface) => surface.identity.id === '@cis-core/sovereign-router-pricing')).toBe(true);
  });

  it('includes the external standards mapping surface in the demo registry', () => {
    const registry = createDemoProofSurfaceRegistry();

    expect(registry.get('@cis-core/external-standards-mapping')).toBeDefined();
    expect(listProofSurfaceSummaries(registry).some((surface) => surface.identity.id === '@cis-core/external-standards-mapping')).toBe(true);
  });

  it('includes the conformance generation surface in the demo registry', () => {
    const registry = createDemoProofSurfaceRegistry();

    expect(registry.get('@cis-core/conformance-generation')).toBeDefined();
    expect(listProofSurfaceSummaries(registry).some((surface) => surface.identity.id === '@cis-core/conformance-generation')).toBe(true);
  });

  it('derives a valid canonical replay and evidence contract', () => {
    const surface = buildSurface();
    const crec = deriveCanonicalReplayEvidenceContract(surface);
    const issues = validateCanonicalReplayEvidenceContract(crec);

    expect(crec.intent).toBe(surface.purpose);
    expect(crec.proofSurfaceLevel).toBe(surface.proofLevel);
    expect(issues.filter((issue) => issue.severity === 'error')).toHaveLength(0);
  });

  it('verifies replay coverage across the demo registry', () => {
    const registry = createDemoProofSurfaceRegistry();
    const report = verifyReplayCoverage(registry.list());

    expect(report.passed).toBe(true);
    expect(report.inspectedSurfaces).toBeGreaterThan(0);
    expect(report.replayableSurfaces).toBe(report.inspectedSurfaces);
  });
});
