import { createHmac } from 'node:crypto';

import { describe, expect, it } from 'vitest';

import {
  buildCodexHandoffLedgerEntry,
  verifySignedCodexReplyPacket,
  type CodexReplyPacket,
} from './codexHandoff';

describe('codex handoff signature verification', () => {
  it('verifies signed reply packets and records signature metadata', () => {
    const reply: CodexReplyPacket = {
      status: 'done',
      summary: 'customer evaluation completed',
      changed_files: ['services/platform-web/app/api/customer/pricing/evaluate/route.ts'],
      verification: ['signed reply verified'],
      next_action: 'ingest the reply into the ledger',
      blockers: [],
    };

    const secret = 'signed-handoff-test-secret';
    const signedReply = {
      signer: 'platform-api',
      signed_at: '2026-07-11T03:00:00.000Z',
      signature: '',
      reply,
    };
    const signature = verifySignedCodexReplyPacket(
      {
        ...signedReply,
        signature: 'placeholder',
      },
      secret,
    );
    expect(signature).toBe(false);

    const payload = JSON.stringify({
      signer: signedReply.signer,
      signed_at: signedReply.signed_at,
      reply: signedReply.reply,
    });
    const actualSignature = createHmac('sha256', secret).update(payload).digest('hex');

    expect(
      verifySignedCodexReplyPacket(
        {
          ...signedReply,
          signature: actualSignature,
        },
        secret,
      ),
    ).toBe(true);

    const ledgerEntry = buildCodexHandoffLedgerEntry({
      sourceFile: 'services/platform-web/app/api/customer/pricing/evaluate/route.ts',
      objective: 'customer-authenticated pricing evaluation',
      packet: reply,
      signature: actualSignature,
      signer: signedReply.signer,
      signatureVerified: true,
    });

    expect(ledgerEntry.signature).toBe(actualSignature);
    expect(ledgerEntry.signer).toBe('platform-api');
    expect(ledgerEntry.signature_verified).toBe(true);
    expect(ledgerEntry.task.objective).toContain('customer-authenticated');
  });
});
