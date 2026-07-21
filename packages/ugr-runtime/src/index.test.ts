import { describe, expect, it } from 'vitest';

import { buildUgrRuntimeStatus, createUgrRuntime, parseUgrQuery } from './index.js';

describe('UGR runtime', () => {
  const runtime = createUgrRuntime({
    objects: [
      {
        id: 'object-1',
        kind: 'knowledge',
        name: 'Governance Ledger',
        domain: 'governance',
        summary: 'Canonical governance object.',
        tags: ['ledger', 'core'],
        concepts: ['authority', 'evidence'],
        stabilityScore: 0.99,
        riskProfile: 'low',
        lineage: ['root'],
        metadata: { version: 1 },
      },
    ],
    worlds: [
      {
        id: 'world-1',
        kind: 'world',
        name: 'Governance World',
        domain: 'governance',
        summary: 'World pack for governance replay.',
        tags: ['world'],
        concepts: ['replay'],
        stabilityScore: 0.94,
        riskProfile: 'medium',
        lineage: ['object-1'],
        metadata: { mode: 'seeded' },
        constitutionRef: 'constitution-1',
        rules: ['rule-1'],
        agents: ['agent-1'],
        arenas: ['arena-1'],
        state: { phase: 'boot' },
        historyRef: 'history-1',
      },
    ],
    modules: [
      {
        id: 'module-1',
        typedId: 'upl:governance/module',
        domain: 'governance',
        constitutionBinding: 'constitution-1',
        evidencePolicy: 'fresh-build',
        replayable: true,
        worlds: ['world-1'],
        lineage: ['world-1'],
        metadata: { source: 'seed' },
      },
    ],
    artifacts: [
      {
        artifactId: 'crf-1',
        version: '1.0.0',
        createdAt: '2026-07-13T00:00:00.000Z',
        timeline: ['boot', 'replay'],
        governanceState: { phase: 'seeded' },
        impactGraph: [
          { from: 'object-1', to: 'world-1', relation: 'JUSTIFIED_BY', weight: 1 },
        ],
        lineage: ['world-1'],
        evidenceBundle: ['receipt-1'],
        signatures: ['sig-1'],
      },
    ],
    changes: [
      {
        changeType: 'promote',
        artifactRef: 'crf-1',
        lineage: ['world-1'],
        councilVoteSummary: 'unanimous',
        before: { phase: 'draft' },
        after: { phase: 'verified' },
        timestamp: '2026-07-13T00:00:00.000Z',
        entryId: 'change-1',
      },
    ],
    links: [
      { from: 'world-1', to: 'object-1', relation: 'JUSTIFIED_BY', weight: 0.9 },
    ],
  });

  it('describes the runtime status and counts', () => {
    const status = buildUgrRuntimeStatus(runtime);
    const snapshot = runtime.snapshot();

    expect(status).toContain('@aaes-os/ugr-runtime');
    expect(status).toContain('worlds');
    expect(snapshot.totalObjects).toBe(2);
    expect(snapshot.totalWorlds).toBe(1);
    expect(snapshot.totalModules).toBe(1);
    expect(snapshot.totalArtifacts).toBe(1);
    expect(snapshot.totalChangeEntries).toBe(1);
    expect(snapshot.totalMeshLinks).toBe(1);
  });

  it('parses and executes the UGR query surface', () => {
    const plan = parseUgrQuery('SELECT name FROM worlds WHERE domain = "governance" WITH LIMIT 1');
    const rows = runtime.query('SELECT name FROM worlds WHERE domain = "governance" WITH LIMIT 1');
    const aggregate = runtime.query('AGGREGATE kind FROM objects WHERE domain = "governance" WITH GROUP BY kind');

    expect(plan.form).toBe('SELECT');
    expect(plan.scope).toBe('worlds');
    expect(rows[0]).toMatchObject({
      id: 'world-1',
      name: 'Governance World',
    });
    expect(aggregate[0]).toMatchObject({
      groupBy: 'kind',
      group: 'knowledge',
      count: 1,
    });
  });

  it('replays ledger entries and compares entities deterministically', () => {
    const comparison = runtime.compare('world-1', 'world-1');
    const change = runtime.replayChange('change-1');

    expect(comparison.equal).toBe(true);
    expect(comparison.differences).toHaveLength(0);
    expect(change).toMatchObject({
      entryId: 'change-1',
      councilVoteSummary: 'unanimous',
    });
    expect(runtime.getLineage('world-1')).toEqual(expect.arrayContaining(['object-1']));
  });

  it('supports direct resolution of worlds, modules, and artifacts', () => {
    expect(runtime.resolveWorld('world-1')).toMatchObject({ id: 'world-1' });
    expect(runtime.resolveModule('module-1')).toMatchObject({ id: 'module-1' });
    expect(runtime.resolveArtifact('crf-1')).toMatchObject({ artifactId: 'crf-1' });
  });
});
