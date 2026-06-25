import { createHash } from 'node:crypto';

export function hashReceipt(receipt: unknown): string {
  const h = createHash('sha256');
  h.update(JSON.stringify(receipt));
  return h.digest('hex');
}
