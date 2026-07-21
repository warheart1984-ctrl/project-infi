import type { PatternLedger } from '@aaes-os/aaes-governance';
import type { KernoScheduler } from '@aaes-os/kerno';
import type { SovrenAuthority } from '@aaes-os/sovren';
import { AuthorityLevel } from '@aaes-os/sovren';
import type {
  CodingBackend,
  CompiledPolicy,
  GovernedChatRequest,
  GovernedChatResponse,
  GovernanceContext,
} from '../types.js';

export class CodingRouter {
  constructor(
    private readonly backends: CodingBackend[],
    private readonly policies: CompiledPolicy[],
    private readonly ledger: PatternLedger,
    private readonly sovren?: SovrenAuthority,
    private readonly kerno?: KernoScheduler,
  ) {
    if (this.kerno) {
      this.kerno.on('IMMUNE_RUNTIME_ALERT', (alert: Record<string, unknown>) => {
        this.ledger.append({
          envelope_id: 'KERNO_ALERT',
          trace_id: 'immune_runtime',
          delta_hash: '',
          action: 'IMMUNE_RUNTIME_ALERT',
          actor_id: 'KERNO',
          verdict_class: 'OPERATIONAL',
          meta: alert,
        });
      });
    }
  }

  async execute(req: GovernedChatRequest): Promise<GovernedChatResponse> {
    if (this.sovren) {
      if (!req.authToken) {
        throw new Error('SOVREN: no auth token — AAIS-2 HALT');
      }
      this.sovren.authorize(req.authToken, AuthorityLevel.OPERATOR);
    }

    const matched = this.policies.filter((p) => p.matches(req.governance));
    const backend = this.resolveBackend(matched);

    if (!backend) {
      throw new Error('No coding backend available for the matched policies');
    }

    this.enforceGuardrails(req, matched);

    const intentClass = req.intent.kind;
    let slotId: string | undefined;
    if (this.kerno) {
      slotId = this.kerno.reserve(req.identity.actorId, intentClass);
    }

    const start = Date.now();
    try {
      const response = await backend.chat(req);
      response.output.latencyMs = Date.now() - start;
      response.governance.policyIds = matched.map((p) => p.id);
      return response;
    } finally {
      if (this.kerno && slotId) {
        this.kerno.release(slotId);
      }
    }
  }

  getBackends(): readonly CodingBackend[] {
    return this.backends;
  }

  getPolicies(): readonly CompiledPolicy[] {
    return this.policies;
  }

  getLedger(): PatternLedger {
    return this.ledger;
  }

  private resolveBackend(matched: CompiledPolicy[]): CodingBackend | undefined {
    const allowed = new Set<string>();
    const preferred = new Set<string>();

    for (const policy of matched) {
      policy.routing.allowedBackends?.forEach((b) => allowed.add(b));
      policy.routing.preferredBackends?.forEach((b) => preferred.add(b));
    }

    const candidates = this.backends.filter((b) =>
      allowed.size === 0 ? true : allowed.has(b.name),
    );

    return candidates.find((b) => preferred.has(b.name)) ?? candidates[0];
  }

  private enforceGuardrails(req: GovernedChatRequest, matched: CompiledPolicy[]): void {
    for (const policy of matched) {
      const roles = policy.guardrails.requireIdentityRole;
      if (roles && roles.length > 0 && !roles.includes(req.identity.role)) {
        throw new Error(
          `Policy ${policy.id} requires identity role in [${roles.join(', ')}], got "${req.identity.role}"`,
        );
      }
    }
  }
}

export function governanceMatches(
  when: { domain?: string; risk?: string; tags?: string[] },
  governance: GovernanceContext,
): boolean {
  if (when.domain !== undefined && when.domain !== governance.domain) {
    return false;
  }
  if (when.risk !== undefined && when.risk !== governance.risk) {
    return false;
  }
  if (when.tags !== undefined && when.tags.length > 0) {
    const reqTags = governance.tags ?? [];
    if (!when.tags.every((tag) => reqTags.includes(tag))) {
      return false;
    }
  }
  return true;
}
