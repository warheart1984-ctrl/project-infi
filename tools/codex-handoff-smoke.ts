#!/usr/bin/env node
import { appendFileSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { SovereignXRouter } from '@aaes-os/sovereignx-router';
import {
  assertReplyPacket,
  assertRequestPacket,
  buildReplyPacket,
  buildRequestPacket,
  type ReplyPacket,
  type RequestPacket,
  validateRequestPacket,
  validateReplyPacket,
} from './codex-handoff-core.js';
import { createCodexHandoffRouter, routeCodexHandoff } from './codex-handoff-router.js';

interface LedgerEntry {
  kind: 'codex-handoff-reply';
  recorded_at: string;
  source_file: string;
  packet: ReplyPacket;
  task: {
    objective: string;
    next_action: string;
    status: ReplyPacket['status'];
    changed_files: string[];
  };
}

function main(): void {
  const tempDir = mkdtempSync(path.join(os.tmpdir(), 'codex-handoff-smoke-'));
  const requestPath = path.join(tempDir, 'codex-handoff-request.json');
  const replyPath = path.join(tempDir, 'codex-handoff-reply.json');
  const ledgerPath = path.join(tempDir, 'codex-task-ledger.jsonl');

  const prompt = 'reduce the model overhead for task handoff';
  const requestOptions = new Map<string, string[]>([
    ['current-state', ['schema and packet CLI are already in place']],
    ['done', ['request schema exists', 'reply schema exists']],
    ['next-action', ['validate the reply and ingest it into the ledger']],
    ['files', ['docs/crk1/release/CODEX_WORKFLOW.md']],
    ['verification', ['corepack pnpm codex-handoff validate <packet>']],
  ]);

  const requestPacket = buildRequestPacket(prompt, requestOptions);
  writeFileSync(requestPath, `${JSON.stringify(requestPacket, null, 2)}\n`, 'utf8');

  const requestValidation = validateRequestPacket(JSON.parse(readFileSync(requestPath, 'utf8')) as unknown);
  if (!requestValidation.valid) {
    throw new Error(`request validation failed: ${requestValidation.issues.map((issue) => `${issue.path}:${issue.message}`).join('; ')}`);
  }

  const replyOptions = new Map<string, string[]>([
    ['status', ['done']],
    ['summary', ['Prompt packet was created and the reply path was accepted.']],
    ['changed-file', ['tools/codex-handoff-smoke.ts']],
    ['changed-file', ['tools/codex-handoff-core.ts']],
    ['verification', ['corepack pnpm codex-handoff validate <packet>']],
    ['next-action', ['wire the orchestrator into the upstream task source']],
  ]);

  const replyPacket = buildReplyPacket(replyOptions);
  writeFileSync(replyPath, `${JSON.stringify(replyPacket, null, 2)}\n`, 'utf8');

  const replyValidation = validateReplyPacket(JSON.parse(readFileSync(replyPath, 'utf8')) as unknown);
  if (!replyValidation.valid) {
    throw new Error(`reply validation failed: ${replyValidation.issues.map((issue) => `${issue.path}:${issue.message}`).join('; ')}`);
  }

  const validatedRequest = assertRequestPacket(JSON.parse(readFileSync(requestPath, 'utf8')) as unknown, requestPath);
  const validatedReply = assertReplyPacket(JSON.parse(readFileSync(replyPath, 'utf8')) as unknown, replyPath);

  const ledgerEntry: LedgerEntry = {
    kind: 'codex-handoff-reply',
    recorded_at: new Date().toISOString(),
    source_file: path.resolve(replyPath),
    packet: validatedReply,
    task: {
      objective: validatedRequest.objective,
      next_action: validatedReply.next_action,
      status: validatedReply.status,
      changed_files: validatedReply.changed_files,
    },
  };

  appendFileSync(ledgerPath, `${JSON.stringify(ledgerEntry)}\n`, 'utf8');

  const ledger = readFileSync(ledgerPath, 'utf8').trim().split(/\r?\n/).filter(Boolean);
  if (ledger.length !== 1) {
    throw new Error(`expected 1 ledger entry, found ${ledger.length}`);
  }

  const entry = JSON.parse(ledger[0] ?? '{}') as { kind?: string; task?: { objective?: string } };
  if (entry.kind !== 'codex-handoff-reply') {
    throw new Error('ledger entry missing codex-handoff-reply kind');
  }
  if (entry.task?.objective !== prompt) {
    throw new Error('ledger entry objective did not match the request objective');
  }

  const router = createCodexHandoffRouter(new SovereignXRouter({ clock: () => 1_700_000_000_000 }));
  const shortRequest = buildRequestPacket(
    'ship slice',
    new Map<string, string[]>([
      ['current-state', ['ready']],
      ['done', ['schema']],
      ['next-action', ['next']],
      ['files', ['a.ts']],
      ['verification', ['ok']],
    ]),
  );
  const shortRoute = routeCodexHandoff(router, {
    request: shortRequest,
    hasReply: false,
  });
  if (shortRoute.selectedModel !== 'qwen-3b') {
    throw new Error(`expected short request to select qwen-3b, got ${shortRoute.selectedModel}`);
  }

  const longRequest = buildRequestPacket(
    'reduce the model overhead for task handoff by routing constitutional requests through the new orchestration layer and recording the selected engine',
    new Map<string, string[]>([
      ['current-state', ['schema and packet CLI are already in place']],
      ['done', ['request schema exists', 'reply schema exists']],
      ['next-action', ['validate the reply and ingest it into the ledger']],
      ['files', ['docs/crk1/release/CODEX_WORKFLOW.md']],
      ['verification', ['corepack pnpm codex-handoff validate <packet>']],
    ]),
  );
  const longRoute = routeCodexHandoff(router, {
    request: longRequest,
    hasReply: true,
    replyPath,
  });
  if (longRoute.selectedModel !== 'qwen-7b') {
    throw new Error(`expected long request to select qwen-7b, got ${longRoute.selectedModel}`);
  }

  writeFileSync(path.join(tempDir, 'smoke.ok'), 'ok\n', 'utf8');
  console.log(`codex handoff smoke passed: ${tempDir}`);
}

main();
