import {
  type ProofSurface,
  ProofSurfaceRegistry,
} from './proofSurface.js';
import { deriveCanonicalReplayEvidenceContract, type CanonicalReplayEvidenceContract } from './crec.js';

function createSurface(overrides: ProofSurface): ProofSurface {
  return structuredClone(overrides);
}

export type ProofSurfaceDomain =
  | 'Governance'
  | 'Execution'
  | 'Runtime'
  | 'Intent'
  | 'Evidence'
  | 'Verification'
  | 'Replay'
  | 'Audit'
  | 'Interoperability';

export type ProofSurfaceHealthIndicator =
  | 'Verified'
  | 'Experimental'
  | 'Simulated'
  | 'Operational'
  | 'Commercially Available';

export interface ProofSurfaceSummary {
  identity: ProofSurface['identity'];
  domain: ProofSurfaceDomain;
  healthIndicator: ProofSurfaceHealthIndicator;
  proofLevel: string;
  maturity: string;
  verificationStatus: string;
  replayStatus: string;
  operationalStatus: string;
  truthBoundary: string;
  constitutionalLimits: string;
  dependencies: string[];
  inputs: string[];
  outputs: string[];
  evidenceReceipts: string[];
  currentEvidence: ProofSurface['evidence'];
  replayPath: string;
  verificationPath: string;
  whatItProves: string;
  whatItDoesNotProve: string;
  blindspots: string[];
  knownLimitations: string[];
  adversarialClaims: string[];
  battleScars: string[];
  relatedProofSurfaces: string[];
  currentMaturity: string;
  commercialReadiness: ProofSurface['commercialReadiness'];
  nextRequiredEvidence: string[];
  crec?: CanonicalReplayEvidenceContract;
}

function uniqueStrings(values: string[]): string[] {
  return [...new Set(values.map((value) => value.trim()).filter((value) => value.length > 0))];
}

function surfaceText(surface: ProofSurface): string {
  return [
    surface.identity.id,
    surface.identity.name,
    surface.identity.type,
    surface.purpose,
    surface.truthBoundary,
    surface.constitutionalProfile.purpose,
    surface.constitutionalProfile.constitutionalScope,
    surface.constitutionalProfile.verificationProcess,
    surface.constitutionalProfile.replayPath,
    surface.constitutionalProfile.evidenceModel,
  ]
    .join(' ')
    .toLowerCase();
}

function deriveProofSurfaceDomain(surface: ProofSurface): ProofSurfaceDomain {
  const identityText = `${surface.identity.id} ${surface.identity.name}`.toLowerCase();
  const text = surfaceText(surface);
  if (identityText.includes('governance')) {
    return 'Governance';
  }
  if (identityText.includes('execution') || identityText.includes('router') || text.includes('execution') || text.includes('gpu')) {
    return 'Execution';
  }
  if (identityText.includes('runtime')) {
    return 'Runtime';
  }
  if (identityText.includes('intent')) {
    return 'Intent';
  }
  if (identityText.includes('console') || identityText.includes('audit') || identityText.includes('operator') || identityText.includes('telemetry')) {
    return 'Audit';
  }
  if (identityText.includes('studio') || text.includes('interoperability') || text.includes('visualization') || text.includes('dashboard')) {
    return 'Interoperability';
  }
  if (identityText.includes('replay')) {
    return 'Replay';
  }
  if (identityText.includes('verification')) {
    return 'Verification';
  }
  if (identityText.includes('evidence')) {
    return 'Evidence';
  }
  return 'Governance';
}

function deriveProofSurfaceHealthIndicator(surface: ProofSurface): ProofSurfaceHealthIndicator {
  const readiness = surface.commercialReadiness.currentReadiness.toLowerCase();
  if (readiness.includes('commercial')) {
    return 'Commercially Available';
  }
  switch (surface.operationalStatus) {
    case 'Production':
    case 'Production Candidate':
      return 'Operational';
    case 'Verified Prototype':
    case 'Reference Implementation':
      return 'Verified';
    case 'Prototype':
      return 'Experimental';
    case 'Scaffold':
    default:
      return 'Simulated';
  }
}

function deriveProofSurfaceSummary(
  surface: ProofSurface,
  surfaces: ProofSurface[],
): ProofSurfaceSummary {
  const relatedProofSurfaces = uniqueStrings([
    ...surface.constitutionalProfile.dependencies.filter((dependency) => surfaces.some((candidate) => candidate.identity.id === dependency)),
    ...surfaces
      .filter((candidate) => candidate.identity.id !== surface.identity.id && candidate.constitutionalProfile.dependencies.includes(surface.identity.id))
      .map((candidate) => candidate.identity.id),
  ]);
  const evidenceReceipts = uniqueStrings(surface.evidence.map((evidence) => evidence.id));
  const inputs = uniqueStrings([
    ...surface.constitutionalProfile.dependencies,
    ...surface.evidence.map((evidence) => evidence.id),
  ]);
  const outputs = uniqueStrings([
    ...surface.claims.map((claim) => claim.statement),
    ...surface.claims.map((claim) => claim.id),
  ]);
  const currentEvidence = surface.evidence.map((evidence) => structuredClone(evidence));

  return {
    identity: surface.identity,
    domain: deriveProofSurfaceDomain(surface),
    healthIndicator: deriveProofSurfaceHealthIndicator(surface),
    proofLevel: surface.proofLevel,
    maturity: surface.constitutionalProfile.currentMaturity,
    verificationStatus: surface.verificationStatus,
    replayStatus: surface.replayStatus,
    operationalStatus: surface.operationalStatus,
    truthBoundary: surface.truthBoundary,
    constitutionalLimits: surface.constitutionalProfile.constitutionalLimits,
    dependencies: [...surface.constitutionalProfile.dependencies],
    inputs,
    outputs,
    evidenceReceipts,
    currentEvidence,
    replayPath: surface.constitutionalProfile.replayPath,
    verificationPath: surface.constitutionalProfile.verificationProcess,
    whatItProves: surface.constitutionalProfile.purpose,
    whatItDoesNotProve: surface.constitutionalProfile.truthBoundary,
    blindspots: [...surface.blindspots],
    knownLimitations: uniqueStrings([
      surface.constitutionalProfile.constitutionalLimits,
      ...surface.battleScars,
    ]),
    adversarialClaims: [...surface.adversarialClaims],
    battleScars: [...surface.battleScars],
    relatedProofSurfaces,
    currentMaturity: surface.constitutionalProfile.currentMaturity,
    commercialReadiness: surface.commercialReadiness,
    nextRequiredEvidence: [...surface.nextRequiredEvidence],
    crec: deriveCanonicalReplayEvidenceContract(surface),
  };
}

