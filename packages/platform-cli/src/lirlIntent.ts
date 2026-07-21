import { readFileSync } from 'node:fs';

import { LirlRuntime, type LirlIntent } from '@aaes-os/lirl';

export interface LirlIntentCliInput {
  actorId: string;
  action: string;
  payload?: LirlIntent['payload'];
  forceBypass?: boolean;
  intentId?: string;
  runtimeRoot?: string;
}

export function parseLirlIntentCliInput(args: Record<string, string | boolean>): LirlIntentCliInput {
  if (typeof args.file === 'string') {
    const raw = JSON.parse(readFileSync(args.file, 'utf8')) as Partial<LirlIntent>;
    return {
      actorId: String(raw.actorId ?? args.actor ?? 'operator-cli'),
      action: String(raw.action ?? args.action ?? ''),
      payload: raw.payload,
      forceBypass: raw.forceBypass === true || args.forceBypass === true,
      intentId: typeof raw.intentId === 'string' ? raw.intentId : undefined,
      runtimeRoot: typeof args['runtime-root'] === 'string' ? args['runtime-root'] : undefined,
    };
  }

  const payload: LirlIntent['payload'] = {};
  if (typeof args.key === 'string') payload.key = args.key;
  if (typeof args.value === 'string') {
    try {
      payload.value = JSON.parse(args.value);
    } catch {
      payload.value = args.value;
    }
  }

  return {
    actorId: String(args.actor ?? 'operator-cli'),
    action: String(args.action ?? ''),
    payload: Object.keys(payload).length > 0 ? payload : undefined,
    forceBypass: args.forceBypass === true,
    runtimeRoot: typeof args['runtime-root'] === 'string' ? args['runtime-root'] : undefined,
  };
}

export async function runLirlIntentCli(input: LirlIntentCliInput) {
  if (!input.action) {
    throw new Error('Usage: organism lirl intent --action <action> [--actor <id>] [--key <key>] [--value <json>] [--file <intent.json>]');
  }

  const runtime = new LirlRuntime(
    input.runtimeRoot ? { runtimeRoot: input.runtimeRoot } : undefined,
  );

  const result = await runtime.processIntent({
    actorId: input.actorId,
    action: input.action,
    payload: input.payload,
    forceBypass: input.forceBypass,
    intentId: input.intentId,
  });

  return {
    result,
    operatorHtmlPath: runtime.operatorHtmlPath,
  };
}
