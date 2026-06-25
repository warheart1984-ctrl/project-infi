import type { RunContext } from '../types.js';

export interface TraceSink {
  onSpan(ctx: RunContext, type: string): void;
}

export class ConsoleTraceSink implements TraceSink {
  onSpan(_ctx: RunContext, _type: string): void {
    // No-op default; wire to logging in ops environments.
  }
}
