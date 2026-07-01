import type { CarRegistry } from "../types/car.js";
import type { DraReport } from "../types/dra.js";
import type { Pgi } from "../types/pgi.js";
import { writeJsonOutput } from "../lib/io.js";
import { COR_SUITE_PATHS } from "../paths.js";
import { loadCarRegistry } from "../car/registry.js";
import { buildPgi } from "../pgi/index.js";

/** DRA-1.0: dependency risk from PGI topology + CAR lifecycle. */
export function computeDra(car: CarRegistry, pgi: Pgi): DraReport {
  const risk: DraReport["risk"] = {};

  for (const node of pgi.nodes) {
    if (node.kind !== "requirement") continue;

    const id = node.id;
    const fanIn = pgi.edges.filter((e) => e.to === id).length;
    const fanOut = pgi.edges.filter((e) => e.from === id).length;
    const dependencyDepth = fanIn + fanOut;

    const verificationGaps =
      car.artifacts.filter(
        (a) => a.kind === "verification" && a.links?.related?.includes(id),
      ).length === 0
        ? 1
        : 0;

    const deprecatedDependencies = car.artifacts.filter(
      (a) => a.status === "deprecated" && a.links?.related?.includes(id),
    ).length;

    const score =
      dependencyDepth * 2 +
      fanIn * 1.5 +
      fanOut * 1 +
      verificationGaps * 3 +
      deprecatedDependencies * 4;

    risk[id] = {
      requirementId: id,
      dependencyDepth,
      fanIn,
      fanOut,
      verificationGaps,
      deprecatedDependencies,
      score,
    };
  }

  return {
    draVersion: "1.0.0",
    generatedAt: new Date().toISOString(),
    risk,
  };
}

export function emitDra(car?: CarRegistry, pgi?: Pgi): string {
  const registry = car ?? loadCarRegistry();
  const graph = pgi ?? buildPgi(registry);
  const report = computeDra(registry, graph);
  return writeJsonOutput(COR_SUITE_PATHS.outputs.draReport, report);
}
