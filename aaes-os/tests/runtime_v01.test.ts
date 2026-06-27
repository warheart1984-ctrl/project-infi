import { randomUUID } from "node:crypto";
import assert from "node:assert/strict";
import { describe, it } from "vitest";

import {
  emitEvent,
  GovernanceViolationError,
  InMemoryTraceStore,
  reconstructSpan,
  runV01Demo,
} from "../src/runtime/v01/index.js";
import type {
  DecisionEvent,
  ExecutionEvent,
  IntentEvent,
  ResultEvent,
} from "../src/runtime/v01/types.js";

function now(): string {
  return new Date().toISOString();
}

describe("AAES-OS v0.1 governed runtime", () => {
  it("proves valid Intent → Decision → Execution → Result → Reconstruction", () => {
    const store = new InMemoryTraceStore();
    const span = randomUUID();

    emitEvent(
      "USER",
      {
        id: randomUUID(),
        span_id: span,
        type: "INTENT",
        timestamp: now(),
        actor: "user",
        payload: { request: "Analyze this request" },
      } satisfies IntentEvent,
      store,
    );

    emitEvent(
      "RUNTIME",
      {
        id: randomUUID(),
        span_id: span,
        type: "DECISION",
        timestamp: now(),
        actor: "runtime",
        payload: { decision: "select_analysis_workflow" },
      } satisfies DecisionEvent,
      store,
    );

    emitEvent(
      "EXECUTOR",
      {
        id: randomUUID(),
        span_id: span,
        type: "EXECUTION",
        timestamp: now(),
        actor: "executor",
        payload: { action: "run_analysis", status: "COMPLETED" },
      } satisfies ExecutionEvent,
      store,
    );

    emitEvent(
      "EXECUTOR",
      {
        id: randomUUID(),
        span_id: span,
        type: "RESULT",
        timestamp: now(),
        actor: "executor",
        payload: { outcome: { summary: "analysis output" }, status: "SUCCESS" },
      } satisfies ResultEvent,
      store,
    );

    const recon = reconstructSpan(store, span);
    assert.equal(recon.intent?.payload.request, "Analyze this request");
    assert.equal(recon.decision?.payload.decision, "select_analysis_workflow");
    assert.equal(recon.execution[0]?.payload.action, "run_analysis");
    assert.deepEqual(recon.result?.payload.outcome, { summary: "analysis output" });
  });

  it("rejects G2: RESULT without EXECUTION", () => {
    const store = new InMemoryTraceStore();
    assert.throws(
      () =>
        emitEvent(
          "EXECUTOR",
          {
            id: randomUUID(),
            span_id: randomUUID(),
            type: "RESULT",
            timestamp: now(),
            actor: "executor",
            payload: { outcome: {}, status: "SUCCESS" },
          } satisfies ResultEvent,
          store,
        ),
      (error: unknown) =>
        error instanceof GovernanceViolationError && error.code === "G2_VIOLATION",
    );
  });

  it("rejects G1: EXECUTION without DECISION", () => {
    const store = new InMemoryTraceStore();
    const span = randomUUID();

    emitEvent(
      "USER",
      {
        id: randomUUID(),
        span_id: span,
        type: "INTENT",
        timestamp: now(),
        actor: "user",
        payload: { request: "x" },
      } satisfies IntentEvent,
      store,
    );

    assert.throws(
      () =>
        emitEvent(
          "EXECUTOR",
          {
            id: randomUUID(),
            span_id: span,
            type: "EXECUTION",
            timestamp: now(),
            actor: "executor",
            payload: { action: "run", status: "STARTED" },
          } satisfies ExecutionEvent,
          store,
        ),
      (error: unknown) =>
        error instanceof GovernanceViolationError && error.code === "G1_VIOLATION",
    );
  });

  it("rejects G3: DECISION without INTENT", () => {
    const store = new InMemoryTraceStore();
    assert.throws(
      () =>
        emitEvent(
          "RUNTIME",
          {
            id: randomUUID(),
            span_id: randomUUID(),
            type: "DECISION",
            timestamp: now(),
            actor: "runtime",
            payload: { decision: "orphan" },
          } satisfies DecisionEvent,
          store,
        ),
      (error: unknown) =>
        error instanceof GovernanceViolationError && error.code === "G3_VIOLATION",
    );
  });

  it("rejects authority: RUNTIME cannot emit INTENT", () => {
    const store = new InMemoryTraceStore();
    assert.throws(
      () =>
        emitEvent(
          "RUNTIME",
          {
            id: randomUUID(),
            span_id: randomUUID(),
            type: "INTENT",
            timestamp: now(),
            actor: "runtime",
            payload: { request: "fake user intent" },
          } satisfies IntentEvent,
          store,
        ),
      (error: unknown) =>
        error instanceof GovernanceViolationError &&
        error.code === "AUTHORITY_VIOLATION",
    );
  });

  it("demo reports valid trace and governance rejections", () => {
    const result = runV01Demo();
    assert.match(result.validSummary, /VALID TRACE/);
    assert.match(result.validSummary, /Analyze this request/);
    assert.equal(result.g2Rejected, true);
    assert.equal(result.authorityRejected, true);
  });
});
