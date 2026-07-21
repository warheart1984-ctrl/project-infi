import { randomUUID } from 'node:crypto';
import type { CodingRouter, GovernedChatResponse, Identity } from '@aaes-os/governed-runtime';

import {
  ConformanceGate,
  CorpusAdmitter,
  EGL1Checker,
  EvidenceBundleCollector,
  ReplayVerifier,
  type PlanStep,
  type StepResult,
} from './chain/index.js';

export interface InfinitySolveResult {
  plan: string;
  results: string[];
  steps: string[];
  responses: GovernedChatResponse[];
  stepResults: StepResult[];
}

export interface InfinityAgentOptions {
  plannerSystemPrompt?: string;
  executorSystemPrompt?: string;
}

export class InfinityCodingAgent {
  private readonly plannerSystemPrompt: string;
  private readonly executorSystemPrompt: string;
  private readonly evidenceCollector = new EvidenceBundleCollector();
  private readonly replayVerifier = new ReplayVerifier();
  private readonly egl1Checker = new EGL1Checker();
  private readonly conformanceGate = new ConformanceGate();
  private readonly corpusAdmitter = new CorpusAdmitter();

  constructor(
    private readonly router: CodingRouter,
    private readonly identity: Identity,
    options: InfinityAgentOptions = {},
  ) {
    this.plannerSystemPrompt =
      options.plannerSystemPrompt ?? 'You are Infinity, a governed coding planner.';
    this.executorSystemPrompt =
      options.executorSystemPrompt ?? 'Execute this coding step precisely and concisely.';
  }

  async solve(task: string): Promise<InfinitySolveResult> {
    const planResp = await this.router.execute(
      this.buildRequest('coding-plan', task, this.plannerSystemPrompt, `Generate a step-by-step plan to solve: ${task}`, [
        'agentic',
      ]),
    );

    const steps = planResp.output.text
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0);

    const results: string[] = [];
    const responses: GovernedChatResponse[] = [planResp];
    const stepResults: StepResult[] = [];

    for (let index = 0; index < steps.length; index++) {
      const step = steps[index]!;
      const stepResult = await this.executeStep({ command: step }, index);
      results.push(String(stepResult.output));
      stepResults.push(stepResult);
      responses.push({
        intentId: stepResult.trace_id,
        backendName: 'infinity-chain',
        trace: {
          traceId: stepResult.trace_id,
          intentId: stepResult.trace_id,
          actorId: this.identity.actorId,
          policyIds: [],
          timestamps: { createdAt: Date.now() },
        },
        output: {
          text: String(stepResult.output),
          tokensIn: 0,
          tokensOut: 0,
          latencyMs: 0,
        },
        governance: { policyIds: [], violations: [] },
      });
    }

    return {
      plan: planResp.output.text,
      steps,
      results,
      responses,
      stepResults,
    };
  }

  async executeStep(step: PlanStep, stepIndex: number): Promise<StepResult> {
    const response = await this.router.execute(
      this.buildRequest('coding-step', step.command, this.executorSystemPrompt, step.command, ['agentic']),
    );

    const stepResult: StepResult = {
      stepIndex,
      actorId: this.identity.actorId,
      action: step.command,
      output: response.output.text,
      trace_id: response.trace.traceId,
      drift: 0,
    };

    const bundle = this.evidenceCollector.collect(stepResult);
    const replayReport = this.replayVerifier.verify(bundle, stepResult);
    const egl1Report = this.egl1Checker.evaluate(stepResult, bundle);
    const conformanceReport = this.conformanceGate.check(egl1Report, replayReport);
    this.corpusAdmitter.admit(conformanceReport);

    return {
      ...stepResult,
      bundle,
      replayReport,
      egl1Report,
      conformanceReport,
    };
  }

  getCorpusAdmitter(): CorpusAdmitter {
    return this.corpusAdmitter;
  }

  getConformanceGate(): ConformanceGate {
    return this.conformanceGate;
  }

  getEgl1Checker(): EGL1Checker {
    return this.egl1Checker;
  }

  private buildRequest(
    kind: string,
    description: string,
    systemPrompt: string,
    userContent: string,
    tags: string[],
  ) {
    const intentId = randomUUID();
    const traceId = randomUUID();

    return {
      intent: { id: intentId, kind, description },
      identity: this.identity,
      governance: { domain: 'coding', risk: 'medium' as const, tags },
      trace: {
        traceId,
        intentId,
        actorId: this.identity.actorId,
        policyIds: [],
        timestamps: { createdAt: Date.now() },
      },
      input: {
        systemPrompt,
        userContent,
        context: '',
      },
    };
  }
}
