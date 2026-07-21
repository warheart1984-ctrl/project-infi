import type { ConsensusConfig, TwinVote } from './models.js';
export function computeConsensus(config: ConsensusConfig, votes: TwinVote[]) {
  const participants = new Set(config.participants);
  const latest = new Map<string, TwinVote>();
  for (const vote of votes) if (participants.has(vote.twinId) && vote.proposalId === config.proposalId) latest.set(vote.twinId, vote);
  if ([...latest.values()].some((vote) => vote.decision === 'AMEND')) return { reached: true, result: 'AMEND' as const };
  if (config.rule === 'UNANIMOUS') {
    if (latest.size < participants.size) return { reached: false, result: null };
    return { reached: true, result: [...latest.values()].every((vote) => vote.decision === 'ACCEPT') ? 'ACCEPT' as const : 'REJECT' as const };
  }
  const weight = (id: string) => config.rule === 'WEIGHTED_ROLES' ? (config.weights?.[id] ?? 0) : 1;
  const total = config.participants.reduce((sum, id) => sum + weight(id), 0);
  const score = (decision: TwinVote['decision']) => [...latest.values()].filter((vote) => vote.decision === decision).reduce((sum, vote) => sum + weight(vote.twinId), 0);
  if (score('ACCEPT') > total / 2) return { reached: true, result: 'ACCEPT' as const };
  if (score('REJECT') >= total / 2) return { reached: true, result: 'REJECT' as const };
  return { reached: false, result: null };
}
