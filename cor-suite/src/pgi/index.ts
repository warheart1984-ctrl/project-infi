import type { CarArtifactKind, CarRegistry } from "../types/car.js";
import type { Pgi, PgiEdge, PgiEdgeRelation, PgiNodeKind } from "../types/pgi.js";
import { writeJsonOutput } from "../lib/io.js";
import { COR_SUITE_PATHS } from "../paths.js";
import { loadCarRegistry } from "../car/registry.js";

const PGI_NODE_KINDS: Set<CarArtifactKind> = new Set([
  "requirement",
  "specification",
  "implementation",
  "verification",
  "evidence",
  "governance_receipt",
]);

function relationForKind(kind: CarArtifactKind): PgiEdgeRelation {
  switch (kind) {
    case "implementation":
      return "implements";
    case "verification":
      return "verifies";
    case "evidence":
      return "evidences";
    default:
      return "related";
  }
}

/** Build PGI-1.0 from CAR link graph + namespace structural edges. */
export function buildPgi(car: CarRegistry): Pgi {
  const nodes = car.artifacts
    .filter((a) => PGI_NODE_KINDS.has(a.kind))
    .map((a) => ({
      id: a.id,
      kind: a.kind as PgiNodeKind,
      path: a.path,
    }));

  const edges: PgiEdge[] = [];
  const seen = new Set<string>();

  const pushEdge = (edge: PgiEdge): void => {
    const key = `${edge.from}|${edge.to}|${edge.relation}`;
    if (seen.has(key)) return;
    seen.add(key);
    edges.push(edge);
  };

  for (const a of car.artifacts) {
    if (a.links?.supersedes) {
      for (const target of a.links.supersedes) {
        pushEdge({ from: a.id, to: target, relation: "supersedes" });
      }
    }
    if (a.links?.related) {
      for (const target of a.links.related) {
        pushEdge({ from: a.id, to: target, relation: "related" });
      }
    }
  }

  const requirementsByNamespace = new Map<string, string[]>();
  for (const a of car.artifacts) {
    if (a.kind !== "requirement") continue;
    const list = requirementsByNamespace.get(a.namespace) ?? [];
    list.push(a.id);
    requirementsByNamespace.set(a.namespace, list);
  }

  for (const a of car.artifacts) {
    if (a.kind === "requirement" || !PGI_NODE_KINDS.has(a.kind)) continue;
    const reqIds = requirementsByNamespace.get(a.namespace) ?? [];
    for (const reqId of reqIds) {
      pushEdge({ from: a.id, to: reqId, relation: relationForKind(a.kind) });
    }
  }

  return {
    pgiVersion: "1.0.0",
    generatedAt: new Date().toISOString(),
    nodes,
    edges,
  };
}

export function emitPgi(car?: CarRegistry): string {
  const registry = car ?? loadCarRegistry();
  const pgi = buildPgi(registry);
  return writeJsonOutput(COR_SUITE_PATHS.outputs.pgi, pgi);
}
