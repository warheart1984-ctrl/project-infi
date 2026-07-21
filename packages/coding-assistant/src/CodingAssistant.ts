import { AAISRuntime, type AAISExecutionReport } from '@aaes-os/aais';
import type { CodingRouter, Identity } from '@aaes-os/governed-runtime';
import { InfinityCodingAgent, type InfinityAgentOptions } from '@aaes-os/infinity-agents';
import { NovaCodingShell, type NovaShellOptions } from '@aaes-os/nova-shell';
import { GovernedSandbox, type GovernedSandboxOptions } from '@aaes-os/sandbox';
import type { SovereignXRouter } from '@aaes-os/sovereignx-router';

interface AAISRuntimeSurface {
  describeFlow(): readonly ('llm' | 'jarvis' | 'nova')[];
  describeCapabilities?(): readonly { name: string }[];
  executeAAISCheck(payload: unknown): AAISExecutionReport;
}

export class CodingAssistant {
  constructor(
    private readonly router: CodingRouter,
    private readonly aaisRuntime: AAISRuntimeSurface = new AAISRuntime() as AAISRuntimeSurface,
    private readonly sovereignXRouter?: SovereignXRouter,
  ) {}

  private runAAIS(surface: 'nova' | 'infinity' | 'sandbox', payload: unknown): AAISExecutionReport {
    const capabilities = this.aaisRuntime.describeCapabilities?.().map(({ name }) => name) ?? [];
    return this.aaisRuntime.executeAAISCheck({
      surface,
      flow: this.aaisRuntime.describeFlow(),
      capabilities,
      payload,
    });
  }

  nova(identity: Identity, options?: NovaShellOptions): NovaCodingShell {
    this.runAAIS('nova', { identity, options });
    return new NovaCodingShell(this.router, identity, options);
  }

  infinity(identity: Identity, options?: InfinityAgentOptions): InfinityCodingAgent {
    this.runAAIS('infinity', { identity, options });
    return new InfinityCodingAgent(this.router, identity, options);
  }

  sandbox(options?: GovernedSandboxOptions): GovernedSandbox {
    this.runAAIS('sandbox', { options });
    return new GovernedSandbox(options);
  }

  setModelPreference(model: 'auto' | 'qwen-3b' | 'qwen-7b'): void {
    if (!this.sovereignXRouter) {
      return;
    }

    this.sovereignXRouter.setOverride(model === 'auto' ? null : model);
  }

  getRouter(): CodingRouter {
    return this.router;
  }

  getAAISRuntime(): AAISRuntimeSurface {
    return this.aaisRuntime;
  }

  getSovereignXRouter(): SovereignXRouter | undefined {
    return this.sovereignXRouter;
  }
}
