import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

type CabEntry = {
  sequence: number;
  object_type: string;
  object_id: string;
  created_at: string;
  superseded?: boolean;
  payload?: Record<string, unknown>;
};

type CabInvariantResult = {
  invariantId: 'CL' | 'RC' | 'TI' | 'SU' | 'NE';
  name: string;
  status: 'pass' | 'fail';
  detail: string;
};

export type CabTelemetrySummary = {
  available: boolean;
  storePath: string;
  entryCount: number;
  activeCount: number;
  latest: {
    intents: string[];
    decisions: string[];
    evidenceChains: string[];
    continuityReceipts: string[];
    reconstructionPlans: string[];
  };
  invariants: {
    passed: boolean;
    results: CabInvariantResult[];
  };
};

export function getCabTelemetrySummary(storePath = defaultCabStorePath()): CabTelemetrySummary {
  const entries = existsSync(storePath) ? readCabEntries(storePath) : [];
  const active = activeEntries(entries);
  const results = evaluateCabInvariants(entries, active);
  return {
    available: entries.length > 0,
    storePath,
    entryCount: entries.length,
    activeCount: active.length,
    latest: {
      intents: latestIds(active, 'IntentRecord'),
      decisions: latestIds(active, 'DecisionRecord'),
      evidenceChains: latestIds(active, 'EvidenceChain'),
      continuityReceipts: latestIds(active, 'ContinuityReceipt'),
      reconstructionPlans: latestIds(active, 'ReconstructionPlan'),
    },
    invariants: {
      passed: results.every((result) => result.status === 'pass'),
      results,
    },
  };
}

function defaultCabStorePath(): string {
  if (process.env.CAB_STORE?.trim()) {
    return path.resolve(process.env.CAB_STORE.trim());
  }
  const home = process.env.USERPROFILE || process.env.HOME || '.';
  return path.join(home, '.cab', 'ledger.jsonl');
}

function readCabEntries(storePath: string): CabEntry[] {
  return readFileSync(storePath, 'utf8')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line) as CabEntry);
}

function activeEntries(entries: CabEntry[]): CabEntry[] {
  const latest = new Map<string, CabEntry>();
  for (const entry of entries) {
    latest.set(entry.object_id, entry);
  }
  return [...latest.values()].filter((entry) => !entry.superseded && !entry.payload?.superseded_by);
}

function latestIds(entries: CabEntry[], objectType: string): string[] {
  return entries
    .filter((entry) => entry.object_type === objectType)
    .sort((a, b) => b.sequence - a.sequence)
    .slice(0, 5)
    .map((entry) => entry.object_id);
}

function evaluateCabInvariants(entries: CabEntry[], active: CabEntry[]): CabInvariantResult[] {
  const activeIds = new Set(active.map((entry) => entry.object_id));
  const decisions = active.filter((entry) => entry.object_type === 'DecisionRecord');
  const orphanDecisions = decisions
    .filter((entry) => {
      const refs = asStringArray(entry.payload?.intent_refs);
      return refs.length === 0 || refs.some((ref) => !activeIds.has(ref));
    })
    .map((entry) => entry.object_id);

  const plans = active.filter((entry) => entry.object_type === 'ReconstructionPlan');
  const missingPlanRefs = plans.flatMap((entry) =>
    asStringArray(entry.payload?.minimal_object_refs)
      .filter((ref) => !activeIds.has(ref))
      .map((ref) => `${entry.object_id}:${ref}`),
  );

  const sequences = entries.map((entry) => entry.sequence);
  const timestamps = entries.map((entry) => entry.created_at);
  const sequenceOk = sequences.every((sequence, index) => sequence === index + 1);
  const timestampsOk = timestamps.every((timestamp, index) => index === 0 || timestamps[index - 1] <= timestamp);

  const hasSuccessionProtocol = active.some((entry) => entry.object_type === 'SuccessionProtocol');
  const founderWithoutProtocol = active
    .filter((entry) => entry.object_type === 'FounderKnowledgeSnapshot')
    .filter((entry) => String(entry.payload?.succession_notes ?? '').trim() && !hasSuccessionProtocol)
    .map((entry) => entry.object_id);

  const nonErasureOk = entries.length >= active.length
    && entries.every((entry) => !entry.superseded || Boolean(entry.payload?.superseded_by));

  return [
    {
      invariantId: 'CL',
      name: 'causal_linkage',
      status: orphanDecisions.length === 0 ? 'pass' : 'fail',
      detail: orphanDecisions.join(', '),
    },
    {
      invariantId: 'RC',
      name: 'reconstructability',
      status: missingPlanRefs.length === 0 ? 'pass' : 'fail',
      detail: missingPlanRefs.join(', '),
    },
    {
      invariantId: 'TI',
      name: 'temporal_integrity',
      status: sequenceOk && timestampsOk ? 'pass' : 'fail',
      detail: sequenceOk && timestampsOk ? '' : 'sequence or timestamp order violated',
    },
    {
      invariantId: 'SU',
      name: 'succession',
      status: founderWithoutProtocol.length === 0 ? 'pass' : 'fail',
      detail: founderWithoutProtocol.join(', '),
    },
    {
      invariantId: 'NE',
      name: 'non_erasure',
      status: nonErasureOk ? 'pass' : 'fail',
      detail: nonErasureOk ? '' : 'superseded entry missing superseded_by link',
    },
  ];
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}
