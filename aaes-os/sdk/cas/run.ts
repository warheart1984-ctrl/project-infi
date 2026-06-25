import type { Identity } from '../client/types.js';
import { RuntimeClient } from '../client/RuntimeClient.js';

export async function executeRun(
  client: RuntimeClient,
  identity: Identity,
  payload: Record<string, unknown>,
) {
  return client.execute({ identity, payload });
}

export async function replayRun(
  client: RuntimeClient,
  runId: string,
  identity: Identity,
  payload: Record<string, unknown>,
) {
  const receipt = await client.getReceipt(runId);
  const echo =
    receipt.result &&
    typeof receipt.result === 'object' &&
    receipt.result !== null &&
    'echo' in receipt.result
      ? (receipt.result as { echo: Record<string, unknown> }).echo
      : payload;
  return client.execute({ identity, payload: echo });
}
