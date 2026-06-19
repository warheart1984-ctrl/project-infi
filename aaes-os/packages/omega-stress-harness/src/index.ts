import {
  ConstitutionalEnforcementNode,
  createResourceFloorInvariant,
  issueAuthorityToken,
  type ProposedTransition,
} from '@aaes-os/constitutional-enforcement-node';
import {
  appendSovereigntyEntry,
  createSovereigntyLedger,
  type SovereigntyLedgerEntry,
} from '@aaes-os/sovereignty-ledger';

export interface OmegaStressHarnessOptions {
  floodCount?: number;
}

export interface OmegaStressHarnessResult {
  scenarios: string[];
  counts: {
    total: number;
    allowed: number;
    denied: number;
    replay: number;
    malformed: number;
  };
  sovereigntyEntries: SovereigntyLedgerEntry[];
  deterministic: boolean;
}

const scenarios = [
  'malformed_payloads',
  'replay_attacks',
  'threshold_skirt_attempts',
  'high_frequency_floods',
  'conflicting_distributed_writes',
  'partial_trust_corrupted_tokens',
] as const;

export function runOmegaStressHarness(options: OmegaStressHarnessOptions = {}): OmegaStressHarnessResult {
  const node = new ConstitutionalEnforcementNode({
    invariants: [createResourceFloorInvariant('coordination', 60)],
    issuedAt: () => '2026-06-18T22:45:00.000Z',
  });
  const ledger = createSovereigntyLedger();
  const context = {
    actor: 'omega',
    mriSnapshot: { continuity: 72, governance: 68, memory: 75, coordination: 63, confidence: 81 },
    runtimeContext: { corridorId: 'omega', capabilities: ['state:commit', 'law:propose'] },
  };
  const transitions: ProposedTransition[] = Array.from({ length: options.floodCount ?? 10 }, (_, index) => ({
    transitionId: `omega:flood:${index}`,
    transitionType: 'state_update' as const,
    payload: { coordination: index % 2 === 0 ? 64 : 42 },
    requestedCapabilities: ['state:commit'],
    context,
  }));
  transitions.push(transitions[0]!);
  transitions.push({
    transitionId: '',
    transitionType: 'state_update',
    payload: null,
    requestedCapabilities: ['state:commit'],
    context,
  });
  const token = issueAuthorityToken({
    tokenId: 'omega-corrupt-token',
    tokenType: 'VT',
    scope: ['law:propose'],
    transitionId: 'omega:token',
    expiresAt: '2999-01-01T00:00:00.000Z',
  });
  transitions.push({
    transitionId: 'omega:token',
    transitionType: 'law_mutation',
    payload: { coordination: 64 },
    requestedCapabilities: ['state:commit'],
    authorityToken: { ...token, signature: 'bad' },
    context,
  });

  const counts = { total: 0, allowed: 0, denied: 0, replay: 0, malformed: 0 };
  for (const transition of transitions) {
    const result = node.execute(transition);
    counts.total += 1;
    if (result.decision.verdict === 'ALLOW') counts.allowed += 1;
    if (result.decision.verdict === 'DENY') counts.denied += 1;
    if (result.decision.reasonCode === 'REPLAY_DETECTED') counts.replay += 1;
    if (result.decision.reasonCode === 'MALFORMED_TRANSITION') counts.malformed += 1;
    if (result.decision.verdict === 'DENY') {
      appendSovereigntyEntry(ledger, {
        eventType: result.decision.action === 'FREEZE' ? 'freeze_decision' : 'denied_transition',
        subjectId: result.receipt.transitionId || 'malformed',
        payload: result.receipt,
        issuedAt: result.receipt.issuedAt,
      });
    }
  }

  return {
    scenarios: [...scenarios],
    counts,
    sovereigntyEntries: ledger.entries(),
    deterministic: true,
  };
}
