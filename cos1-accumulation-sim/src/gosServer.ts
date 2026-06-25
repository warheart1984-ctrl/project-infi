import express from "express";
import type { GameEvent, ValidationContext, WorldChangeProposal } from "./domain.js";
import {
  initialState,
  applyEvent,
  registerChange,
  runPostAcceptanceValidation,
  recordConsequence,
} from "./state.js";
import { gameEventToJPSS } from "./gameAdapter.js";
import type { RAState } from "./domain.js";
import { toContinuityHealthResponse } from "./gosAdapter.js";
import { proposalToLineageChange } from "./changeAdapter.js";
import { InMemoryContinuityLedger } from "./ledger/continuityLedger.js";

async function main() {
  let state: RAState = initialState();
  const app = express();
  app.use(express.json());

  app.post("/events", (req, res) => {
    const ev = req.body as GameEvent;
    if (!ev?.id || !ev?.actorId || !ev?.timestamp) {
      res.status(400).json({ error: "Missing required fields: id, actorId, timestamp" });
      return;
    }
    const jpssEv = gameEventToJPSS(ev);
    state = applyEvent(state, jpssEv);
    const stored = state.events[state.events.length - 1];
    res.status(202).json({
      ok: true,
      eventId: ev.id,
      origin: stored?.origin ?? null,
      mode: stored?.mode ?? null,
    });
  });

  app.get("/continuity/health", (_req, res) => {
    res.json(toContinuityHealthResponse(state));
  });

  app.get("/world/history", (_req, res) => {
    res.json({
      events: state.events,
      eventOrigins: state.eventOrigins,
      ledgerCycles: state.ledgerCycles,
      cycleDrafts: state.cycleDrafts,
      capabilityProfiles: state.capabilityProfiles,
      changes: state.changes,
      ledger: state.ledger,
      continuity: state.continuity,
    });
  });

  app.get("/ledger/cycles", async (_req, res) => {
    const store = InMemoryContinuityLedger.fromArray(state.ledgerCycles);
    res.json({ cycles: await store.getAllCycles() });
  });

  app.get("/ledger/cycles/:id", async (req, res) => {
    const store = InMemoryContinuityLedger.fromArray(state.ledgerCycles);
    const cycle = await store.getCycle(req.params.id);
    if (!cycle) {
      res.status(404).json({ error: "Cycle not found" });
      return;
    }
    res.json(cycle);
  });

  app.get("/ledger/thresholds", async (_req, res) => {
    const store = InMemoryContinuityLedger.fromArray(state.ledgerCycles);
    res.json({ thresholds: await store.getThresholdViews() });
  });

  app.get("/ledger/thresholds/:id/recalibrations", async (req, res) => {
    const store = InMemoryContinuityLedger.fromArray(state.ledgerCycles);
    res.json({
      recalibrations: await store.getRecalibrationViews(req.params.id),
    });
  });

  app.post("/world/changes", (req, res) => {
    const proposal = req.body as WorldChangeProposal;
    if (!proposal?.id || !proposal?.description || !proposal?.proposedBy || !proposal?.origin) {
      res.status(400).json({
        error: "Missing required fields: id, description, proposedBy, origin",
      });
      return;
    }
    const change = proposalToLineageChange(proposal);
    state = registerChange(state, change);
    res.status(202).json({
      ok: true,
      changeId: change.id,
      status: "PROVISIONAL",
      origin: proposal.origin,
    });
  });

  app.post("/world/changes/:id/validate", (req, res) => {
    const changeId = req.params.id;
    if (!state.changes[changeId]) {
      res.status(404).json({ error: "Change not found" });
      return;
    }
    const ctx = req.body as ValidationContext;
    const baseline = typeof req.body?.baseline === "number" ? req.body.baseline : 0.5;

    state = runPostAcceptanceValidation(state, changeId, ctx, baseline);

    res.json({
      ok: true,
      changeId,
      status: state.changes[changeId]?.status,
      ledger: state.ledger[changeId],
    });
  });

  app.post("/world/changes/:id/consequences", (req, res) => {
    const changeId = req.params.id;
    if (!state.changes[changeId]) {
      res.status(404).json({ error: "Change not found" });
      return;
    }
    const { metric, value, timestamp } = req.body as {
      metric: string;
      value: number;
      timestamp?: string;
    };
    if (!metric || value === undefined) {
      res.status(400).json({ error: "Missing metric or value" });
      return;
    }
    state = recordConsequence(
      state,
      changeId,
      metric,
      value,
      timestamp ?? new Date().toISOString(),
    );
    res.status(201).json({ ok: true, changeId, metric, value });
  });

  app.listen(4000, () => {
    console.log("GOS-1 server on http://localhost:4000");
  });
}

main();
