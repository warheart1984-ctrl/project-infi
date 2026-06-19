import type { RunId } from '@aaes-os/runledger';

export interface UCRRunInput {
  label?: string;
  metadata?: Record<string, unknown>;
  payload?: Record<string, unknown>;
}

export interface UCRRunResult {
  runId: RunId;
  status: 'completed' | 'failed' | 'cancelled';
  traceEventCount: number;
}

export interface UCRRuntime {
  run(input: UCRRunInput): Promise<UCRRunResult>;
}
