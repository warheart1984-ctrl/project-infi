import { createHmac } from 'node:crypto';
import { appendFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';

export type CodexReplyPacket = {
  status: 'done' | 'blocked' | 'partial';
  summary: string;
  changed_files: string[];
  verification: string[];
  next_action: string;
  blockers?: string[];
};

export type SignedCodexReplyPacket = {
  signer: string;
  signed_at: string;
  signature: string;
  reply: CodexReplyPacket;
};

export interface CodexHandoffLedgerEntry {
  kind: 'codex-handoff-reply';
  recorded_at: string;
  source_file: string;
  packet: CodexReplyPacket;
  signature?: string;
  signer?: string;
  signature_verified?: boolean;
  task: {
    objective: string;
    next_action: string;
    status: CodexReplyPacket['status'];
    changed_files: string[];
  };
}

function getLedgerPath(): string | null {
  const raw = process.env.CODEX_HANDOFF_LEDGER_PATH;
  if (!raw || raw.trim().length === 0) {
    return null;
  }
  return path.resolve(raw);
}

export function appendCodexHandoffLedgerEntry(entry: CodexHandoffLedgerEntry): string | null {
  const ledgerPath = getLedgerPath();
  if (!ledgerPath) {
    return null;
  }

  mkdirSync(path.dirname(ledgerPath), { recursive: true });
  appendFileSync(ledgerPath, `${JSON.stringify(entry)}\n`, 'utf8');
  return ledgerPath;
}

function canonicalizeSignedReplyPacket(signedReply: SignedCodexReplyPacket): string {
  return JSON.stringify({
    signer: signedReply.signer,
    signed_at: signedReply.signed_at,
    reply: {
      status: signedReply.reply.status,
      summary: signedReply.reply.summary,
      changed_files: [...signedReply.reply.changed_files],
      verification: [...signedReply.reply.verification],
      next_action: signedReply.reply.next_action,
      blockers: signedReply.reply.blockers ? [...signedReply.reply.blockers] : undefined,
    },
  });
}

export function verifySignedCodexReplyPacket(signedReply: SignedCodexReplyPacket, secret: string): boolean {
  const expected = createHmac('sha256', secret).update(canonicalizeSignedReplyPacket(signedReply)).digest('hex');
  return expected === signedReply.signature;
}

export function buildCodexHandoffLedgerEntry(input: {
  sourceFile: string;
  objective: string;
  packet: CodexReplyPacket;
  signature?: string;
  signer?: string;
  signatureVerified?: boolean;
}): CodexHandoffLedgerEntry {
  return {
    kind: 'codex-handoff-reply',
    recorded_at: new Date().toISOString(),
    source_file: path.resolve(input.sourceFile),
    packet: input.packet,
    signature: input.signature,
    signer: input.signer,
    signature_verified: input.signatureVerified,
    task: {
      objective: input.objective,
      next_action: input.packet.next_action,
      status: input.packet.status,
      changed_files: input.packet.changed_files,
    },
  };
}
