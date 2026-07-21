import { describe, expect, it } from 'vitest';

import {
  getDefaultManagedServiceId,
  getManagedServiceStatus,
  listManagedServiceSummaries,
} from './operatorConsole';

describe('managed service adapter specification', () => {
  it('registers the canonical adapter set', () => {
    const summaries = listManagedServiceSummaries();
    const ids = new Set(summaries.map((summary) => summary.id));

    expect(getDefaultManagedServiceId()).toBe('dropbox');
    expect(ids.has('dropbox')).toBe(true);
    expect(ids.has('ulx')).toBe(true);
    expect(ids.has('cori-alpha')).toBe(true);
    expect(ids.has('sovereignx')).toBe(true);
    expect(ids.has('nova')).toBe(true);
    expect(ids.has('ai-factory')).toBe(true);
    expect(ids.has('research-os')).toBe(true);
  });

  it('exposes non-empty contract fields for each adapter', () => {
    for (const summary of listManagedServiceSummaries()) {
      expect(summary.label.trim().length).toBeGreaterThan(0);
      expect(summary.description.trim().length).toBeGreaterThan(0);
      expect(summary.actions.length).toBeGreaterThan(0);
      for (const action of summary.actions) {
        expect(action.action.trim().length).toBeGreaterThan(0);
        expect(action.label.trim().length).toBeGreaterThan(0);
        expect(action.description.trim().length).toBeGreaterThan(0);
      }
    }
  });

  it('exposes concrete status snapshots for AI Factory and Research OS', async () => {
    const [aiFactory, researchOs] = await Promise.all([
      getManagedServiceStatus('ai-factory'),
      getManagedServiceStatus('research-os'),
    ]);

    expect(aiFactory).not.toBeNull();
    expect(aiFactory?.serviceDisplayName).toBe('AI Factory');
    expect(aiFactory?.backend).toBe('governance-retirement');
    expect(aiFactory?.lastStartupLine).toContain('backend=governance-retirement');

    expect(researchOs).not.toBeNull();
    expect(researchOs?.serviceDisplayName).toBe('Research OS');
    expect(researchOs?.backend).toBe('frozen-research-corpus');
    expect(researchOs?.lastStartupLine).toContain('backend=frozen-research-corpus');
  });

  it('keeps Dropbox as the first production adapter', () => {
    const [first] = listManagedServiceSummaries();
    expect(first?.id).toBe('dropbox');
  });
});
