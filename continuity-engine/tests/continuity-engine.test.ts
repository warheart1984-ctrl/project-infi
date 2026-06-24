import assert from "node:assert/strict";
import { beforeEach, describe, it } from "node:test";
import {
  InMemoryThresholdRegistry,
  RecalibrationGovernanceEngine,
  defaultInvariantSet,
  detectRecalibrationTriggers,
  applyDeltaWithCRKGuard,
  pullThresholdHistory,
  emitThresholdChartSpec,
  generateLineageReport,
  diffThresholdDelta,
  processRACosEvent,
  createInterpretiveStore,
  recordObservation,
  proposeProtoThreshold,
  advanceProtoToTesting,
  adoptProtoThreshold,
} from "../src/index.js";

describe("ThresholdRegistry", () => {
  let registry: InMemoryThresholdRegistry;

  beforeEach(() => {
    registry = new InMemoryThresholdRegistry();
  });

  it("creates threshold at version 1 with history", async () => {
    const th = await registry.create({
      id: "T_incident_escalation_001",
      name: "Incident escalation threshold",
      domain: "Org.incident",
      metric: "incidents_per_24h",
      comparator: ">",
      value: 5,
      unit: "count",
      intent: "Escalate to governance if more than 5 incidents occur in 24 hours.",
      createdBy: "Founder",
      lastUpdatedBy: "Founder",
    });
    assert.equal(th.version, 1);
    assert.equal(th.active, true);
    const hist = await registry.getHistory(th.id);
    assert.equal(hist.length, 1);
    assert.equal(hist[0]!.deltaRationale, "initial");
  });

  it("applies delta and increments version", async () => {
    const th = await registry.create({
      id: "T1",
      name: "t",
      domain: "Org.incident",
      metric: "incidents_per_24h",
      comparator: ">",
      value: 5,
      intent: "test",
      createdBy: "Founder",
      lastUpdatedBy: "Founder",
    });
    const updated = await registry.applyDelta(
      {
        thresholdId: th.id,
        before: th,
        after: { value: 3 },
        rationale: "Earlier escalation",
        recalibrationEventId: "recal-2026-06-23-001",
      },
      "WhiteTeam:ContinuityCouncil",
    );
    assert.equal(updated.value, 3);
    assert.equal(updated.version, 2);
    const hist = await pullThresholdHistory(registry, th.id);
    assert.equal(hist.length, 2);
    assert.equal(hist[1]!.recalibrationEventId, "recal-2026-06-23-001");
  });
});

describe("Worked example #1 — approved recalibration (5 → 3)", () => {
  it("approves incident threshold tightening after late interventions", async () => {
    const registry = new InMemoryThresholdRegistry();
    const governance = new RecalibrationGovernanceEngine();

    const th = await registry.create({
      id: "T_incident_escalation_001",
      name: "Incident escalation threshold",
      domain: "Org.incident",
      metric: "incidents_per_24h",
      comparator: ">",
      value: 5,
      unit: "count",
      intent: "Escalate to governance if more than 5 incidents occur in 24 hours.",
      createdBy: "Founder",
      lastUpdatedBy: "Founder",
    });

    const validation = {
      lateInterventionsForThreshold: { [th.id]: 7 },
    };

    const triggers = await detectRecalibrationTriggers(
      { domain: "Org.incident", metric: "incidents_per_24h" },
      {},
      validation,
      registry,
    );
    assert.equal(
      triggers.some((t) => t.reason === "late_intervention"),
      true,
    );

    const delta = {
      thresholdId: th.id,
      before: th,
      after: { value: 3 },
      rationale:
        "Escalation at >5 incidents per 24h is too late; repeated severe failures suggest earlier intervention at >3.",
      recalibrationEventId: "recal-2026-06-23-001",
    };

    const event = await governance.evaluate({
      delta,
      invSet: defaultInvariantSet,
      evidence: triggers[0]!.evidence,
    });
    assert.equal(event.decision, "approved");

    const updated = await registry.applyDelta(delta, event.decidedBy);
    assert.equal(updated.value, 3);
    assert.equal(updated.version, 2);
  });
});

describe("Worked example #2 — rejected by CRK-1 (safety 0 → 3)", () => {
  it("blocks weakening safety halt threshold", async () => {
    const registry = new InMemoryThresholdRegistry();
    const governance = new RecalibrationGovernanceEngine();

    const th = await registry.create({
      id: "T_safety_override_001",
      name: "Safety override threshold",
      domain: "Safety.core",
      metric: "safety_violations_per_hour",
      comparator: ">",
      value: 0,
      intent: "Any safety violation triggers immediate halt.",
      createdBy: "Founder",
      lastUpdatedBy: "Founder",
    });

    const delta = {
      thresholdId: th.id,
      before: th,
      after: { value: 3 },
      rationale: "Reduce unnecessary halts and improve productivity.",
      recalibrationEventId: "recal-2026-06-23-002",
    };

    const event = await governance.evaluate({
      delta,
      invSet: defaultInvariantSet,
      evidence: ["halt frequency high"],
      triggerType: "other",
    });

    assert.equal(event.decision, "rejected");
    assert.ok(event.legitimacyBasis.includes("INV_001_HALT_ON_SAFETY"));

    const guard = await applyDeltaWithCRKGuard(
      registry,
      delta,
      "Manager",
      defaultInvariantSet,
    );
    assert.equal(guard.applied, false);

    const current = await registry.getById(th.id);
    assert.equal(current!.value, 0);
    assert.equal(current!.version, 1);
  });
});

