import { test } from "node:test";
import assert from "node:assert/strict";
import { runEvidenceLoop } from "../src/ra-cos1/evidence-loop";

test("evidence loop processes observations", async () => {
  let processed = false;

  const handlers = {
    async receiveObservation() {
      if (processed) return null;
      processed = true;
      return {
        id: "obs-1",
        observerId: "obs",
        timestamp: new Date().toISOString(),
        domain: "test",
        description: "test observation",
      };
    },
    async buildCase(obs: { observerId: string; domain: string }) {
      return {
        id: "case-1",
        createdAt: new Date().toISOString(),
        createdBy: obs.observerId,
        observations: [],
        domain: obs.domain,
        status: "open" as const,
      };
    },
    async generateEvidence() {
      return [];
    },
    async runAudit() {
      return {
        id: "audit-1",
        subjectId: "case-1",
        subjectType: "case",
        createdAt: new Date().toISOString(),
        createdBy: "obs",
        evidence: [],
        conclusion: "valid" as const,
        rationale: "ok",
      };
    },
    async planTransfer() {
      return {
        id: "transfer-1",
        fromContext: "A",
        toContext: "B",
        createdAt: new Date().toISOString(),
        createdBy: "obs",
        audits: [],
        summary: "transfer",
        medium: "doc" as const,
      };
    },
    async deriveExtension() {
      return null;
    },
    async persistAll() {},
  };

  await runEvidenceLoop(handlers);
  assert.ok(processed);
});
