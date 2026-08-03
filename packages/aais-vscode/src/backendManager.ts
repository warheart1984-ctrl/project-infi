import { createFreeCodingStack, FreeCodingStackOptions } from '@aaes-os/coding-assistant';
import { AAISConfig } from './config';

export class AAISBackendManager {
  private stack: Awaited<ReturnType<typeof createFreeCodingStack>> | null = null;
  private config: AAISConfig;

  constructor(config: AAISConfig) {
    this.config = config;
  }

  async initialize(): Promise<void> {
    const options: FreeCodingStackOptions = {
      ollamaUrl: this.config.ollamaUrl,
      openRouterApiKey: this.config.getOpenRouterApiKey(),
      groqApiKey: this.config.getGroqApiKey(),
      includeCloudFree: true,
      warmModels: true,
    };
    this.stack = await createFreeCodingStack(options);
  }

  updateConfig(config: AAISConfig): void {
    this.config = config;
    // Re-initialize on next request if needed
    this.stack = null;
  }

  async getStack() {
    if (!this.stack) {
      await this.initialize();
    }
    return this.stack!;
  }

  getAvailableBackends(): string[] {
    return this.stack?.discovery.available.map(a => a.name) ?? [];
  }

  getSkippedBackends(): Array<{ name: string; reason: string }> {
    return this.stack?.discovery.skipped ?? [];
  }

  dispose(): void {
    this.stack = null;
  }
}