describe("Lineage tooling", () => {
  it("emits chart spec and markdown report", async () => {
    const registry = new InMemoryThresholdRegistry();
    const th = await registry.create({
      id: "T_incident_escalation_001",
      name: "Incident escalation",
      domain: "Org.incident",
      metric: "incidents_per_24h",
      comparator: ">",
      value: 5,
      intent: "Escalate",
      createdBy: "Founder",
      lastUpdatedBy: "Founder",
    });
    await registry.applyDelta(
      {
        thresholdId: th.id,
        before: th,
        after: { value: 3 },
        rationale: "Earlier escalation reduces severe cascades.",
        recalibrationEventId: "recal-2026-06-23-001",
      },
      "ContinuityCouncil",
    );

    const history = await pullThresholdHistory(registry, th.id);
    const spec = emitThresholdChartSpec(history);
    assert.equal(spec.type, "line-chart");
    assert.equal(spec.points.length, 2);
    assert.equal(spec.points[1]!.value, 3);

    const md = generateLineageReport(history);
    assert.ok(md.includes("T_incident_escalation_001"));
    assert.ok(md.includes("recal-2026-06-23-001"));
  });

  it("diffs threshold delta fields", () => {
    const before = {
      id: "T1",
      name: "t",
      domain: "d",
      metric: "m",
      comparator: ">" as const,
      value: 5,
      intent: "old intent",
      version: 1,
      active: true,
      createdAt: "",
      createdBy: "",
      lastUpdatedAt: "",
      lastUpdatedBy: "",
    };
    const diff = diffThresholdDelta({
      thresholdId: "T1",
      before,
      after: { value: 3 },
      rationale: "test",
    });
    assert.equal(diff.changes.length, 1);
    assert.equal(diff.changes[0]!.field, "value");
  });
});

describe("Interpretive stewardship", () => {
  it("promotes ProtoThreshold to operational Threshold", async () => {
    const store = createInterpretiveStore();
    const registry = new InMemoryThresholdRegistry();

    recordObservation(store, {
      id: "obs-1",
      domain: "Governance.stewardship",
      description: "Stewards avoid hard decisions",
      evidence: ["missed sessions", "deferred votes"],
      proposedBy: "GoldTeam",
    });

    proposeProtoThreshold(store, {
      id: "proto-1",
      patternId: "obs-1",
      domain: "Governance.stewardship",
      metric: "steward_disengagement_score",
      comparator: ">",
      value: 0.6,
      intent: "Flag steward disengagement before continuity erosion.",
      proposedBy: "InterpretiveSteward",
    });

    advanceProtoToTesting(store, "proto-1");

    const result = await adoptProtoThreshold(store, registry, "proto-1", {
      id: "T_steward_disengagement_001",
      name: "Steward disengagement",
      createdBy: "ContinuityCouncil",
    });

    assert.notEqual(result, null);
    assert.equal(result!.threshold.metric, "steward_disengagement_score");
    assert.equal(result!.pattern.status, "formalized");
    assert.equal(result!.proto.status, "adopted");
  });
});

describe("RA-COS loop integration", () => {
  it("processes late_intervention trigger and updates registry when approved", async () => {
    const registry = new InMemoryThresholdRegistry();
    const approved: number[] = [];

    await registry.create({
      id: "T_incident_escalation_001",
      name: "Incident",
      domain: "Org.incident",
      metric: "incidents_per_24h",
      comparator: ">",
      value: 5,
      intent: "escalate",
      createdBy: "Founder",
      lastUpdatedBy: "Founder",
    });

    const { events } = await processRACosEvent(
      {
        registry,
        governance: new RecalibrationGovernanceEngine(),
        invariantSet: defaultInvariantSet,
        onApproved: () => approved.push(1),
      },
      { domain: "Org.incident", metric: "incidents_per_24h" },
      {},
      { lateInterventionsForThreshold: { T_incident_escalation_001: 6 } },
    );

    assert.equal(
      events.some((e) => e.decision === "approved"),
      true,
    );
    assert.ok(approved.length > 0);
    const th = await registry.getById("T_incident_escalation_001");
    assert.equal(th!.value, 4);
    assert.equal(th!.version, 2);
  });
});
