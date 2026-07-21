import { createHmac, randomBytes } from 'node:crypto';

import { AuthorityLevel } from './AuthorityLevel.js';

export interface AuthToken {
  token_id: string;
  actor_id: string;
  level: AuthorityLevel;
  issued_at: string;
  expires_at: string | null;
  signature: string;
}

export class SovrenAuthority {
  private readonly lawKey: string;

  constructor(lawKey?: string) {
    this.lawKey = lawKey ?? process.env.SOVREN_LAW_KEY ?? randomBytes(32).toString('hex');
  }

  issue(actorId: string, level: AuthorityLevel, ttlSeconds?: number): AuthToken {
    const token_id = `sovren_${randomBytes(8).toString('hex')}`;
    const issued_at = new Date().toISOString();
    const expires_at = ttlSeconds
      ? new Date(Date.now() + ttlSeconds * 1000).toISOString()
      : null;

    const payload = JSON.stringify({ token_id, actor_id: actorId, level, issued_at, expires_at });
    const signature = createHmac('sha256', this.lawKey).update(payload).digest('hex');

    return { token_id, actor_id: actorId, level, issued_at, expires_at, signature };
  }

  verify(token: AuthToken): boolean {
    const { signature, ...rest } = token;
    const payload = JSON.stringify(rest);
    const expected = createHmac('sha256', this.lawKey).update(payload).digest('hex');
    if (expected !== signature) {
      return false;
    }
    if (token.expires_at && new Date(token.expires_at) < new Date()) {
      return false;
    }
    return true;
  }

  authorize(token: AuthToken, requiredLevel: AuthorityLevel): void {
    if (!this.verify(token)) {
      throw new Error(`SOVREN: invalid or expired token for actor ${token.actor_id}`);
    }
    if (token.level < requiredLevel) {
      throw new Error(
        `SOVREN: actor ${token.actor_id} has level ${token.level} but operation requires level ${requiredLevel} — AAIS-2 HALT`,
      );
    }
  }

  signEnvelope(envelope: Record<string, unknown>): string {
    const sorted = JSON.stringify(
      Object.keys(envelope)
        .sort()
        .reduce<Record<string, unknown>>((acc, key) => {
          acc[key] = envelope[key];
          return acc;
        }, {}),
    );
    return createHmac('sha256', this.lawKey).update(sorted).digest('hex');
  }
}
