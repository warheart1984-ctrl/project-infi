import { appendFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

import type { RunContext, Span } from '../types.js';

export interface TraceSink {
  onSpan(ctx: RunContext, type: string, span?: Span): void;
}

export class ConsoleTraceSink implements TraceSink {
  onSpan(_ctx: RunContext, _type: string, _span?: Span): void {
    // No-op default; wire to logging in ops environments.
  }
}

export class FileTraceSink implements TraceSink {
  constructor(private readonly path: string) {
    mkdirSync(dirname(path), { recursive: true });
  }

  onSpan(ctx: RunContext, type: string, span?: Span): void {
    appendFileSync(
      this.path,
      `${JSON.stringify({
        runId: ctx.id,
        type,
        span,
        timestamp: new Date().toISOString(),
      })}\n`,
      'utf8',
    );
  }
}
