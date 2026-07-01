import type { ArtifactRef, CorRequirement, MaturityLevel } from "../types/cor.js";

/** Path prefix → requirement namespace (Phase 2 mapping). */
export const REQUIREMENT_NAMESPACES: Array<{ prefix: string; namespace: string; authority: string }> = [
  { prefix: "aaes-os/packages/runledger/", namespace: "RUNLEDGER", authority: "aaes-os" },
  { prefix: "aaes-os/packages/trace-bus/", namespace: "TRACEBUS", authority: "aaes-os" },
  { prefix: "aaes-os/packages/aaes-governance/", namespace: "GOV", authority: "aaes-os" },
  { prefix: "aaes-os/packages/ucr-runtime/", namespace: "UCR", authority: "aaes-os" },
  { prefix: "aaes-os/packages/tri-core-protocol/", namespace: "TRICORE", authority: "aaes-os" },
  { prefix: "aaes-os/services/ops-console/", namespace: "OPSCONSOLE", authority: "aaes-os" },
  { prefix: "aaes-os/tests/", namespace: "AAES-TEST", authority: "aaes-os" },
  { prefix: "operator-surface/", namespace: "OPSURF", authority: "operator-surface" },
  { prefix: "frontend/", namespace: "UI", authority: "frontend" },
];

function normalizePath(p: string): string {
  return p.replace(/\\/g, "/");
}

export function resolveNamespace(filePath: string): { namespace: string; authority: string } | null {
  const rel = normalizePath(filePath);
  for (const row of REQUIREMENT_NAMESPACES) {
    if (rel.startsWith(row.prefix)) {
      return { namespace: row.namespace, authority: row.authority };
    }
  }
  return null;
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

export function buildRequirementsFromArtifacts(input: {
  specArtifacts: ArtifactRef[];
  implArtifacts: ArtifactRef[];
  verificationArtifacts: ArtifactRef[];
  evidenceArtifacts: ArtifactRef[];
}): CorRequirement[] {
  const buckets = new Map<
    string,
    {
      authority: string;
      spec: ArtifactRef[];
      impl: ArtifactRef[];
      verification: ArtifactRef[];
      evidence: ArtifactRef[];
    }
  >();

  const assign = (artifacts: ArtifactRef[], kind: "spec" | "impl" | "verification" | "evidence") => {
    for (const artifact of artifacts) {
      const ns = resolveNamespace(artifact.path);
      if (!ns) continue;
      const reqId = `${ns.namespace}.CORE`;
      let bucket = buckets.get(reqId);
      if (!bucket) {
        bucket = { authority: ns.authority, spec: [], impl: [], verification: [], evidence: [] };
        buckets.set(reqId, bucket);
      }
      if (kind === "spec") bucket.spec.push(artifact);
      if (kind === "impl") bucket.impl.push(artifact);
      if (kind === "verification") bucket.verification.push(artifact);
      if (kind === "evidence") bucket.evidence.push(artifact);
    }
  };

  assign(input.specArtifacts, "spec");
  assign(input.implArtifacts, "impl");
  assign(input.verificationArtifacts, "verification");
  assign(input.evidenceArtifacts, "evidence");

  return [...buckets.entries()].map(([id, bucket]) => ({
    id,
    authority: bucket.authority,
    specArtifacts: bucket.spec,
    implArtifacts: bucket.impl,
    verificationArtifacts: bucket.verification,
    evidence: bucket.evidence.map((a, i) => ({
      id: `${id}-EV-${i + 1}`,
      type: "artifact",
      artifact: a,
    })),
    provenance: [],
    reproductionStatus: "not_attempted" as const,
    maturity: inferMaturity(bucket.spec, bucket.impl, bucket.verification),
  }));
}

export function findOrphanImplementations(
  implArtifacts: ArtifactRef[],
  requirements: CorRequirement[],
): string[] {
  const linked = new Set(requirements.flatMap((r) => r.implArtifacts.map((a) => a.path)));
  return implArtifacts.map((a) => a.path).filter((p) => !linked.has(p));
}

export function findOrphanVerifications(
  verificationArtifacts: ArtifactRef[],
  requirements: CorRequirement[],
): string[] {
  const linked = new Set(requirements.flatMap((r) => r.verificationArtifacts.map((a) => a.path)));
  return verificationArtifacts.map((a) => a.path).filter((p) => !linked.has(p));
}

export function findMissingArtifacts(requirements: CorRequirement[]): Array<{
  expectedForRequirement: string;
  kind: "spec" | "impl" | "verification" | "evidence";
}> {
  const missing: Array<{ expectedForRequirement: string; kind: "spec" | "impl" | "verification" | "evidence" }> = [];
  for (const req of requirements) {
    if (req.implArtifacts.length > 0 && req.verificationArtifacts.length === 0) {
      missing.push({ expectedForRequirement: req.id, kind: "verification" });
    }
    if (req.implArtifacts.length === 0 && req.specArtifacts.length > 0) {
      missing.push({ expectedForRequirement: req.id, kind: "impl" });
    }
  }
  return missing;
}
