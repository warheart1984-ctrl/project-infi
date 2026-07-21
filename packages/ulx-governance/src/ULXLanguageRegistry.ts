export type ULXLanguageKind =
  | 'verb-language'
  | 'source-language'
  | 'constitutional-layer'
  | 'query-language'
  | 'package-language'
  | 'dsl'
  | 'spec-family'
  | 'replay-format'
  | 'runtime-surface';

export type ULXLanguageStatus = 'live' | 'spec-only' | 'bridge' | 'external';

export interface ULXLanguageDescriptor {
  id: string;
  name: string;
  kind: ULXLanguageKind;
  status: ULXLanguageStatus;
  ulxRole: string;
  source: string;
  aliases: readonly string[];
}

export interface ULXLanguageManifestEntry {
  id: string;
  name: string;
  kind: ULXLanguageKind;
  status: ULXLanguageStatus;
  ulxRole: string;
  source: string;
  aliases: readonly string[];
}

export interface ULXLanguageManifest {
  total: number;
  entries: readonly ULXLanguageManifestEntry[];
}

const DEFAULT_LANGUAGE_ENTRIES: readonly ULXLanguageDescriptor[] = [
  {
    id: 'UL',
    name: 'UL',
    kind: 'verb-language',
    status: 'live',
    ulxRole: 'Live verb-language runtime for imperative action phrasing before intent is normalized by ISL.',
    source: 'docs-site/docs/runtime/ul-runtime.md',
    aliases: ['ul language', 'verb language', 'universal language'],
  },
  {
    id: 'ULX',
    name: 'ULX',
    kind: 'source-language',
    status: 'live',
    ulxRole: 'Canonical source and bytecode format for constitutional execution.',
    source: 'docs-site/docs/ulx/ulx-language.md',
    aliases: ['ulx language', 'ulx source', 'ulx bytecode'],
  },
  {
    id: 'CSL',
    name: 'CSL',
    kind: 'constitutional-layer',
    status: 'live',
    ulxRole: 'Live constitutional schema layer for governed artifact schemas and evolution contracts.',
    source: 'docs-site/docs/runtime/csl-runtime.md',
    aliases: ['constitutional schema layer'],
  },
  {
    id: 'ISL',
    name: 'ISL',
    kind: 'constitutional-layer',
    status: 'live',
    ulxRole: 'Intent layer for governed requests and authority bindings.',
    source: 'docs/specifications/aaes-os-constitutional-kernel-specification.md',
    aliases: ['intent specification layer'],
  },
  {
    id: 'CIC',
    name: 'CIC',
    kind: 'constitutional-layer',
    status: 'live',
    ulxRole: 'Live inference layer for deterministic constitutional reasoning and semantic graphs.',
    source: 'docs-site/docs/runtime/cic-runtime.md',
    aliases: ['constitutional inference contract'],
  },
  {
    id: 'CCC',
    name: 'CCC',
    kind: 'constitutional-layer',
    status: 'live',
    ulxRole: 'Live continuity layer for replay contracts, lineage invariants, and time-bound governance.',
    source: 'docs-site/docs/runtime/ccc-runtime.md',
    aliases: ['constitutional continuity contract'],
  },
  {
    id: 'COE',
    name: 'COE',
    kind: 'constitutional-layer',
    status: 'live',
    ulxRole: 'Live execution layer for constitutional routes, schedules, promotion workflows, and receipts.',
    source: 'docs-site/docs/runtime/coe-runtime.md',
    aliases: ['constitutional operation engine'],
  },
  {
    id: 'UGR',
    name: 'UGR',
    kind: 'runtime-surface',
    status: 'live',
    ulxRole: 'Unified general repository runtime for governed knowledge, queries, packages, and replay.',
    source: 'docs-site/docs/runtime/ugr-runtime.md',
    aliases: ['unified general repository'],
  },
  {
    id: 'UGQL',
    name: 'UGQL',
    kind: 'query-language',
    status: 'live',
    ulxRole: 'Query facet of the live UGR runtime for selecting, tracing, and comparing knowledge.',
    source: 'docs-site/docs/runtime/ugr-runtime.md',
    aliases: ['ugql language', 'query language'],
  },
  {
    id: 'UPL',
    name: 'UPL',
    kind: 'package-language',
    status: 'live',
    ulxRole: 'Package facet of the live UGR runtime for worlds, constitutions, rules, agents, and arenas.',
    source: 'docs-site/docs/runtime/ugr-runtime.md',
    aliases: ['upl language', 'universal policy language'],
  },
  {
    id: 'CRF',
    name: 'CRF',
    kind: 'replay-format',
    status: 'live',
    ulxRole: 'Replay facet of the live UGR runtime for portable constitutional replay artifacts.',
    source: 'docs-site/docs/runtime/ugr-runtime.md',
    aliases: ['constitutional replay file'],
  },
  {
    id: 'Policy DSL',
    name: 'Policy DSL',
    kind: 'dsl',
    status: 'live',
    ulxRole: 'Routing and guardrail rules for governed requests.',
    source: 'docs-site/docs/governance/policy-dsl.md',
    aliases: ['policy language', 'policy'],
  },
  {
    id: 'Replay DSL',
    name: 'Replay DSL',
    kind: 'dsl',
    status: 'live',
    ulxRole: 'Replay scenario language for deterministic recreation of governance runs.',
    source: 'docs/proof/platform/HARDWARE_GOVERNANCE_PLAYBOOK.md',
    aliases: ['replay language', 'replay studio'],
  },
  {
    id: 'CML-2',
    name: 'CML-2',
    kind: 'spec-family',
    status: 'live',
    ulxRole: 'Live corpus family in the CML/Voss runtime surface for governed meaning constraints.',
    source: 'docs-site/docs/runtime/cml-voss-runtime.md',
    aliases: ['cml2'],
  },
  {
    id: 'CVM-1',
    name: 'CVM-1',
    kind: 'spec-family',
    status: 'live',
    ulxRole: 'Live corpus family in the CML/Voss runtime surface for governed verification models.',
    source: 'docs-site/docs/runtime/cml-voss-runtime.md',
    aliases: ['cvm1'],
  },
  {
    id: 'The Voss Binding',
    name: 'The Voss Binding',
    kind: 'spec-family',
    status: 'live',
    ulxRole: 'Live binding protocol between CML-2 meaning constraints and CVM-1 verification models.',
    source: 'docs-site/docs/runtime/cml-voss-runtime.md',
    aliases: ['voss binding', 'voss'],
  },
  {
    id: 'CodaDoc',
    name: 'CodaDoc',
    kind: 'runtime-surface',
    status: 'live',
    ulxRole: 'Documentation catalog surface in the live Coda stack.',
    source: 'docs-site/docs/runtime/coda-doc.md',
    aliases: ['coda doc'],
  },
  {
    id: 'CodaRuntime',
    name: 'CodaRuntime',
    kind: 'runtime-surface',
    status: 'live',
    ulxRole: 'Runtime facade that composes the Coda corpus with NovaCoda.',
    source: 'docs-site/docs/runtime/coda-runtime.md',
    aliases: ['coda runtime'],
  },
  {
    id: 'NovaCoda',
    name: 'NovaCoda',
    kind: 'runtime-surface',
    status: 'live',
    ulxRole: 'Runtime facade over the Nova substrate and typed socket client.',
    source: 'docs-site/docs/runtime/nova-coda.md',
    aliases: ['nova coda'],
  },
  {
    id: 'GCRE-SYSMIN-001',
    name: 'GCRE-SYSMIN-001',
    kind: 'runtime-surface',
    status: 'live',
    ulxRole: 'Registry surface for the GCRE family and related corpus members.',
    source: 'docs-site/docs/runtime/gcre-sysmin.md',
    aliases: ['gcre sysmin 001', 'gcre sysmin'],
  },
];

