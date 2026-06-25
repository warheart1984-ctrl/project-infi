import { createHash, randomUUID } from 'node:crypto';

import type { IntentRecord } from './types.js';

function hashIntent(record: Omit<IntentRecord, 'content_hash' | 'prev_hash'> & { prev_hash: string | null }): string {
  const payload = JSON.stringify({
    intent_id: record.intent_id,
    timestamp: record.timestamp,
    operator_id: record.operator_id,
    semantic_goal: record.semantic_goal,
    constraints: record.constraints,
    success_criteria: record.success_criteria,
    horizon: record.horizon,
    version: record.version,
    signature: record.signature,
    prev_hash: record.prev_hash,
  });
  return createHash('sha256').update(payload).digest('hex');
}

export class IntentLedger {
  private readonly chain: IntentRecord[] = [];

  append(
    input: Omit<IntentRecord, 'intent_id' | 'version' | 'content_hash' | 'prev_hash' | 'timestamp'> & {
      intent_id?: string;
      timestamp?: number;
    },
  ): IntentRecord {
    const prev = this.chain.at(-1) ?? null;
    const version = prev ? prev.version + 1 : 1;
    const draft = {
      intent_id: input.intent_id ?? randomUUID(),
      timestamp: input.timestamp ?? Date.now(),
      operator_id: input.operator_id,
      semantic_goal: input.semantic_goal,
      constraints: [...input.constraints],
      success_criteria: [...input.success_criteria],
      horizon: input.horizon,
      version,
      signature: input.signature,
      prev_hash: prev?.content_hash ?? null,
    };
    const content_hash = hashIntent(draft);
    const record: IntentRecord = { ...draft, content_hash };
    this.chain.push(record);
    return record;
  }

  latest(): IntentRecord | null {
    return this.chain.at(-1) ?? null;
  }

  getVersion(version: number): IntentRecord | null {
    return this.chain.find((r) => r.version === version) ?? null;
  }

  verifyChain(): boolean {
    for (let i = 0; i < this.chain.length; i += 1) {
      const rec = this.chain[i]!;
      const expectedPrev = i === 0 ? null : this.chain[i - 1]!.content_hash;
      if (rec.prev_hash !== expectedPrev) return false;
      const { content_hash: _h, ...rest } = rec;
      const recomputed = hashIntent({ ...rest, prev_hash: rec.prev_hash });
      if (recomputed !== rec.content_hash) return false;
    }
    return true;
  }

  list(): readonly IntentRecord[] {
    return this.chain;
  }
}
