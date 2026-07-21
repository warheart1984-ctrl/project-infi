import { FaultJournal, InvariantEngine, type Invariant } from '@aaes-os/aaes-governance';
import { RunStore } from '@aaes-os/runledger';

import { LIRL_ALLOWED_ACTIONS, type LirlGateResult, type LirlIntent } from './types.js';

function isAllowedAction(action: string): boolean {
  return (LIRL_ALLOWED_ACTIONS as readonly string[]).includes(action);
}

export function createLirlInvariants(): Invariant[] {
  return [
    {
      id: 'LIRL_ACTOR_REQUIRED',
      description: 'Intent must identify a non-empty actorId',
      evaluate: (ctx) => {
        const intent = ctx.input as LirlIntent | undefined;
        const actorId = intent?.actorId?.trim();
        if (!actorId) {
          return {
            passed: false,
            severity: 'error',
            message: 'actorId is required',
          };
        }
        if (actorId.toLowerCase() === 'anonymous') {
          return {
            passed: false,
            severity: 'error',
            message: 'anonymous actor is not lawful under LIRL',
          };
        }
        return { passed: true, severity: 'info', message: 'actorId present' };
      },
    },
    {
      id: 'LIRL_NO_BYPASS',
      description: 'forceBypass and unlawful bypass actions are rejected',
      evaluate: (ctx) => {
        const intent = ctx.input as LirlIntent | undefined;
        if (intent?.forceBypass === true) {
          return {
            passed: false,
            severity: 'fatal',
            message: 'forceBypass is unlawful',
          };
        }
        if (intent?.action === 'unlawful.bypass') {
          return {
            passed: false,
            severity: 'fatal',
            message: 'action unlawful.bypass is forbidden',
          };
        }
        return { passed: true, severity: 'info', message: 'no bypass attempted' };
      },
    },
    {
      id: 'LIRL_ACTION_ALLOWLIST',
      description: 'action must be in LIRL allowlist',
      evaluate: (ctx) => {
        const intent = ctx.input as LirlIntent | undefined;
        const action = intent?.action;
        if (!action || !isAllowedAction(action)) {
          return {
            passed: false,
            severity: 'error',
            message: `action must be one of: ${LIRL_ALLOWED_ACTIONS.join(', ')}`,
          };
        }
        return { passed: true, severity: 'info', message: 'action allowed' };
      },
    },
    {
      id: 'LIRL_MEMORY_WRITE_SHAPE',
      description: 'memory.write requires payload.key and payload.value',
      evaluate: (ctx) => {
        const intent = ctx.input as LirlIntent | undefined;
        if (intent?.action !== 'memory.write') {
          return { passed: true, severity: 'info', message: 'not a memory.write' };
        }
        const key = intent.payload?.key;
        if (typeof key !== 'string' || key.trim().length === 0) {
          return {
            passed: false,
            severity: 'error',
            message: 'memory.write requires non-empty payload.key',
          };
        }
        if (!('value' in (intent.payload ?? {}))) {
          return {
            passed: false,
            severity: 'error',
            message: 'memory.write requires payload.value',
          };
        }
        return { passed: true, severity: 'info', message: 'memory.write shape ok' };
      },
    },
  ];
}

export class LirlLawGate {
  readonly engine: InvariantEngine;
  readonly journal: FaultJournal;
  readonly runs: RunStore;

  constructor() {
    this.journal = new FaultJournal();
    this.engine = new InvariantEngine(this.journal);
    this.runs = new RunStore();
    for (const invariant of createLirlInvariants()) {
      this.engine.register(invariant);
    }
  }

  async evaluate(intent: LirlIntent): Promise<LirlGateResult> {
    const run = this.runs.startRun({
      metadata: { subsystem: 'lirl', intentAction: intent.action },
    });
    const span = this.runs.startSpan(run.runId, { name: 'lirl.law_gate' });

    const invariantResults = await this.engine.evaluateAll({
      runId: run.runId,
      spanId: span.spanId,
      input: intent,
      output: { stage: 'law_gate' },
      actor: intent.actorId || 'unknown',
      action: intent.action || 'unknown',
      payload: intent.payload,
    });

    this.runs.endSpan(span.spanId);
    this.runs.endRun(run.runId);

    const failures = invariantResults.filter((result) => !result.passed);
    const reasons = failures.map(
      (result) => result.message ?? `invariant failed: ${result.invariantId ?? 'unknown'}`,
    );

    return {
      verdict: failures.length === 0 ? 'ACCEPT' : 'REJECT',
      reasons,
      invariantResults: invariantResults.map((result) => ({
        invariantId: result.invariantId,
        passed: result.passed,
        message: result.message,
      })),
      runId: run.runId,
      spanId: span.spanId,
    };
  }
}
