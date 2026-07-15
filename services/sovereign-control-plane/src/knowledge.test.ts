import { describe, expect, it } from 'vitest';

import {
  diffGovernanceStates,
  getChangeLedgerEntry,
  getCrfArtifacts,
  getGovernanceHistory,
  getKnowledgeWorld,
  parseUgql,
  queryKnowledge,
  replayGovernanceState,
  validateCrfArtifact,
} from './knowledge.js';

describe('knowledge substrate', () => {
  it('parses and executes UGQL against the seeded UGR', () => {
    const query = 'TRACE concept risk FROM lineage WITH INCLUDE worlds, docs, metrics LIMIT 12';
    const parsed = parseUgql(query);
    expect(parsed.verb).toBe('TRACE');
    expect(parsed.scope).toBe('lineage');
    expect(parsed.options.limit).toBe(12);

    const result = queryKnowledge(query);
    expect(result.meta.count).toBeGreaterThan(0);
    expect(result.results.some((node) => node.nodeId === 'node-concept-risk')).toBe(true);
  });

  it('replays and diffs governance states deterministically', () => {
    const replay = replayGovernanceState('2026-07-11T19:11:00.000Z');
    expect(replay.profiles).toContain('profile:prod-critical-v3');
    expect(replay.authorityModes).toContain('COUNCIL');

    const diff = diffGovernanceStates('2026-06-01T00:00:00.000Z', '2026-07-11T19:10:00.000Z');
    expect(diff.authority_diffs[0]?.authority_mode.to).toBe('COUNCIL');
    expect(diff.arena_diffs[0]?.required_arenas.added).toContain('arena:simulation');
  });

  it('exposes a replayable ledger and CRF validation surface', () => {
    const ledgerEntry = getChangeLedgerEntry('entry-044');
    expect(ledgerEntry).not.toBeNull();
    expect(getGovernanceHistory('intent-987').governanceChain).toContain('entry-044');

    const crf = getCrfArtifacts()[0];
    expect(crf).toBeDefined();
    expect(validateCrfArtifact(crf).valid).toBe(true);

    const world = getKnowledgeWorld('world:project-infi');
    expect(world?.constitutionRef).toBe('constitution:project-infi');
  });
});