function governanceSurface(): ProofSurface {
  return createSurface({
    identity: {
      id: '@aaes-os/aaes-governance',
      name: 'AAES Governance Package',
      type: 'repository',
      version: '0.2.0',
    },
    purpose: 'Provide the constitutional proof-surface runtime, registry, and validation law.',
    claims: [
      {
        id: 'gov-impl',
        type: 'Implementation',
        statement: 'The package implements proof-surface types, validation, and registry helpers.',
        evidenceIds: ['gov-impl-evidence'],
        proofLevel: 'P1',
      },
      {
        id: 'gov-verify',
        type: 'Verification',
        statement: 'The package ships tests that validate supported and unsupported proof surfaces.',
        evidenceIds: ['gov-test-evidence'],
        proofLevel: 'P2',
      },
    ],
    evidence: [
      {
        id: 'gov-impl-evidence',
        statement: 'Source files define ProofSurface, ProofSurfaceRegistry, and JSON helpers.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'src/proofSurface.ts',
      },
      {
        id: 'gov-test-evidence',
        statement: 'Vitest coverage exercises validation, proof levels, and registry publication.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'src/proofSurface.test.ts',
      },
    ],
    verificationStatus: 'Test Verified',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'The package proves proof-surface governance and validation, not application deployments.',
    constitutionalProfile: {
      purpose: 'Govern proof-surface claims across the stack.',
      authority: 'AAES governance law and registry validation.',
      evidenceModel: 'Typed claims, typed evidence, schema documents, and test outputs.',
      verificationProcess: 'Build, test, and schema serialization checks.',
      complianceRequirements: ['No claim may exceed its proof surface', 'Every claim references evidence'],
      truthBoundary: 'The package does not certify external production systems.',
      constitutionalScope: 'Governance primitives, registry, and proof-surface schema.',
      constitutionalLimits: 'Does not replace consumer-specific adapters or deployment pipelines.',
      dependencies: ['runledger'],
      stewardship: 'AAES governance maintainers.',
      replayPath: 'Replay from registry documents and validation output.',
      failurePath: 'Reject unverified or unsupported claims and require stronger evidence.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: ['Independent verification is still limited to the local workspace.'],
    battleScars: ['Readiness language used to outpace machine-readable evidence.'],
    adversarialClaims: ['A scorecard can be mistaken for a verified artifact.'],
    colorTeamReadiness: {
      redTeam: 'Attack surface is low but claim/data mismatch remains a risk.',
      blueTeam: 'Validation rejects unsupported claims.',
      purpleTeam: 'Claims and evidence can be reconciled mechanically.',
      greenTeam: 'Build/test and schema generation are repeatable.',
      yellowTeam: 'Truth boundaries are explicit for consumers.',
      whiteTeam: 'Authority chain lives in governance code.',
    },
    commercialReadiness: {
      targetTier: 'Builder',
      intendedCustomer: 'Governance teams and tool builders',
      primaryUseCase: 'Machine-readable proof-surface publication',
      valueProposition: 'A standard claim/evidence contract for dashboards and product tiers.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['Independent consumer integration', 'Cross-repo publish/subscribe demos'],
  });
}

function runtimeSurface(): ProofSurface {
  return createSurface({
    identity: {
      id: '@aaes-os/ucr-runtime',
      name: 'UCR Runtime',
      type: 'runtime',
      version: '0.2.0',
    },
    purpose: 'Execute governed runtime runs with trace, invariant, and patch wiring.',
    claims: [
      {
        id: 'ucr-impl',
        type: 'Implementation',
        statement: 'The runtime delegates compatibility callers into the governed UCRRuntime execution path and writes terminal evidence receipts.',
        evidenceIds: ['ucr-impl-evidence'],
        proofLevel: 'P1',
      },
      {
        id: 'ucr-verify',
        type: 'Verification',
        statement: 'Package tests prove trace-fault emission, span closure, and deployed patch behavior.',
        evidenceIds: ['ucr-test-evidence'],
        proofLevel: 'P2',
      },
    ],
    evidence: [
      {
        id: 'ucr-impl-evidence',
        statement: 'src/ucrRuntime.ts, src/RuntimeCore.ts, and src/withSpanGuard.ts wire the governed runtime path, trace receipts, and terminal evidence storage.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'packages/ucr-runtime/src/ucrRuntime.ts',
      },
      {
        id: 'ucr-test-evidence',
        statement: 'Vitest coverage exercises the governed runtime, fault traces, and patch regression behavior.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'packages/ucr-runtime/src/ucrRuntime.test.ts',
      },
    ],
    verificationStatus: 'Test Verified',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'The runtime proves governed execution and trace consistency, not full production orchestration.',
    constitutionalProfile: {
      purpose: 'Governed UCR runtime execution.',
      authority: 'AAES governance invariants, runledger, trace-bus, and tri-core patch ledger.',
      evidenceModel: 'Run records, trace events, invariant faults, and patch ledger states.',
      verificationProcess: 'Package tests and runtime integration checks.',
      complianceRequirements: [
        'Every run must emit trace evidence for invariants and faults',
        'Span boundaries must close deterministically',
      ],
      truthBoundary: 'The runtime does not certify external systems.',
      constitutionalScope: 'UCR runtime execution, trace emission, and patch application.',
      constitutionalLimits: 'Does not replace the governance ledger or downstream services.',
      dependencies: ['aaes-governance', 'runledger', 'trace-bus', 'tri-core-protocol'],
      stewardship: 'UCR runtime maintainers.',
      replayPath: 'Replay from run ledger and trace bus logs.',
      failurePath: 'Fail closed on invariant breaches and orphan spans.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: ['The runtime still relies on in-memory run, trace, and receipt stores in this workspace.'],
    battleScars: ['Trace-fault emission had to be wired into the invariant engine.'],
    adversarialClaims: ['A compatibility wrapper can masquerade as a governed path if receipt evidence is ignored.'],
    colorTeamReadiness: {
      redTeam: 'Attack surface remains wherever outputs or spans diverge from evidence.',
      blueTeam: 'Trace and ledger events can be inspected deterministically.',
      purpleTeam: 'Execution and governance claims can be reconciled mechanically.',
      greenTeam: 'Build, test, and patch regression checks are repeatable.',
      yellowTeam: 'Truth boundaries are explicit for consumers.',
      whiteTeam: 'Authority remains in the governance package.',
    },
    commercialReadiness: {
      targetTier: 'Builder',
      intendedCustomer: 'Runtime and governance teams',
      primaryUseCase: 'Governed runtime execution',
      valueProposition: 'A traceable execution path with patch-controlled output behavior.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['End-to-end integration in a long-running service', 'Independent replay of fault traces'],
  });
}

function opsConsoleSurface(): ProofSurface {
  return createSurface({
    identity: {
      id: '@aaes-os/ops-console',
      name: 'AAES Ops Console',
      type: 'runtime',
      version: '0.2.0',
    },
    purpose: 'Expose governance, telemetry, and proof-surface records to operators.',
    claims: [
      {
        id: 'ops-impl',
        type: 'Implementation',
        statement: 'The console exposes telemetry routes and a proof-surface endpoint.',
        evidenceIds: ['ops-impl-evidence'],
        proofLevel: 'P1',
      },
      {
        id: 'ops-verify',
        type: 'Verification',
        statement: 'The console has route coverage and API tests for operator surfaces.',
        evidenceIds: ['ops-test-evidence'],
        proofLevel: 'P2',
      },
    ],
    evidence: [
      {
        id: 'ops-impl-evidence',
        statement: 'Server routes expose telemetry and proof-surface catalog JSON.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'services/ops-console/src/server.ts',
      },
      {
        id: 'ops-test-evidence',
        statement: 'Vitest routes prove the operator console behavior.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'services/ops-console/src/server.test.ts',
      },
    ],
    verificationStatus: 'Test Verified',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'The console proves operator visibility and proof-surface exposure, not governance authority itself.',
    constitutionalProfile: {
      purpose: 'Operator telemetry and proof-surface visualization.',
      authority: 'AAES governance and runtime telemetry adapters.',
      evidenceModel: 'HTTP JSON routes, test output, and registry snapshots.',
      verificationProcess: 'Build, test, route smoke, and JSON serialization checks.',
      complianceRequirements: ['No claim beyond route evidence', 'Every surface references a proof source'],
      truthBoundary: 'The console is an operator view, not the source of truth.',
      constitutionalScope: 'Telemetry, proof surfaces, and operator dashboards.',
      constitutionalLimits: 'Does not replace governance or runtime execution.',
      dependencies: ['aaes-governance'],
      stewardship: 'Ops console maintainers.',
      replayPath: 'Replay from route output and serialized proof-surface catalog.',
      failurePath: 'Degrade to read-only operator view when proof-surface data is unavailable.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: ['Some upstream telemetry remains seeded or synthesized.'],
    battleScars: ['Operator surfaces previously outpaced evidence wiring.'],
    adversarialClaims: ['A dashboard can be mistaken for the governing authority.'],
    colorTeamReadiness: {
      redTeam: 'Routes can be probed, so the proof surface should stay read-only.',
      blueTeam: 'Validation and JSON output are inspectable.',
      purpleTeam: 'Telemetry plus proof surfaces can be reconciled.',
      greenTeam: 'Build/test and server routes are repeatable.',
      yellowTeam: 'Operator truth boundaries are visible.',
      whiteTeam: 'Authority and evidence are separated from presentation.',
    },
    commercialReadiness: {
      targetTier: 'Professional',
      intendedCustomer: 'Operators and governance teams',
      primaryUseCase: 'Operational proof-surface visibility',
      valueProposition: 'A single pane for evidence-backed governance claims.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['Live registry-backed operator demo', 'Independent dashboard integration'],
  });
}

function novaStudioSurface(): ProofSurface {
  return createSurface({
    identity: {
      id: '@aaes-os/nova-studio',
      name: 'Nova Studio',
      type: 'runtime',
      version: '0.1.0',
    },
    purpose: 'Render proof-surface records for operators and contributors in a studio UI.',
    claims: [
      {
        id: 'studio-impl',
        type: 'Implementation',
        statement: 'The studio can render proof-surface registry records from a direct import.',
        evidenceIds: ['studio-impl-evidence'],
        proofLevel: 'P1',
      },
      {
        id: 'studio-verify',
        type: 'Verification',
        statement: 'The production bundle and replay coverage smoke run successfully against the local registry.',
        evidenceIds: ['studio-smoke-evidence'],
        proofLevel: 'P2',
      },
    ],
    evidence: [
      {
        id: 'studio-impl-evidence',
        statement: 'The studio source tree contains components for proof-surface visualization.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'nova-studio/src/components/StudioApp.tsx',
      },
      {
        id: 'studio-smoke-evidence',
        statement: 'The Nova Studio production build and smoke verify the built dist output and replay coverage on the local registry.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'nova-studio/scripts/smoke.ts',
      },
    ],
    verificationStatus: 'Test Verified',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'The studio proves the visualization concept and the packaged build/smoke path, not a full production desktop platform.',
    constitutionalProfile: {
      purpose: 'Studio UI for proof-surface visualization.',
      authority: 'AAES governance package and studio adapters.',
      evidenceModel: 'Direct registry import, rendered summary data, built bundles, and smoke output.',
      verificationProcess: 'Static render, production bundle build, and local replay smoke.',
      complianceRequirements: ['No visual claim beyond imported registry data', 'No maturity claim beyond built and smokes output'],
      truthBoundary: 'The studio is a consumer view and smoke-verified bundle, not a verifier of external systems.',
      constitutionalScope: 'Proof-surface rendering in the studio UI.',
      constitutionalLimits: 'Does not replace the authoritative registry or backend verification.',
      dependencies: ['aaes-governance'],
      stewardship: 'Nova Studio maintainers.',
      replayPath: 'Replay via the imported registry snapshot and the smoke-verified local registry path.',
      failurePath: 'Fallback to empty or seeded visualization when the registry is unavailable, and fail smoke when the bundle or replay coverage is missing.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: ['Live operator backend integration still needs a replayable production catalog path.'],
    battleScars: ['Studio surfaces can become pretty before they are verified.'],
    adversarialClaims: ['A studio screenshot can be mistaken for authoritative evidence.'],
    colorTeamReadiness: {
      redTeam: 'UI surfaces are visible and should be scrutinized.',
      blueTeam: 'Imported records can be inspected deterministically.',
      purpleTeam: 'UI and registry claims can be reconciled.',
      greenTeam: 'Components can render seeded or direct registry data.',
      yellowTeam: 'Truth boundaries can be shown in the interface.',
      whiteTeam: 'Authority remains in the governance package.',
    },
    commercialReadiness: {
      targetTier: 'Builder',
      intendedCustomer: 'Operators, reviewers, and contributors',
      primaryUseCase: 'Proof-surface visualization and review',
      valueProposition: 'A clear UI for claim/evidence maturity.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['Backend integration with operator and proof surfaces', 'User-facing session persistence'],
  });
}

function cisStandardsHierarchySurface(): ProofSurface {
  return createSurface({
    identity: {
      id: '@cis-core/standards-hierarchy',
      name: 'CIS Standards Hierarchy',
      type: 'specification',
      version: '1.0.0',
    },
    purpose: 'Define the constitutional standards hierarchy, machine-readable ingest spec, and traceability matrix for CIS Core and its companion specifications.',
    claims: [
      {
        id: 'cis-hierarchy-spec',
        type: 'Specification',
        statement: 'The repository publishes a CIS standards hierarchy document and machine-readable hierarchy spec that preserve Core terminology and governance rules.',
        evidenceIds: ['cis-hierarchy-doc', 'cis-hierarchy-json'],
        proofLevel: 'P1',
      },
      {
        id: 'cis-hierarchy-traceability',
        type: 'Verification',
        statement: 'The hierarchy has a formal traceability matrix that maps requirements to components, evidence, and tests.',
        evidenceIds: ['cis-hierarchy-traceability', 'cis-hierarchy-test'],
        proofLevel: 'P2',
      },
    ],
    evidence: [
      {
        id: 'cis-hierarchy-doc',
        statement: 'docs/crk1/release/CIS_STANDARDS_HIERARCHY.md defines CIS Core, companion specifications, governance, and Research OS mapping.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/CIS_STANDARDS_HIERARCHY.md',
      },
      {
        id: 'cis-hierarchy-json',
        statement: 'docs/crk1/release/CIS_STANDARDS_HIERARCHY.spec.json provides a machine-readable hierarchy for orchestrator ingestion.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/CIS_STANDARDS_HIERARCHY.spec.json',
      },
      {
        id: 'cis-hierarchy-traceability',
        statement: 'docs/crk1/release/CIS_STANDARDS_TRACEABILITY_MATRIX.md maps requirements to components, evidence, and tests.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'docs/crk1/release/CIS_STANDARDS_TRACEABILITY_MATRIX.md',
      },
      {
        id: 'cis-hierarchy-test',
        statement: 'Proof-surface tests publish the CIS hierarchy into the demo registry and verify it remains first-class evidence.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'packages/aaes-governance/src/proofSurface.test.ts',
      },
    ],
    verificationStatus: 'Test Verified',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'The surface proves documentation and registry publication, not independent external certification.',
    constitutionalProfile: {
      purpose: 'Standards hierarchy publication and traceability.',
      authority: 'CIS Core, AAES governance, and the proof-surface catalog.',
      evidenceModel: 'Markdown hierarchy, machine-readable JSON spec, traceability matrix, and registry publication tests.',
      verificationProcess: 'Document review, JSON ingestion, proof-surface publication, and Vitest coverage.',
      complianceRequirements: [
        'Core terminology must remain stable',
        'Companion specifications must inherit Core terms',
        'Traceability must connect requirements, evidence, and tests',
      ],
      truthBoundary: 'The surface is a release artifact, not an external conformance certificate.',
      constitutionalScope: 'CIS Core, companion specifications, traceability, and Research OS mapping.',
      constitutionalLimits: 'Does not certify third-party implementations or domain profiles.',
      dependencies: ['@aaes-os/aaes-governance'],
      stewardship: 'CIS release maintainers.',
      replayPath: 'Replay from the release docs, JSON ingest spec, and catalog publication coverage.',
      failurePath: 'Reject hierarchy claims when the markdown, JSON, or traceability artifacts drift out of sync.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: ['External implementations still need independent conformance suites.'],
    battleScars: ['Standards language can drift when companion documents start redefining core terms.'],
    adversarialClaims: ['A polished documentation set can be mistaken for a complete conformance suite.'],
    colorTeamReadiness: {
      redTeam: 'Hierarchy drift must be watched where companions or profiles introduce local terminology.',
      blueTeam: 'The JSON spec and traceability matrix can be inspected directly.',
      purpleTeam: 'Docs, JSON, and proof-surface records can be reconciled mechanically.',
      greenTeam: 'Registry publication and summary rendering are repeatable.',
      yellowTeam: 'Core terminology remains the stable center.',
      whiteTeam: 'Governance evidence is separated from implementation detail.',
    },
    commercialReadiness: {
      targetTier: 'Professional',
      intendedCustomer: 'Standards stewards, platform teams, and implementers',
      primaryUseCase: 'Constitutional standards publication and traceability',
      valueProposition: 'A stable hierarchy that can be ingested by tooling and audited by humans.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['Independent downstream ingest of the JSON hierarchy', 'Conformance suite linkage for companion specifications'],
  });
}

function cisStandardsTraceabilityMatrixSurface(): ProofSurface {
  return createSurface({
    identity: {
      id: '@cis-core/standards-traceability-matrix',
      name: 'CIS Standards Traceability Matrix',
      type: 'specification',
      version: '1.0.0',
    },
    purpose: 'Provide the first-class requirement, component, evidence, and test matrix for CIS Core and companion artifacts.',
    claims: [
      {
        id: 'cis-traceability-impl',
        type: 'Specification',
        statement: 'The repository publishes a formal traceability matrix that maps requirements to components, evidence, and tests.',
        evidenceIds: ['cis-traceability-doc'],
        proofLevel: 'P1',
      },
      {
        id: 'cis-traceability-test',
        type: 'Verification',
        statement: 'The traceability matrix drives the generated conformance suite input and is covered by a drift test.',
        evidenceIds: ['cis-traceability-json', 'cis-traceability-test-evidence'],
        proofLevel: 'P2',
      },
    ],
    evidence: [
      {
        id: 'cis-traceability-doc',
        statement: 'docs/crk1/release/CIS_STANDARDS_TRACEABILITY_MATRIX.md defines the formal matrix with requirement, component, evidence, and test columns.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/CIS_STANDARDS_TRACEABILITY_MATRIX.md',
      },
      {
        id: 'cis-traceability-json',
        statement: 'docs/crk1/release/CIS_STANDARDS_HIERARCHY.spec.json embeds the traceability matrix as the machine-readable source of truth.',
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/CIS_STANDARDS_HIERARCHY.spec.json',
      },
      {
        id: 'cis-traceability-test-evidence',
        statement: 'The conformance generation test verifies that the committed suite input matches the generated output from the hierarchy traceability matrix.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'tests/release/cis-conformance-generation.test.ts',
      },
    ],
    verificationStatus: 'Test Verified',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'The surface proves traceability publication and generation linkage, not external certification.',
    constitutionalProfile: {
      purpose: 'Traceability from requirements to evidence and tests.',
      authority: 'CIS release maintainers and the hierarchy source of truth.',
      evidenceModel: 'Traceability matrix markdown, machine-readable hierarchy JSON, and drift tests.',
      verificationProcess: 'Review matrix rows, regenerate suite input, and compare committed output.',
      complianceRequirements: [
        'Every major capability must have a matrix row',
        'Matrix rows must expose requirement, component, evidence, and test',
        'Generated conformance input must remain aligned with the matrix',
      ],
      truthBoundary: 'The matrix is a publication surface, not a certification authority.',
      constitutionalScope: 'Traceability rows and generated conformance input.',
      constitutionalLimits: 'Does not replace the conformance suite itself or external certifications.',
      dependencies: ['@cis-core/standards-hierarchy'],
      stewardship: 'CIS release maintainers.',
      replayPath: 'Replay from the traceability markdown and the generated suite input.',
      failurePath: 'Reject traceability claims when the matrix, generated input, or tests drift apart.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: ['Traceability rows still require release governance before they can change.'],
    battleScars: ['Manual suite editing used to bypass the matrix.'],
    adversarialClaims: ['A matrix can appear complete if its generated output is not checked.'],
    colorTeamReadiness: {
      redTeam: 'Drift between docs and generated suite should fail release checks.',
      blueTeam: 'The matrix and generated input are machine-checkable.',
      purpleTeam: 'Docs, JSON, and tests can be reconciled mechanically.',
      greenTeam: 'The release surface can be regenerated repeatably.',
      yellowTeam: 'The matrix remains the source of truth.',
      whiteTeam: 'Governance stays attached to the published matrix.',
    },
    commercialReadiness: {
      targetTier: 'Professional',
      intendedCustomer: 'Standards stewards and conformance teams',
      primaryUseCase: 'Requirement-to-evidence traceability publication',
      valueProposition: 'A first-class matrix that prevents documentation and test drift.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['Publish downstream profile-specific traceability rows', 'Generate conformance execution reports from the matrix'],
  });
}

function cisCompanionRegistrySurface(): ProofSurface {
  return createSurface({
    identity: {
      id: '@cis-core/companion-spec-registry',
      name: 'CIS Companion Spec Registry',
      type: 'specification',
      version: '1.0.0',
    },
    purpose: 'Publish CIS Core, companion specifications, implementation profiles, and Research OS through a shared proof-surface pattern.',
    claims: [
      {
        id: 'cis-registry-impl',
        type: 'Specification',
        statement: 'The repository publishes a machine-readable companion-spec registry that keeps CIS Core, companion specifications, profiles, and Research OS aligned.',
        evidenceIds: ['cis-registry-json'],
        proofLevel: 'P1',
      },
      {
        id: 'cis-registry-evidence',
        type: 'Implementation',
        statement: 'The registry is represented in the proof-surface catalog and can be replayed from the release surface.',
        evidenceIds: ['cis-registry-test', 'cis-registry-doc'],
        proofLevel: 'P1',
      },
    ],
    evidence: [
      {
        id: 'cis-registry-json',
        statement: 'docs/crk1/release/CIS_COMPANION_SPEC_REGISTRY.spec.json enumerates CIS Core, companions, profiles, and Research OS.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/CIS_COMPANION_SPEC_REGISTRY.spec.json',
      },
      {
        id: 'cis-registry-doc',
        statement: 'docs/crk1/release/CIS_STANDARDS_HIERARCHY.md links the companion registry into the release surface.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/CIS_STANDARDS_HIERARCHY.md',
      },
      {
        id: 'cis-registry-test',
        statement: 'Proof-surface tests confirm the companion registry is published into the demo catalog.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'packages/aaes-governance/src/proofSurface.test.ts',
      },
    ],
    verificationStatus: 'Test Verified',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'The registry proves publication and alignment, not external certification of every companion implementation.',
    constitutionalProfile: {
      purpose: 'Registry publication for companion specifications and Research OS.',
      authority: 'CIS Core, the hierarchy, and the proof-surface catalog.',
      evidenceModel: 'Machine-readable registry, linked release docs, and registry publication tests.',
      verificationProcess: 'JSON ingest, release review, and proof-surface publication.',
      complianceRequirements: [
        'Companion specifications must be listed',
        'Implementation profiles must be listed',
        'Research OS must be listed',
      ],
      truthBoundary: 'The registry is a publication surface, not a certification authority.',
      constitutionalScope: 'Companion specifications, implementation profiles, and Research OS.',
      constitutionalLimits: 'Does not replace conformance suites or implementation audits.',
      dependencies: ['@cis-core/standards-hierarchy'],
      stewardship: 'CIS release maintainers.',
      replayPath: 'Replay from the JSON registry and the release docs that reference it.',
      failurePath: 'Reject registry claims when the JSON file and release docs drift apart.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: ['Registry alignment still depends on disciplined release updates.'],
    battleScars: ['Companion lists can drift if they are maintained in more than one place.'],
    adversarialClaims: ['A registry entry can look official without being synchronized to the hierarchy.'],
    colorTeamReadiness: {
      redTeam: 'Registry drift should be watched wherever companion specs change.',
      blueTeam: 'The JSON registry can be inspected directly.',
      purpleTeam: 'Registry and hierarchy can be reconciled mechanically.',
      greenTeam: 'Release publication is repeatable.',
      yellowTeam: 'Core remains the stable source of truth.',
      whiteTeam: 'Authority stays with the constitutional release process.',
    },
    commercialReadiness: {
      targetTier: 'Professional',
      intendedCustomer: 'Platform and standards teams',
      primaryUseCase: 'Unified publication of companion specifications',
      valueProposition: 'One registry for core, companions, profiles, and Research OS.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['Round-trip registry ingestion in the orchestrator', 'Independent companion-spec publish flow'],
  });
}

function artifactGovernanceSurface(): ProofSurface {
  return createSurface({
    identity: {
      id: '@cis-core/artifact-governance',
      name: 'Artifact Governance Model',
      type: 'specification',
      version: '1.0.0',
    },
    purpose: 'Standardize the governance metadata model across major artifacts in the CIS ecosystem.',
    claims: [
      {
        id: 'artifact-gov-model',
        type: 'Specification',
        statement: 'The repository publishes a shared artifact governance model and registry for major artifacts.',
        evidenceIds: ['artifact-gov-doc', 'artifact-gov-json'],
        proofLevel: 'P1',
      },
      {
        id: 'artifact-gov-test',
        type: 'Verification',
        statement: 'The artifact governance registry can be loaded and summarized by tooling.',
        evidenceIds: ['artifact-gov-test-evidence'],
        proofLevel: 'P2',
      },
    ],
    evidence: [
      {
        id: 'artifact-gov-doc',
        statement: 'docs/crk1/release/ARTIFACT_GOVERNANCE_MODEL.md defines the shared governance fields and lifecycle.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/ARTIFACT_GOVERNANCE_MODEL.md',
      },
      {
        id: 'artifact-gov-json',
        statement: 'docs/crk1/release/ARTIFACT_GOVERNANCE_REGISTRY.spec.json enumerates the governed artifact records.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/ARTIFACT_GOVERNANCE_REGISTRY.spec.json',
      },
      {
        id: 'artifact-gov-test-evidence',
        statement: 'The artifact governance registry test confirms the shared model is machine-readable.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'tests/release/artifact-governance.test.ts',
      },
    ],
    verificationStatus: 'Test Verified',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'The surface proves repository-level governance metadata publication, not external certification.',
    constitutionalProfile: {
      purpose: 'Shared governance metadata for major artifacts.',
      authority: 'CIS release maintainers and the artifact governance registry.',
      evidenceModel: 'Governance model docs, registry JSON, and loader tests.',
      verificationProcess: 'Document review, registry loading, and test execution.',
      complianceRequirements: [
        'Artifacts must declare status, version, steward, and classification',
        'Artifacts must identify their parent specification',
        'Artifacts must expose traceability and history',
      ],
      truthBoundary: 'The surface standardizes metadata; it does not adjudicate every future release decision.',
      constitutionalScope: 'Artifact metadata, release records, and traceability links.',
      constitutionalLimits: 'Does not replace the normative specifications themselves.',
      dependencies: ['@cis-core/standards-hierarchy'],
      stewardship: 'CIS release maintainers.',
      replayPath: 'Replay from the governance model doc and registry JSON.',
      failurePath: 'Reject artifact claims when the metadata registry and release docs drift.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: ['Coverage is currently scoped to the major release artifacts in this repository.'],
    battleScars: ['Some artifacts historically mixed normative and informative content without explicit labels.'],
    adversarialClaims: ['A polished release note can be mistaken for a governed artifact without metadata.'],
    colorTeamReadiness: {
      redTeam: 'Artifacts without declared stewardship should be treated as suspect.',
      blueTeam: 'The registry is machine-readable and inspectable.',
      purpleTeam: 'Docs and JSON can be reconciled mechanically.',
      greenTeam: 'Loader tests make the registry repeatable.',
      yellowTeam: 'Classification and parentage are visible.',
      whiteTeam: 'Governance authority stays in the published metadata.',
    },
    commercialReadiness: {
      targetTier: 'Professional',
      intendedCustomer: 'Standards stewards and platform operators',
      primaryUseCase: 'Repository-wide artifact governance',
      valueProposition: 'One metadata model for major artifacts.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['Expand registry coverage to more implementation profiles', 'Link artifact governance to conformance review workflows'],
  });
}

function sovereignRouterPricingSurface(): ProofSurface {
  return createSurface({
    identity: {
      id: '@cis-core/sovereign-router-pricing',
      name: 'Sovereign Router X Pricing Model',
      type: 'specification',
      version: '1.0.0',
    },
    purpose: 'Define layered revenue streams and customer-segment pricing for the Sovereign Router X platform.',
    claims: [
      {
        id: 'pricing-layers',
        type: 'Specification',
        statement: 'The product prices platform subscription, AI usage, governance and assurance, knowledge services, enterprise services, and professional services as separate value layers.',
        evidenceIds: ['pricing-doc', 'pricing-spec'],
        proofLevel: 'P1',
      },
      {
        id: 'pricing-segments',
        type: 'Verification',
        statement: 'The pricing model enumerates individual, professional, team, enterprise, and public sector segments for comparative unit economics.',
        evidenceIds: ['pricing-test'],
        proofLevel: 'P2',
      },
    ],
    evidence: [
      {
        id: 'pricing-doc',
        statement: 'docs/crk1/release/SOVEREIGN_ROUTER_X_PRICING.md documents the layered revenue model and segment strategy.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/SOVEREIGN_ROUTER_X_PRICING.md',
      },
      {
        id: 'pricing-spec',
        statement: 'docs/crk1/release/SOVEREIGN_ROUTER_X_PRICING.spec.json provides a machine-readable pricing model.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/SOVEREIGN_ROUTER_X_PRICING.spec.json',
      },
      {
        id: 'pricing-test',
        statement: 'The pricing model test validates layered revenue and segment coverage.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'tests/release/pricing-model.test.ts',
      },
    ],
    verificationStatus: 'Test Verified',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'The surface proves the pricing model is documented and machine-readable, not that every market price is optimized.',
    constitutionalProfile: {
      purpose: 'Layered pricing and unit economics for Sovereign Router X.',
      authority: 'Platform maintainers and the release documentation surface.',
      evidenceModel: 'Pricing markdown, pricing spec JSON, and unit-economics tests.',
      verificationProcess: 'Document review, JSON loading, and test execution.',
      complianceRequirements: [
        'Revenue layers must be separated',
        'Customer segments must be explicit',
        'Unit economics must be measurable',
      ],
      truthBoundary: 'The surface guides pricing strategy; it does not guarantee market fit.',
      constitutionalScope: 'Pricing layers, segment strategy, and unit economics.',
      constitutionalLimits: 'Does not replace sales execution or finance operations.',
      dependencies: ['@cis-core/standards-hierarchy'],
      stewardship: 'Platform maintainers.',
      replayPath: 'Replay from the pricing docs, JSON spec, and test coverage.',
      failurePath: 'Reject pricing claims when the markdown, spec, or tests drift apart.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: ['Real-world willingness to pay still needs validation across target segments.'],
    battleScars: ['Inference-only pricing tends to collapse as model costs fall.'],
    adversarialClaims: ['A low token price can hide the absence of durable platform revenue.'],
    colorTeamReadiness: {
      redTeam: 'Segment-specific pricing assumptions should be stress-tested.',
      blueTeam: 'The pricing spec can be inspected mechanically.',
      purpleTeam: 'Docs and JSON can be reconciled with tests.',
      greenTeam: 'Summaries and tests are repeatable.',
      yellowTeam: 'Revenue layers are explicit.',
      whiteTeam: 'Pricing strategy remains separated from technical governance.',
    },
    commercialReadiness: {
      targetTier: 'Professional',
      intendedCustomer: 'Product, finance, and platform teams',
      primaryUseCase: 'Layered pricing strategy and unit economics',
      valueProposition: 'Pricing that survives falling inference costs.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['Segment-specific customer interviews', 'Scenario model comparison across tiers'],
  });
}

function externalStandardsMappingSurface(): ProofSurface {
  return createSurface({
    identity: {
      id: '@cis-core/external-standards-mapping',
      name: 'External Standards Mapping Layer',
      type: 'specification',
      version: '1.0.0',
    },
    purpose: 'Map CIS Core and companion artifacts to ISO, NIST, IEEE, W3C, and IETF families.',
    claims: [
      {
        id: 'external-map-families',
        type: 'Specification',
        statement: 'The repository publishes an external standards mapping layer covering ISO, NIST, IEEE, W3C, and IETF.',
        evidenceIds: ['external-map-doc', 'external-map-json'],
        proofLevel: 'P1',
      },
      {
        id: 'external-map-trace',
        type: 'Verification',
        statement: 'The mapping layer ties external standards families to CIS artifacts and traceability concerns.',
        evidenceIds: ['external-map-test'],
        proofLevel: 'P2',
      },
    ],
    evidence: [
      {
        id: 'external-map-doc',
        statement: 'docs/crk1/release/EXTERNAL_STANDARDS_MAPPING.md explains the mapping layer and standards families.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/EXTERNAL_STANDARDS_MAPPING.md',
      },
      {
        id: 'external-map-json',
        statement: 'docs/crk1/release/EXTERNAL_STANDARDS_MAPPING.spec.json is a machine-readable mapping registry.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/EXTERNAL_STANDARDS_MAPPING.spec.json',
      },
      {
        id: 'external-map-test',
        statement: 'The external standards mapping test confirms the five major standards families are represented.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'tests/release/external-standards.test.ts',
      },
    ],
    verificationStatus: 'Test Verified',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'The surface proves standards-family mapping, not certification under those standards.',
    constitutionalProfile: {
      purpose: 'External interoperability and traceability mapping.',
      authority: 'CIS release maintainers and the external standards registry.',
      evidenceModel: 'Mapping docs, registry JSON, and loader tests.',
      verificationProcess: 'Document review, JSON loading, and test execution.',
      complianceRequirements: [
        'Five major standards families must be represented',
        'Mappings must be explicit and reviewable',
        'CIS terminology must remain unchanged',
      ],
      truthBoundary: 'The layer maps standards families; it does not claim formal certification.',
      constitutionalScope: 'ISO, NIST, IEEE, W3C, and IETF alignment.',
      constitutionalLimits: 'Does not override CIS requirements or governance.',
      dependencies: ['@cis-core/standards-hierarchy'],
      stewardship: 'CIS release maintainers.',
      replayPath: 'Replay from the external mapping docs and JSON registry.',
      failurePath: 'Reject mappings when docs, JSON, and tests drift.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: ['Standards family mappings still need project-by-project depth.'],
    battleScars: ['External references often outlive the mapping notes that explain them.'],
    adversarialClaims: ['A standards logo can be mistaken for actual compliance mapping.'],
    colorTeamReadiness: {
      redTeam: 'Each mapping should be treated as traceable and reviewable.',
      blueTeam: 'The registry is machine-readable and inspectable.',
      purpleTeam: 'Docs and JSON can be reconciled mechanically.',
      greenTeam: 'Family coverage is repeatable.',
      yellowTeam: 'The mapping boundary is explicit.',
      whiteTeam: 'CIS remains the normative center.',
    },
    commercialReadiness: {
      targetTier: 'Professional',
      intendedCustomer: 'Standards and compliance teams',
      primaryUseCase: 'Interoperability mapping and traceability',
      valueProposition: 'Clear mapping to the major external standards families.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['Map specific CIS artifacts to selected ISO/NIST/IEEE/W3C/IETF standards', 'Add downstream reviewer sign-off'],
  });
}

function cisConformanceGenerationSurface(): ProofSurface {
  return createSurface({
    identity: {
      id: '@cis-core/conformance-generation',
      name: 'CIS Conformance Suite Generation',
      type: 'specification',
      version: '1.0.0',
    },
    purpose: 'Generate the CIS conformance suite directly from the traceability matrix source of truth.',
    claims: [
      {
        id: 'conformance-gen-rule',
        type: 'Specification',
        statement: 'The repository defines a generation rule that derives the conformance suite input from the hierarchy traceability matrix.',
        evidenceIds: ['conformance-gen-doc', 'conformance-gen-generator'],
        proofLevel: 'P1',
      },
      {
        id: 'conformance-gen-test',
        type: 'Verification',
        statement: 'The committed conformance suite input matches the generated output from the hierarchy traceability source.',
        evidenceIds: ['conformance-gen-test'],
        proofLevel: 'P2',
      },
    ],
    evidence: [
      {
        id: 'conformance-gen-doc',
        statement: 'docs/crk1/release/CIS_CONFORMANCE_SUITE_GENERATION.md documents the generation rule and source of truth.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/CIS_CONFORMANCE_SUITE_GENERATION.md',
      },
      {
        id: 'conformance-gen-generator',
        statement: 'docs/crk1/release/CIS_CONFORMANCE_SUITE_INPUT.spec.generator.json records the generator inputs and rules.',
        proofLevel: 'P1',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'docs/crk1/release/CIS_CONFORMANCE_SUITE_INPUT.spec.generator.json',
      },
      {
        id: 'conformance-gen-test',
        statement: 'The generation test confirms the generated suite input matches the committed release artifact.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'tests/release/cis-conformance-generation.test.ts',
      },
    ],
    verificationStatus: 'Test Verified',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'The surface proves reproducible generation, not formal standards certification.',
    constitutionalProfile: {
      purpose: 'Generate the conformance suite from the traceability matrix.',
      authority: 'CIS release maintainers and the hierarchy source of truth.',
      evidenceModel: 'Generation docs, generator record, and comparison tests.',
      verificationProcess: 'Load hierarchy, derive suite input, and compare to committed output.',
      complianceRequirements: [
        'Suite input must derive from the traceability matrix',
        'Generator output must match the committed artifact',
        'Tests must cover the round trip',
      ],
      truthBoundary: 'The surface is a generation proof, not a certification authority.',
      constitutionalScope: 'Conformance suite input generation and verification.',
      constitutionalLimits: 'Does not replace the conformance suite itself.',
      dependencies: ['@cis-core/standards-hierarchy'],
      stewardship: 'CIS release maintainers.',
      replayPath: 'Replay from the hierarchy spec, generator record, and suite comparison test.',
      failurePath: 'Reject generation claims when the committed suite diverges from the source matrix.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: ['Traceability rows still require human governance before changes are published.'],
    battleScars: ['Manually maintained suite inputs drift from the traceability matrix over time.'],
    adversarialClaims: ['A copied JSON file can look generated even when it is stale.'],
    colorTeamReadiness: {
      redTeam: 'Generation drift should be treated as a release risk.',
      blueTeam: 'The generator and committed output are machine-checkable.',
      purpleTeam: 'Docs, generator record, and test can be reconciled mechanically.',
      greenTeam: 'Round-trip verification is repeatable.',
      yellowTeam: 'The traceability matrix remains the source of truth.',
      whiteTeam: 'Governance stays attached to the release docs.',
    },
    commercialReadiness: {
      targetTier: 'Professional',
      intendedCustomer: 'Conformance and standards teams',
      primaryUseCase: 'Reproducible conformance-suite generation',
      valueProposition: 'No manual drift between traceability and tests.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: ['Generate the suite as part of release automation', 'Add downstream conformance suite execution against the generated input'],
  });
}

export function createDemoProofSurfaceRegistry(): ProofSurfaceRegistry {
  const registry = new ProofSurfaceRegistry();
  const surfaces = [
    governanceSurface(),
    runtimeSurface(),
    opsConsoleSurface(),
    novaStudioSurface(),
    cisStandardsHierarchySurface(),
    cisStandardsTraceabilityMatrixSurface(),
    cisCompanionRegistrySurface(),
    artifactGovernanceSurface(),
    sovereignRouterPricingSurface(),
    externalStandardsMappingSurface(),
    cisConformanceGenerationSurface(),
  ];
  for (const surface of surfaces) {
    registry.publish(surface);
  }
  return registry;
}

export function listProofSurfaceSummaries(
  registry: ProofSurfaceRegistry = createDemoProofSurfaceRegistry(),
): ProofSurfaceSummary[] {
  const surfaces = registry.list();
  return surfaces.map((surface) => deriveProofSurfaceSummary(surface, surfaces));
}
