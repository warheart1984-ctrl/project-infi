#!/usr/bin/env node
import { appendFileSync, readFileSync } from 'node:fs';
import path from 'node:path';
import {
  assertReplyPacket,
  assertRequestPacket,
  type ReplyPacket,
  type RequestPacket,
  verifySignedReplyPacket,
} from './codex-handoff-core.js';

interface LedgerEntry {
  kind: 'codex-handoff-reply';
  recorded_at: string;
  source_file: string;
  packet: ReplyPacket;
  signature?: string;
  signer?: string;
  signature_verified?: boolean;
  task: {
    objective: string;
    next_action: string;
    status: ReplyPacket['status'];
    changed_files: string[];
  };
}

interface SignedReplyEnvelope {
  signer: string;
  signed_at: string;
  signature: string;
  reply: ReplyPacket;
}

function usage(): string {
  return [
    'Usage:',
    '  pnpm codex-handoff-ingest <reply.json> [--ledger <file>] [--signing-secret <secret>] [--json]',
  ].join('\n');
}

function die(message: string): never {
  console.error(message);
  console.error('');
  console.error(usage());
  process.exit(1);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function isMissingFileError(error: unknown): boolean {
  return typeof error === 'object' && error !== null && 'code' in error && (error as { code?: string }).code === 'ENOENT';
}

function parseArgs(argv: string[]): { replyPath: string; ledgerPath: string; signingSecret: string | null; json: boolean } {
  if (argv.length === 0) {
    die(usage());
  }

  const replyPath = argv[0];
  if (!isNonEmptyString(replyPath)) {
    die('Missing reply file path.');
  }

  let ledgerPath = path.resolve('.runtime/codex-task-ledger.jsonl');
  let signingSecret: string | null = process.env.CODEX_HANDOFF_SIGNING_SECRET ?? null;
  let json = false;

  for (let i = 1; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === '--json') {
      json = true;
      continue;
    }

    if (token === '--ledger') {
      const next = argv[i + 1];
      if (!isNonEmptyString(next)) {
        die('Missing value for --ledger');
      }
      ledgerPath = path.resolve(next);
      i += 1;
      continue;
    }

    if (token === '--signing-secret') {
      const next = argv[i + 1];
      if (!isNonEmptyString(next)) {
        die('Missing value for --signing-secret');
      }
      signingSecret = next;
      i += 1;
      continue;
    }

    die(`Unexpected argument: ${token}`);
  }

  return { replyPath, ledgerPath, signingSecret, json };
}

function readReplyEnvelope(replyPath: string): { packet: ReplyPacket; signedReply: SignedReplyEnvelope | null } {
  const parsed = JSON.parse(readFileSync(replyPath, 'utf8')) as unknown;
  if (
    parsed &&
    typeof parsed === 'object' &&
    'reply' in parsed &&
    'signature' in parsed &&
    'signer' in parsed
  ) {
    const signedReply = parsed as SignedReplyEnvelope;
    try {
      const packet = assertReplyPacket(signedReply.reply, `${replyPath}.reply`);
      return { packet, signedReply: { ...signedReply, reply: packet } };
    } catch (error) {
      die(error instanceof Error ? error.message : `${replyPath}.reply is not a valid Codex reply packet`);
    }
  }

  try {
    return { packet: assertReplyPacket(parsed, replyPath), signedReply: null };
  } catch (error) {
    die(error instanceof Error ? error.message : `${replyPath} is not a valid Codex reply packet`);
  }
}

function readRequestPacketFromSibling(replyPath: string): RequestPacket | undefined {
  const candidate = path.join(path.dirname(replyPath), 'codex-handoff-request.json');
  try {
    const packet = JSON.parse(readFileSync(candidate, 'utf8')) as unknown;
    return assertRequestPacket(packet, candidate);
  } catch (error) {
    if (isMissingFileError(error)) {
      return undefined;
    }
    die(error instanceof Error ? error.message : `${candidate} is not a valid Codex request packet`);
    return undefined;
  }
}

function buildLedgerEntry(
  replyPath: string,
  packet: ReplyPacket,
  signedReply: SignedReplyEnvelope | null,
  signingSecret: string | null,
): LedgerEntry {
  const request = readRequestPacketFromSibling(replyPath);
  const signatureVerified = signedReply && signingSecret ? verifySignedReplyPacket(signedReply, signingSecret) : undefined;
  if (signedReply && signingSecret && !signatureVerified) {
    die('Signed reply packet failed signature verification.');
  }
  if (signedReply && !signingSecret) {
    die('Signed reply packet requires --signing-secret or CODEX_HANDOFF_SIGNING_SECRET.');
  }
  return {
    kind: 'codex-handoff-reply',
    recorded_at: new Date().toISOString(),
    source_file: path.resolve(replyPath),
    packet,
    signature: signedReply?.signature,
    signer: signedReply?.signer,
    signature_verified: signatureVerified,
    task: {
      objective: request?.objective ?? packet.summary,
      next_action: packet.next_action,
      status: packet.status,
      changed_files: packet.changed_files,
    },
  };
}

function appendLedgerEntry(ledgerPath: string, entry: LedgerEntry): void {
  appendFileSync(ledgerPath, `${JSON.stringify(entry)}\n`, 'utf8');
}

function main(): void {
  const { replyPath, ledgerPath, signingSecret, json } = parseArgs(process.argv.slice(2));
  const { packet, signedReply } = readReplyEnvelope(replyPath);
  const entry = buildLedgerEntry(replyPath, packet, signedReply, signingSecret);
  appendLedgerEntry(ledgerPath, entry);

  if (json) {
    process.stdout.write(`${JSON.stringify({ ok: true, ledger: path.resolve(ledgerPath), entry })}\n`);
    return;
  }

  console.log(`appended ${path.resolve(ledgerPath)}`);
  console.log(`status: ${packet.status}`);
  console.log(`summary: ${packet.summary}`);
}

main();
