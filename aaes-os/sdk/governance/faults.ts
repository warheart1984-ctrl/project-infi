import type { FaultWire } from '../client/types.js';
import { RuntimeClient } from '../client/RuntimeClient.js';

export async function getGovernanceFault(
  client: RuntimeClient,
  runId: string,
): Promise<FaultWire> {
  return (await client.getFault(runId)) as FaultWire;
}

export function formatFaultForLedger(fault: FaultWire): string {
  return `[${fault.invariantId}] ${fault.message} (run ${fault.runId})`;
}
