import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { LirlRuntime } from '@aaes-os/lirl';

let runtime: LirlRuntime | undefined;

function resolveRuntimeRoot(): string {
  return (
    process.env.LIRL_RUNTIME_ROOT?.trim() ||
    path.resolve(process.cwd(), '.runtime', 'lirl')
  );
}

/** Shared LIRL runtime for platform-api (file-backed memory + operator HTML). */
export function getLirlRuntime(): LirlRuntime {
  if (!runtime) {
    runtime = new LirlRuntime({ runtimeRoot: resolveRuntimeRoot() });
  }
  return runtime;
}

/** Test hook — isolate LIRL state per test file or case. */
export function resetLirlRuntimeForTests(runtimeRoot?: string): LirlRuntime {
  const root =
    runtimeRoot ??
    mkdtempSync(path.join(tmpdir(), 'platform-api-lirl-'));
  runtime = new LirlRuntime({ runtimeRoot: root });
  return runtime;
}
