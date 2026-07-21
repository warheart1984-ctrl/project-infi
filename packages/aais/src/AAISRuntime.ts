import { randomUUID } from 'node:crypto';

import { TriCoreBus, type TriCoreMessage } from '@aaes-os/tri-core-protocol';

import { listAAISCapabilities, resolveRoutingHint, type AAISPreferredModel, type AAISRoutingHint } from './capabilities.js';
import { listAAISCodingCapabilities } from './codingCapabilities.js';
import { AAISDoctrine } from './AAISDoctrine.js';
import { AAISInvariants } from './invariants/AAISInvariants.js';

export type AAISFlowStage = 'llm' | 'jarvis' | 'nova';

export interface AAISStageReport {
  stage: AAISFlowStage;
  passed: boolean;
  reason?: string;
  details?: ReadonlyArray<{
    id: string;
    passed: boolean;
    severity: 'info' | 'warn' | 'error' | 'fatal';
    message?: string;
  }>;
}

export interface AAISExecutionReport {
  flow: readonly AAISFlowStage[];
  stages: readonly AAISStageReport[];
  payload: unknown;
  validation: { passed: boolean; reason?: string };
  message: TriCoreMessage | null;
  routingHint?: AAISRoutingHint;
  provenance?: AAISProvenance;
}

export type AAISResult = AAISExecutionReport;

export interface AAISProvenance {
  capabilityName: string;
  capabilityFile: string;
  resolver: string;
  routingHint?: AAISRoutingHint;
  routerDecision?: {
    model: AAISPreferredModel;
    reason: string;
    overrideApplied: boolean;
  };
}

export interface AAISRuntimeOptions {
  bus?: TriCoreBus;
}

const AAIS_FLOW: readonly AAISFlowStage[] = ['llm', 'jarvis', 'nova'];

export class AAISRuntime {
  private readonly doctrine = new AAISDoctrine();

  constructor(private readonly options: AAISRuntimeOptions = {}) {}

  private get bus(): TriCoreBus {
    return this.options.bus ?? new TriCoreBus();
  }

  describeFlow(): readonly AAISFlowStage[] {
    return AAIS_FLOW;
  }

  describeCapabilities() {
    return listAAISCapabilities();
  }

  describeCodingCapabilities() {
    return listAAISCodingCapabilities();
  }

  executeAAISCheck(payload: unknown): AAISExecutionReport {
    const flow = this.describeFlow();
    const llmPayload = this.normalizePayload(payload);
    const routingHint = resolveRoutingHint(llmPayload);
    const provenance: AAISProvenance = {
      capabilityName: 'Capability Discovery Engine',
      capabilityFile: 'packages/aais/src/capabilities.ts',
      resolver: 'AAISRuntime.executeAAISCheck',
      routingHint,
    };
    const validation = this.doctrine.validateAction({
      actor: 'agent',
      action: 'AAIS_CHECK',
      payload: llmPayload,
      freezeActive: this.bus.isFrozen(),
    });
    const jarvisStage = this.evaluateJarvisStage(llmPayload, validation);
    const passed = jarvisStage.passed;
    const message = passed
      ? this.bus.send({
          id: randomUUID(),
          from: 'agent',
          to: 'governance',
          type: 'AAIS_CHECK',
          payload: {
            payload: llmPayload,
            flow,
            stages: [
              { stage: 'llm', passed: true },
              jarvisStage,
              { stage: 'nova', passed: true },
            ],
            validation,
            routingHint,
            provenance,
          },
          timestamp: Date.now(),
        })
      : null;

    return {
      flow,
      stages: [
        { stage: 'llm', passed: true },
        jarvisStage,
        { stage: 'nova', passed: message !== null },
      ],
      payload: llmPayload,
      validation,
      message,
      routingHint,
      provenance,
    };
  }

  sendAAISCheck(payload: unknown): TriCoreMessage | null {
    return this.executeAAISCheck(payload).message;
  }

  getAAISProvenance(payload: unknown = { surface: 'docs-site' }): AAISProvenance {
    const report = this.executeAAISCheck(payload);
    return report.provenance ?? {
      capabilityName: 'Capability Discovery Engine',
      capabilityFile: 'packages/aais/src/capabilities.ts',
      resolver: 'AAISRuntime.executeAAISCheck',
      routingHint: report.routingHint,
    };
  }

  private normalizePayload(payload: unknown): unknown {
    if (payload === null || typeof payload !== 'object') {
      return { input: payload };
    }
    return payload;
  }

  private evaluateJarvisStage(
    payload: unknown,
    validation: { passed: boolean; reason?: string },
  ): AAISStageReport {
    const context = {
      actor: 'agent',
      action: 'AAIS_CHECK',
      payload,
      freezeActive: this.bus.isFrozen(),
    };

    const details = AAISInvariants.map((invariant) => {
      const result = invariant.check(context);
      return {
        id: invariant.id,
        passed: result.passed,
        severity: result.severity,
        message: result.message,
      };
    });

    const passed = validation.passed && details.every((detail) => detail.passed);
    const reason = validation.reason ?? details.find((detail) => !detail.passed)?.message;

    return {
      stage: 'jarvis',
      passed,
      reason,
      details,
    };
  }
}

export function getAAISProvenance(payload: unknown = { surface: 'docs-site' }): AAISProvenance {
  return new AAISRuntime().getAAISProvenance(payload);
}
