import { runEvidenceLoop } from "../src/index";

const handlers = {
  async receiveObservation() {
    return {
      id: `obs-${Date.now()}`,
      observerId: "observer-1",
      timestamp: new Date().toISOString(),
      domain: "demo",
      description: "Demo observation",
    };
  },

  async buildCase(obs: { observerId: string; domain: string }) {
    return {
      id: `case-${Date.now()}`,
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
      id: `audit-${Date.now()}`,
      subjectId: "demo",
      subjectType: "case",
      createdAt: new Date().toISOString(),
      createdBy: "observer-1",
      evidence: [],
      conclusion: "valid" as const,
      rationale: "Demo audit",
    };
  },

  async planTransfer(audit: { id: string }) {
    return {
      id: `transfer-${Date.now()}`,
      fromContext: "demo-A",
      toContext: "demo-B",
      createdAt: new Date().toISOString(),
      createdBy: "observer-1",
      audits: [audit],
      summary: "Demo transfer",
      medium: "doc" as const,
    };
  },

  async deriveExtension() {
    return null;
  },

  async persistAll(objects: unknown) {
    console.log("Persisted:", objects);
  },
};

runEvidenceLoop(handlers).then(() => {
  console.log("Demo evidence loop complete.");
});
