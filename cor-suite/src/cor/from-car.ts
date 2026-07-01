import type { CarArtifact, CarRegistry } from "../types/car.js";
import type { ArtifactRef, CorRequirement, CorStateVector, MaturityLevel } from "../types/cor.js";
import { tryGitCommit } from "../lib/io.js";

function toArtifactRef(entry: CarArtifact): ArtifactRef {
  return { path: entry.path, type: entry.kind, hash: entry.hash };
}

function inferMaturity(
  spec: ArtifactRef[],
  impl: ArtifactRef[],
  verification: ArtifactRef[],
): MaturityLevel {
  if (verification.length > 0 && impl.length > 0) return "verified";
  if (impl.length > 0) return "implemented";
  if (spec.length > 0) return "normative";
  return "normative";
}

function activeArtifacts(car: CarRegistry, kind: CarArtifact["kind"]): CarArtifact[] {
  return car.artifacts.filter((a) => a.kind === kind && a.status === "active");
}

function requirementEntries(car: CarRegistry): CarArtifact[] {
  const explicit = activeArtifacts(car, "requirement");
  if (explicit.length > 0) return explicit;

  const namespaces = new Set(
    car.artifacts
      .filter((a) => a.status === "active" && a.kind !== "schema" && a.kind !== "registry")
      .map((a) => a.namespace),
  );

  return [...namespaces].map((namespace) => ({
    id: `${namespace}.CORE`,
    namespace,
    kind: "requirement" as const,
    version: "1.0.0",
    status: "active" as const,
    authority: namespace,
    path: `cor-suite/car/requirements/${namespace.toLowerCase()}.md`,
    hash: "",
  }));
}

function artifactsForNamespace(car: CarRegistry, namespace: string, kind: CarArtifact["kind"]): CarArtifact[] {
  return car.artifacts.filter((a) => a.namespace === namespace && a.kind === kind && a.status === "active");
}

export function buildCorStateFromCar(car: CarRegistry): CorStateVector {
  const requirements: CorRequirement[] = requirementEntries(car).map((req) => {
    const ns = req.namespace;
    const specArtifacts = artifactsForNamespace(car, ns, "specification").map(toArtifactRef);
    const implArtifacts = artifactsForNamespace(car, ns, "implementation").map(toArtifactRef);
    const verificationArtifacts = artifactsForNamespace(car, ns, "verification").map(toArtifactRef);
    const evidenceArtifacts = artifactsForNamespace(car, ns, "evidence").map(toArtifactRef);

    return {
      id: req.id,
      authority: req.authority ?? ns,
      specArtifacts,
      implArtifacts,
      verificationArtifacts,
      evidence: evidenceArtifacts.map((a, i) => ({
        id: `${req.id}-EV-${i + 1}`,
        type: "artifact",
        artifact: a,
      })),
      provenance: [],
      reproductionStatus: "not_attempted",
      maturity: inferMaturity(specArtifacts, implArtifacts, verificationArtifacts),
    };
  });

  const allImpl = activeArtifacts(car, "implementation").map((a) => a.path);
  const allVer = activeArtifacts(car, "verification").map((a) => a.path);
  const linkedImpl = new Set(requirements.flatMap((r) => r.implArtifacts.map((a) => a.path)));
  const linkedVer = new Set(requirements.flatMap((r) => r.verificationArtifacts.map((a) => a.path)));

  const missingArtifacts: CorStateVector["structuralIntegrity"]["missingArtifacts"] = [];
  for (const req of requirements) {
    if (req.implArtifacts.length > 0 && req.verificationArtifacts.length === 0) {
      missingArtifacts.push({ expectedForRequirement: req.id, kind: "verification" });
    }
    if (req.implArtifacts.length === 0 && req.specArtifacts.length > 0) {
      missingArtifacts.push({ expectedForRequirement: req.id, kind: "impl" });
    }
  }

  const specIndex = activeArtifacts(car, "specification").map(toArtifactRef);
  const implIndex = activeArtifacts(car, "implementation").map(toArtifactRef);
  const verIndex = activeArtifacts(car, "verification").map(toArtifactRef);
  const evIndex = activeArtifacts(car, "evidence").map(toArtifactRef);

  return {
    corVersion: "1.0.0",
    generatedAt: new Date().toISOString(),
    commit: tryGitCommit(),
    requirements,
    artifactIndex: {
      specifications: specIndex,
      implementations: implIndex,
      verifications: verIndex,
      evidence: evIndex,
    },
    structuralIntegrity: {
      orphans: {
        requirements: [],
        implementations: allImpl.filter((p) => !linkedImpl.has(p)),
        verifications: allVer.filter((p) => !linkedVer.has(p)),
      },
      missingArtifacts,
      brokenLineage: [],
      unresolvedAssumptions: [],
    },
  };
}
