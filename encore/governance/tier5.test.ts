import { describe, expect, it } from "vitest";
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const repoRoot = join(__dirname, "..", "..");
const healthPath = join(repoRoot, ".runtime", "governance", "tier5_health.json");

describe("tier5 health artifact", () => {
  it("matches AAIS contract fields when gate has run", () => {
    if (!existsSync(healthPath)) {
      return; // skip until `make tier5-gate` has been run locally
    }
    const report = JSON.parse(readFileSync(healthPath, "utf8"));
    expect(report.genome_count).toBeGreaterThan(0);
    expect(report.stage_histogram).toBeTypeOf("object");
    expect(Array.isArray(report.tier5_enabled_genes)).toBe(true);
    expect(Array.isArray(report.pending_promotions)).toBe(true);
  });
});
