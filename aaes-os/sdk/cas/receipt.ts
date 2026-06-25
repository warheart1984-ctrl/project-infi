import { RuntimeClient } from '../client/RuntimeClient.js';
import { hashReceipt } from '../util/hash.js';

export async function getReceipt(client: RuntimeClient, runId: string) {
  return client.getReceipt(runId);
}

export async function getReceiptHash(client: RuntimeClient, runId: string) {
  const receipt = await client.getReceipt(runId);
  return hashReceipt(receipt);
}

export function compareReceiptHashes(hashA: string, hashB: string): boolean {
  return hashA === hashB;
}

export async function exportReceipt(
  client: RuntimeClient,
  runId: string,
): Promise<string> {
  const receipt = await client.getReceipt(runId);
  return JSON.stringify(receipt, null, 2);
}