function normalizeIdentifier(value: string): string {
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '');
}

function cloneEntry(entry: ULXLanguageDescriptor): ULXLanguageManifestEntry {
  return {
    id: entry.id,
    name: entry.name,
    kind: entry.kind,
    status: entry.status,
    ulxRole: entry.ulxRole,
    source: entry.source,
    aliases: [...entry.aliases],
  };
}

export class ULXLanguageRegistry {
  private readonly entries: readonly ULXLanguageDescriptor[];

  constructor(entries: readonly ULXLanguageDescriptor[] = DEFAULT_LANGUAGE_ENTRIES) {
    this.entries = [...entries];
  }

  list(): readonly ULXLanguageDescriptor[] {
    return [...this.entries];
  }

  find(identifier: string): ULXLanguageDescriptor | undefined {
    const needle = normalizeIdentifier(identifier);

    return this.entries.find((entry) => {
      if (normalizeIdentifier(entry.id) === needle) {
        return true;
      }

      if (normalizeIdentifier(entry.name) === needle) {
        return true;
      }

      return entry.aliases.some((alias) => normalizeIdentifier(alias) === needle);
    });
  }

  manifest(): ULXLanguageManifest {
    return {
      total: this.entries.length,
      entries: this.entries.map(cloneEntry),
    };
  }
}

export const ulxLanguageRegistry = new ULXLanguageRegistry();
