export type CodaCorpusStatus = 'live' | 'mixed' | 'doc-forward';

export type CodaCorpusKind = 'package' | 'runtime' | 'specification' | 'binding' | 'substrate';

export interface CodaCorpusRecord {
  id: string;
  displayName: string;
  kind: CodaCorpusKind;
  status: CodaCorpusStatus;
  summary: string;
  references: string[];
  aliases: string[];
}

const DEFAULT_CORPUS: readonly CodaCorpusRecord[] = [
  {
    id: 'codadoc',
    displayName: 'CodaDoc',
    kind: 'package',
    status: 'live',
    summary: 'Canonical documentation surface for the Coda stack and its public corpus.',
    references: [
      'docs/specifications/README.md',
      'docs-site/docs/overview.md',
    ],
    aliases: ['CodaDoc', 'coda-doc'],
  },
  {
    id: 'coda-runtime',
    displayName: 'CodaRuntime',
    kind: 'runtime',
    status: 'live',
    summary: 'Live runtime facade that composes the documented corpus with the NovaCoda substrate.',
    references: [
      'packages/coda-runtime/src/index.ts',
      'packages/nova-coda/src/index.ts',
    ],
    aliases: ['CodaRuntime', 'coda-runtime'],
  },
  {
    id: 'nova-coda',
    displayName: 'NovaCoda',
    kind: 'substrate',
    status: 'live',
    summary: 'Live substrate/client pair backed by the Rust NovaCoda socket substrate and the TypeScript client.',
    references: [
      'packages/nova-substrate/src/main.rs',
      'packages/nova-substrate-client/src/NovaCodaClient.ts',
    ],
    aliases: ['NovaCoda', 'nova-coda'],
  },
  {
    id: 'isl',
    displayName: 'ISL',
    kind: 'specification',
    status: 'live',
    summary: 'Intent Specification Layer, now surfaced as a live runtime package for governed intents, evidence, and authority.',
    references: [
      'packages/isl-runtime/src/index.ts',
      'docs/specifications/aaes-os-constitutional-kernel-specification.md',
      'docs/specifications/aaes-os-constitutional-kernel.schema.json',
    ],
    aliases: ['ISL', 'Intent Specification Layer'],
  },
  {
    id: 'cml-2',
    displayName: 'CML-2',
    kind: 'specification',
    status: 'doc-forward',
    summary: 'CML-2 is present in the corpus as a governance language name and remains doc-forward in this checkout.',
    references: [
      'docs/proof/platform/META_CONSTITUTIONAL_COLLAPSE.md',
    ],
    aliases: ['CML-2'],
  },
  {
    id: 'cvm-1',
    displayName: 'CVM-1',
    kind: 'specification',
    status: 'doc-forward',
    summary: 'CVM-1 appears in the corpus as part of the meta-constitutional naming family and is still doc-forward.',
    references: [
      'docs/proof/platform/META_CONSTITUTIONAL_COLLAPSE.md',
    ],
    aliases: ['CVM-1'],
  },
  {
    id: 'the-voss-binding',
    displayName: 'The Voss Binding',
    kind: 'binding',
    status: 'doc-forward',
    summary: 'The Voss Binding remains a corpus name for a binding or contract surface that is not yet a separate live package.',
    references: [
      'docs/specifications/README.md',
    ],
    aliases: ['The Voss Binding', 'Voss Binding', 'voss-binding'],
  },
  {
    id: 'gcre-sysmin-001',
    displayName: 'GCRE-SYSMIN-001',
    kind: 'specification',
    status: 'live',
    summary: 'GCRE-SYSMIN-001 is now surfaced as a live family registry with a runtime package surface.',
    references: [
      'packages/gcre-sysmin/src/index.ts',
      'docs/specifications/README.md',
      'docs/specifications/aaes-os-constitutional-kernel-specification.md',
    ],
    aliases: ['GCRE-SYSMIN-001', 'GCRE'],
  },
];

function cloneRecord(record: CodaCorpusRecord): CodaCorpusRecord {
  return {
    ...record,
    references: [...record.references],
    aliases: [...record.aliases],
  };
}

export function buildCodaCorpus(): CodaCorpusRecord[] {
  return DEFAULT_CORPUS.map(cloneRecord);
}

export function findCodaCorpusRecord(query: string, corpus: readonly CodaCorpusRecord[] = DEFAULT_CORPUS): CodaCorpusRecord | undefined {
  const normalized = query.trim().toLowerCase();
  if (!normalized) {
    return undefined;
  }

  return corpus.find((record) => {
    if (record.id.toLowerCase() === normalized) {
      return true;
    }
    if (record.displayName.toLowerCase() === normalized) {
      return true;
    }
    return record.aliases.some((alias) => alias.toLowerCase() === normalized);
  });
}

export function summarizeCodaCorpus(corpus: readonly CodaCorpusRecord[] = DEFAULT_CORPUS): {
  total: number;
  live: number;
  mixed: number;
  docForward: number;
} {
  return corpus.reduce(
    (summary, record) => {
      summary.total += 1;
      if (record.status === 'live') {
        summary.live += 1;
      } else if (record.status === 'mixed') {
        summary.mixed += 1;
      } else {
        summary.docForward += 1;
      }
      return summary;
    },
    { total: 0, live: 0, mixed: 0, docForward: 0 },
  );
}
