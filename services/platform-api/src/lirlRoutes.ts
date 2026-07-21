import path from 'node:path';

import type { Express, Request, Response } from 'express';

import type { LirlIntent } from '@aaes-os/lirl';

import { getLirlRuntime } from './lirlState.js';
import { asyncHandler, authRequired } from './httpUtils.js';

function intentFromBody(req: Request): LirlIntent {
  const actorId =
    typeof req.body.actorId === 'string' && req.body.actorId.trim().length > 0
      ? req.body.actorId.trim()
      : req.platformCtx!.ownerId;

  return {
    intentId: typeof req.body.intentId === 'string' ? req.body.intentId : undefined,
    actorId,
    action: String(req.body.action ?? ''),
    payload: (req.body.payload as LirlIntent['payload']) ?? undefined,
    forceBypass: req.body.forceBypass === true,
    metadata: (req.body.metadata as Record<string, unknown>) ?? undefined,
  };
}

export function mountLirlRoutes(app: Express): void {
  app.post(
    '/v1/lirl/intents',
    authRequired,
    asyncHandler(async (req, res) => {
      const intent = intentFromBody(req);
      if (!intent.action) {
        res.status(400).json({ error: 'LIRL: action is required' });
        return;
      }

      const result = await getLirlRuntime().processIntent(intent);
      const status = result.verdict === 'ACCEPT' ? 201 : 422;

      res.status(status).json({
        intentId: result.intentId,
        verdict: result.verdict,
        reasons: result.reasons,
        runId: result.runId,
        spanId: result.spanId,
        receiptId: result.receiptId,
        memoryWritten: result.memoryWritten,
        memoryKey: result.memoryKey,
        operator: {
          htmlPath: getLirlRuntime().operatorHtmlPath,
          snapshot: {
            verdict: result.operatorView.verdict,
            receiptId: result.operatorView.receiptId,
            intentId: result.operatorView.intentId,
            actorId: result.operatorView.actorId,
            action: result.operatorView.action,
            memoryWritten: result.operatorView.memoryWritten,
            reasons: result.operatorView.reasons,
            issuedAt: result.operatorView.issuedAt,
          },
        },
      });
    }),
  );

  app.get(
    '/v1/lirl/memory/:key',
    authRequired,
    (req, res: Response) => {
      const key = String(req.params.key ?? '').trim();
      if (!key) {
        res.status(400).json({ error: 'LIRL: key is required' });
        return;
      }
      const record = getLirlRuntime().memory.getByKey(key);
      if (!record) {
        res.status(404).json({ error: 'LIRL: memory key not found' });
        return;
      }
      res.json({ record });
    },
  );

  app.get(
    '/v1/lirl/operator',
    authRequired,
    (_req, res: Response) => {
      const runtime = getLirlRuntime();
      res.type('html').sendFile(path.resolve(runtime.operatorHtmlPath));
    },
  );
}
