import { RuntimeClient } from '../client/RuntimeClient.js';
import type { FaultWire } from '../client/types.js';

export async function getFault(
  client: RuntimeClient,
  runId: string,
): Promise<FaultWire> {
  return (await client.getFault(runId)) as FaultWire;
}

export function explainFault(fault: {
  invariantId: string;
  message: string;
}): string {
  return `Invariant ${fault.invariantId}: ${fault.message}`;
}
