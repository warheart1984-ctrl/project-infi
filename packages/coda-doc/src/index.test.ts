import { describe, expect, it } from 'vitest';

import { buildCodaCorpus, findCodaCorpusRecord, summarizeCodaCorpus } from './index.js';

describe('coda-doc corpus', () => {
  it('exposes the live and doc-forward corpus records', () => {
    const corpus = buildCodaCorpus();
    expect(corpus.map((record) => record.displayName)).toEqual(
      expect.arrayContaining([
        'CodaDoc',
        'CodaRuntime',
        'NovaCoda',
        'ISL',
        'CML-2',
        'CVM-1',
        'The Voss Binding',
        'GCRE-SYSMIN-001',
      ]),
    );
    expect(findCodaCorpusRecord('gcre')).toBeTruthy();
    expect(findCodaCorpusRecord('The Voss Binding')).toBeTruthy();
  });

  it('summarizes the corpus maturity split', () => {
    const summary = summarizeCodaCorpus();
    expect(summary.total).toBe(8);
    expect(summary.live).toBe(5);
    expect(summary.docForward).toBe(3);
  });
});
