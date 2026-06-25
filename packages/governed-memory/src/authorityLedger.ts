import { createHash, randomUUID } from 'node:crypto';

import type { AuthorityToken } from './types.js';

export class AuthorityLedger {
  private readonly tokens = new Map<string, AuthorityToken>();

  issue(
    input: Omit<AuthorityToken, 'token_id' | 'revoked' | 'signature'> & {
      token_id?: string;
      signature?: string;
    },
  ): AuthorityToken {
    if (input.scope.intent_version < 1) {
      throw new Error('authority scope must bind to intent_version >= 1');
    }
    const token_id = input.token_id ?? randomUUID();
    const payload = JSON.stringify({
      token_id,
      issued_by: input.issued_by,
      issued_to: input.issued_to,
      capabilities: input.capabilities,
      scope: input.scope,
      delegation_chain: input.delegation_chain,
    });
    const signature =
      input.signature ?? createHash('sha256').update(`auth:${payload}`).digest('hex');
    const token: AuthorityToken = {
      token_id,
      issued_by: input.issued_by,
      issued_to: input.issued_to,
      capabilities: [...input.capabilities],
      scope: { ...input.scope, resources: [...input.scope.resources] },
      delegation_chain: [...input.delegation_chain],
      signature,
      revoked: false,
    };
    this.tokens.set(token_id, token);
    return token;
  }

  get(token_id: string): AuthorityToken | null {
    return this.tokens.get(token_id) ?? null;
  }

  revoke(token_id: string): boolean {
    const token = this.tokens.get(token_id);
    if (!token || token.revoked) return false;
    this.tokens.set(token_id, { ...token, revoked: true });
    return true;
  }

  validate(token_id: string, capability: string, now = Date.now()): { ok: boolean; reason?: string } {
    const token = this.get(token_id);
    if (!token) return { ok: false, reason: 'missing_token' };
    if (token.revoked) return { ok: false, reason: 'revoked' };
    if (!token.capabilities.includes(capability)) {
      return { ok: false, reason: 'capability_denied' };
    }
    const issuedAt = token.scope.time_limit_ms;
    if (issuedAt > 0 && now > issuedAt) {
      return { ok: false, reason: 'expired' };
    }
    return { ok: true };
  }
}
