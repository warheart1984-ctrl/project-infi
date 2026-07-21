import { createHmac } from 'node:crypto';

export interface CodexReplyPacket {
  status: 'done' | 'blocked' | 'partial';
  summary: string;
  changed_files: string[];
  verification: string[];
  next_action: string;
  blockers?: string[];
}

export interface SignedCodexReplyPacket {
  signer: string;
  signed_at: string;
  signature: string;
  reply: CodexReplyPacket;
}

function canonicalizeReply(reply: CodexReplyPacket, signer: string, signedAt: string): string {
  return JSON.stringify({
    signer,
    signed_at: signedAt,
    reply: {
      status: reply.status,
      summary: reply.summary,
      changed_files: [...reply.changed_files],
      verification: [...reply.verification],
      next_action: reply.next_action,
      blockers: reply.blockers ? [...reply.blockers] : undefined,
    },
  });
}

export function signCodexReplyPacket(
  reply: CodexReplyPacket,
  secret: string,
  signer = 'platform-api',
  signedAt = new Date().toISOString(),
): SignedCodexReplyPacket {
  const payload = canonicalizeReply(reply, signer, signedAt);
  const signature = createHmac('sha256', secret).update(payload).digest('hex');
  return {
    signer,
    signed_at: signedAt,
    signature,
    reply,
  };
}

export function verifySignedCodexReplyPacket(
  signed: SignedCodexReplyPacket,
  secret: string,
): boolean {
  const expected = signCodexReplyPacket(signed.reply, secret, signed.signer, signed.signed_at).signature;
  return expected === signed.signature;
}

