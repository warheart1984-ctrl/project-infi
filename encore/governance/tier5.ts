import { api, APIError } from "encore.dev/api";
import { secret } from "encore.dev/config";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

/** Repo root where AAIS writes `.runtime/governance/tier5_health.json`. */
const aaisRepoRoot = secret("AAIS_REPO_ROOT");

/** Mirrors `AdaptiveEngine.health_check()` output (AAIS Tier 5 contract). */
export interface PendingPromotion {
  gene: string;
  from: string;
  to: string;
  failures: string[];
}

export interface MutationProposal {
  mp_id: string;
  gene: string;
  status: string;
}

export interface Tier5HealthReport {
  genome_count: number;
  stage_histogram: Record<string, number>;
  tier5_enabled_genes: string[];
  pending_promotions: PendingPromotion[];
  mutation_proposals: MutationProposal[];
  retirement_steps: Record<string, string>;
  adaptive_lanes_awakened?: boolean;
  adaptive_lane_count?: number;
}

export interface Tier5HealthResponse {
  source: "tier5_health.json";
  path: string;
  report: Tier5HealthReport;
}

const tier5HealthPath = () =>
  join(aaisRepoRoot(), ".runtime", "governance", "tier5_health.json");

/** Typed read of the Tier 5 self-audit artifact written by Python governance gates. */
export const getTier5Health = api(
  { method: "GET", path: "/governance/tier5/health", expose: true },
  async (): Promise<Tier5HealthResponse> => {
    const path = tier5HealthPath();
    let raw: string;
    try {
      raw = await readFile(path, "utf8");
    } catch {
      throw APIError.notFound(
        "tier5_health.json not found — run `make tier5-gate` or Tier5Governance.health_check() in project-infi first",
        { path }
      );
    }

    let report: Tier5HealthReport;
    try {
      report = JSON.parse(raw) as Tier5HealthReport;
    } catch {
      throw APIError.internal("tier5_health.json is not valid JSON", { path });
    }

    return { source: "tier5_health.json", path, report };
  }
);
