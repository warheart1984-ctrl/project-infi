import { createHash } from 'node:crypto';

export type GcreFamilyStatus = 'live' | 'mixed' | 'doc-forward';

export type GcreFamilyKind = 'family' | 'specification' | 'binding' | 'runtime';

export interface GcreFamilyMember {
  id: string;
  displayName: string;
  kind: GcreFamilyKind;
  status: GcreFamilyStatus;
  summary: string;
  references: string[];
  aliases: string[];
}

export interface GcreFamilyEdge {
  from: string;
  to: string;
  relation: 'root' | 'related' | 'alias' | 'reference';
}

export interface GcreFamilyGraph {
  members: GcreFamilyMember[];
  edges: GcreFamilyEdge[];
  fingerprint: string;
}

export interface GcreSysminSnapshot {
  packageName: '@aaes-os/gcre-sysmin';
  rootFamily: string;
  total: number;
  live: number;
  mixed: number;
  docForward: number;
  liveMembers: string[];
  docForwardMembers: string[];
  fingerprint: string;
}

const DEFAULT_FAMILY: readonly GcreFamilyMember[] = [
  {
    id: 'gcre-sysmin-001',
    displayName: 'GCRE-SYSMIN-001',
    kind: 'specification',
    status: 'live',
    summary: 'Root GCRE-SYSMIN-001 family surface for the extracted AAES-OS canon.',
    references: [
      'packages/gcre-sysmin/src/index.ts',
      'docs/specifications/README.md',
    ],
    aliases: ['GCRE-SYSMIN-001'],
  },
  {
    id: 'gcre',
    displayName: 'GCRE',
    kind: 'family',
    status: 'live',
    summary: 'Canonical GCRE family root that resolves the SYSMIN-001 surface and its related language names.',
    references: [
      'packages/gcre-sysmin/src/index.ts',
      'docs/specifications/README.md',
    ],
    aliases: ['GCRE'],
  },
  {
    id: 'cml-2',
    displayName: 'CML-2',
    kind: 'specification',
    status: 'doc-forward',
    summary: 'CML-2 remains a doc-forward member of the GCRE-adjacent corpus family.',
    references: ['docs/proof/platform/META_CONSTITUTIONAL_COLLAPSE.md'],
    aliases: ['CML-2'],
  },
  {
    id: 'cvm-1',
    displayName: 'CVM-1',
    kind: 'specification',
    status: 'doc-forward',
    summary: 'CVM-1 remains a doc-forward member of the GCRE-adjacent corpus family.',
    references: ['docs/proof/platform/META_CONSTITUTIONAL_COLLAPSE.md'],
    aliases: ['CVM-1'],
  },
  {
    id: 'the-voss-binding',
    displayName: 'The Voss Binding',
    kind: 'binding',
    status: 'doc-forward',
    summary: 'The Voss Binding is a doc-forward binding member of the extracted family.',
    references: ['docs/specifications/README.md'],
    aliases: ['The Voss Binding', 'Voss Binding', 'voss-binding'],
  },
];

export function buildGcreFamily(): GcreFamilyMember[] {
  return DEFAULT_FAMILY.map(cloneMember);
}

export function findGcreFamilyMember(query: string, family: readonly GcreFamilyMember[] = DEFAULT_FAMILY): GcreFamilyMember | undefined {
  const normalized = query.trim().toLowerCase();
  if (!normalized) {
    return undefined;
  }

  return family.find((member) => {
    if (member.id.toLowerCase() === normalized) {
      return true;
    }
    if (member.displayName.toLowerCase() === normalized) {
      return true;
    }
    return member.aliases.some((alias) => alias.toLowerCase() === normalized);
  });
}

export function buildGcreFamilyGraph(family: readonly GcreFamilyMember[] = DEFAULT_FAMILY): GcreFamilyGraph {
  const members = family.map(cloneMember);
  const edges: GcreFamilyEdge[] = [];

  for (const member of members) {
    if (member.id === 'gcre-sysmin-001') {
      edges.push({ from: member.id, to: 'gcre', relation: 'related' });
    }
    for (const alias of member.aliases) {
      if (alias.toLowerCase() !== member.displayName.toLowerCase()) {
        edges.push({ from: member.id, to: alias, relation: 'alias' });
      }
    }
    for (const reference of member.references) {
      edges.push({ from: member.id, to: reference, relation: 'reference' });
    }
  }

  edges.unshift({ from: 'gcre-sysmin-001', to: 'gcre-sysmin-001', relation: 'root' });

  return {
    members,
    edges,
    fingerprint: fingerprintFamily(members),
  };
}

export function summarizeGcreFamily(family: readonly GcreFamilyMember[] = DEFAULT_FAMILY): GcreSysminSnapshot {
  const graph = buildGcreFamilyGraph(family);
  const liveMembers = graph.members.filter((member) => member.status === 'live').map((member) => member.displayName);
  const docForwardMembers = graph.members.filter((member) => member.status !== 'live').map((member) => member.displayName);

  return {
    packageName: '@aaes-os/gcre-sysmin',
    rootFamily: 'GCRE-SYSMIN-001',
    total: graph.members.length,
    live: liveMembers.length,
    mixed: graph.members.filter((member) => member.status === 'mixed').length,
    docForward: docForwardMembers.length,
    liveMembers,
    docForwardMembers,
    fingerprint: graph.fingerprint,
  };
}

export class GcreSysminRuntime {
  constructor(private readonly family: readonly GcreFamilyMember[] = DEFAULT_FAMILY) {}

  snapshot(): GcreSysminSnapshot {
    return summarizeGcreFamily(this.family);
  }

  resolve(query: string): GcreFamilyMember | undefined {
    return findGcreFamilyMember(query, this.family);
  }

  graph(): GcreFamilyGraph {
    return buildGcreFamilyGraph(this.family);
  }
}

export function createGcreSysminRuntime(family?: readonly GcreFamilyMember[]): GcreSysminRuntime {
  return new GcreSysminRuntime(family);
}

export { DEFAULT_FAMILY as GCRE_SYSMIN_FAMILY };

function cloneMember(member: GcreFamilyMember): GcreFamilyMember {
  return {
    ...member,
    references: [...member.references],
    aliases: [...member.aliases],
  };
}

function fingerprintFamily(family: readonly GcreFamilyMember[]): string {
  return createHash('sha256')
    .update(
      JSON.stringify(
        family
          .map((member) => ({
            id: member.id,
            displayName: member.displayName,
            kind: member.kind,
            status: member.status,
            references: [...member.references].sort(),
            aliases: [...member.aliases].sort(),
          }))
          .sort((left, right) => left.id.localeCompare(right.id)),
      ),
    )
    .digest('hex');
}
