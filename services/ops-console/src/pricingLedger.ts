import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import path from 'node:path';

import type { SovereignRouterXPricingLedgerEntry } from '@aaes-os/sovereignx-router';

export interface PricingLedgerSummary {
  available: boolean;
  storePath: string;
  entryCount: number;
  totalRevenueUsd: number;
  totalCostUsd: number;
  totalGrossMarginUsd: number;
  grossMarginPct: number;
  recentEntries: SovereignRouterXPricingLedgerEntry[];
  bySegment: {
    segment: SovereignRouterXPricingLedgerEntry['segment'];
    entryCount: number;
    revenueUsd: number;
    costUsd: number;
    grossMarginUsd: number;
    grossMarginPct: number;
  }[];
  byStrategy: {
    strategy: SovereignRouterXPricingLedgerEntry['strategy'];
    entryCount: number;
    revenueUsd: number;
    costUsd: number;
    grossMarginUsd: number;
    grossMarginPct: number;
  }[];
  cohortHistory: PricingCohortHistoryRow[];
}

export interface PricingCohortHistoryRow {
  cohort: string;
  entryCount: number;
  revenueUsd: number;
  costUsd: number;
  grossMarginUsd: number;
  grossMarginPct: number;
  strategyMix: string[];
}

export interface PricingLedgerValidationIssue {
  path: string;
  message: string;
}

const DEFAULT_STORE_PATH = path.join(process.cwd(), '.runtime', 'ops-console-pricing-ledger.jsonl');

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function addIssue(issues: PricingLedgerValidationIssue[], path: string, message: string): void {
  issues.push({ path, message });
}

function validateEntry(value: unknown): { valid: boolean; issues: PricingLedgerValidationIssue[] } {
  const issues: PricingLedgerValidationIssue[] = [];
  if (!isRecord(value)) {
    addIssue(issues, '', 'must be an object');
    return { valid: false, issues };
  }

  const stringFields: Array<keyof SovereignRouterXPricingLedgerEntry> = [
    'requestId',
    'recordedAt',
    'segment',
    'strategy',
    'selectedModel',
    'backend',
    'routeReason',
  ];
  for (const key of stringFields) {
    if (!isNonEmptyString(value[key])) {
      addIssue(issues, String(key), 'must be a non-empty string');
    }
  }

  const numericFields: Array<keyof SovereignRouterXPricingLedgerEntry> = [
    'routedRequests',
    'monthlyCustomers',
    'estimatedRevenueUsd',
    'estimatedCostUsd',
    'estimatedGrossMarginUsd',
    'estimatedGrossMarginPct',
  ];
  for (const key of numericFields) {
    if (!isFiniteNumber(value[key])) {
      addIssue(issues, String(key), 'must be a finite number');
    }
  }

  return { valid: issues.length === 0, issues };
}

function ensureStoreDir(storePath: string): void {
  mkdirSync(path.dirname(storePath), { recursive: true });
}

function readJsonl<T>(storePath: string): T[] {
  if (!existsSync(storePath)) {
    return [];
  }

  const contents = readFileSync(storePath, 'utf8');
  const entries: T[] = [];
  for (const line of contents.split(/\r?\n/)) {
    if (!line.trim()) {
      continue;
    }
    entries.push(JSON.parse(line) as T);
  }
  return entries;
}

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

function bucketCohort(recordedAt: string): string {
  const date = new Date(recordedAt);
  if (Number.isNaN(date.getTime())) {
    return 'unknown';
  }
  return date.toISOString().slice(0, 7);
}

function aggregateSegments(entries: SovereignRouterXPricingLedgerEntry[]): PricingLedgerSummary['bySegment'] {
  const groups = new Map<string, SovereignRouterXPricingLedgerEntry[]>();
  for (const entry of entries) {
    const groupKey = entry.segment;
    const list = groups.get(groupKey) ?? [];
    list.push(entry);
    groups.set(groupKey, list);
  }

  return Array.from(groups.entries())
    .map(([groupKey, groupEntries]) => {
      const revenueUsd = groupEntries.reduce((sum, entry) => sum + entry.estimatedRevenueUsd, 0);
      const costUsd = groupEntries.reduce((sum, entry) => sum + entry.estimatedCostUsd, 0);
      const grossMarginUsd = groupEntries.reduce((sum, entry) => sum + entry.estimatedGrossMarginUsd, 0);
      return {
        segment: groupKey as SovereignRouterXPricingLedgerEntry['segment'],
        entryCount: groupEntries.length,
        revenueUsd: round(revenueUsd),
        costUsd: round(costUsd),
        grossMarginUsd: round(grossMarginUsd),
        grossMarginPct: revenueUsd > 0 ? round((grossMarginUsd / revenueUsd) * 100) : 0,
      };
    })
    .sort((left, right) => right.entryCount - left.entryCount || right.grossMarginUsd - left.grossMarginUsd);
}

function aggregateStrategies(entries: SovereignRouterXPricingLedgerEntry[]): PricingLedgerSummary['byStrategy'] {
  const groups = new Map<string, SovereignRouterXPricingLedgerEntry[]>();
  for (const entry of entries) {
    const groupKey = entry.strategy;
    const list = groups.get(groupKey) ?? [];
    list.push(entry);
    groups.set(groupKey, list);
  }

  return Array.from(groups.entries())
    .map(([groupKey, groupEntries]) => {
      const revenueUsd = groupEntries.reduce((sum, entry) => sum + entry.estimatedRevenueUsd, 0);
      const costUsd = groupEntries.reduce((sum, entry) => sum + entry.estimatedCostUsd, 0);
      const grossMarginUsd = groupEntries.reduce((sum, entry) => sum + entry.estimatedGrossMarginUsd, 0);
      return {
        strategy: groupKey as SovereignRouterXPricingLedgerEntry['strategy'],
        entryCount: groupEntries.length,
        revenueUsd: round(revenueUsd),
        costUsd: round(costUsd),
        grossMarginUsd: round(grossMarginUsd),
        grossMarginPct: revenueUsd > 0 ? round((grossMarginUsd / revenueUsd) * 100) : 0,
      };
    })
    .sort((left, right) => right.entryCount - left.entryCount || right.grossMarginUsd - left.grossMarginUsd);
}

function aggregateCohorts(entries: SovereignRouterXPricingLedgerEntry[]): PricingCohortHistoryRow[] {
  const groups = new Map<string, SovereignRouterXPricingLedgerEntry[]>();
  for (const entry of entries) {
    const cohort = bucketCohort(entry.recordedAt);
    const list = groups.get(cohort) ?? [];
    list.push(entry);
    groups.set(cohort, list);
  }

  return Array.from(groups.entries())
    .map(([cohort, cohortEntries]) => {
      const revenueUsd = cohortEntries.reduce((sum, entry) => sum + entry.estimatedRevenueUsd, 0);
      const costUsd = cohortEntries.reduce((sum, entry) => sum + entry.estimatedCostUsd, 0);
      const grossMarginUsd = cohortEntries.reduce((sum, entry) => sum + entry.estimatedGrossMarginUsd, 0);
      const strategies = Array.from(new Set(cohortEntries.map((entry) => entry.strategy))).sort();
      return {
        cohort,
        entryCount: cohortEntries.length,
        revenueUsd: round(revenueUsd),
        costUsd: round(costUsd),
        grossMarginUsd: round(grossMarginUsd),
        grossMarginPct: revenueUsd > 0 ? round((grossMarginUsd / revenueUsd) * 100) : 0,
        strategyMix: strategies,
      };
    })
    .sort((left, right) => left.cohort.localeCompare(right.cohort));
}

export function getPricingLedgerStorePath(): string {
  return process.env.PRICING_LEDGER_PATH ?? DEFAULT_STORE_PATH;
}

export function readPricingLedgerEntries(storePath = getPricingLedgerStorePath()): SovereignRouterXPricingLedgerEntry[] {
  try {
    return readJsonl<SovereignRouterXPricingLedgerEntry>(storePath);
  } catch {
    return [];
  }
}

export function appendPricingLedgerEntry(
  entry: SovereignRouterXPricingLedgerEntry,
  storePath = getPricingLedgerStorePath(),
): SovereignRouterXPricingLedgerEntry {
  const validation = validateEntry(entry);
  if (!validation.valid) {
    const details = validation.issues.map((issue) => `${issue.path}: ${issue.message}`).join('; ');
    throw new Error(`Invalid pricing ledger entry: ${details}`);
  }

  ensureStoreDir(storePath);
  appendFileSync(storePath, `${JSON.stringify(entry)}\n`, 'utf8');
  return entry;
}

export function summarizePricingLedger(storePath = getPricingLedgerStorePath()): PricingLedgerSummary {
  const entries = readPricingLedgerEntries(storePath);
  const totalRevenueUsd = entries.reduce((sum, entry) => sum + entry.estimatedRevenueUsd, 0);
  const totalCostUsd = entries.reduce((sum, entry) => sum + entry.estimatedCostUsd, 0);
  const totalGrossMarginUsd = entries.reduce((sum, entry) => sum + entry.estimatedGrossMarginUsd, 0);
  return {
    available: existsSync(storePath),
    storePath,
    entryCount: entries.length,
    totalRevenueUsd: round(totalRevenueUsd),
    totalCostUsd: round(totalCostUsd),
    totalGrossMarginUsd: round(totalGrossMarginUsd),
    grossMarginPct: totalRevenueUsd > 0 ? round((totalGrossMarginUsd / totalRevenueUsd) * 100) : 0,
    recentEntries: entries.slice(-10).reverse(),
    bySegment: aggregateSegments(entries),
    byStrategy: aggregateStrategies(entries),
    cohortHistory: aggregateCohorts(entries),
  };
}

export function createPricingLedgerEntryResponse(entry: SovereignRouterXPricingLedgerEntry): {
  entry: SovereignRouterXPricingLedgerEntry;
  summary: PricingLedgerSummary;
} {
  const persisted = appendPricingLedgerEntry(entry);
  return {
    entry: persisted,
    summary: summarizePricingLedger(),
  };
}

export function renderPricingMarginReportCsv(summary = summarizePricingLedger()): string {
  const rows = [
    ['scope', 'name', 'entryCount', 'revenueUsd', 'costUsd', 'grossMarginUsd', 'grossMarginPct'],
    ['total', 'all', summary.entryCount, summary.totalRevenueUsd, summary.totalCostUsd, summary.totalGrossMarginUsd, summary.grossMarginPct],
    ...summary.bySegment.map((row) => ['segment', row.segment, row.entryCount, row.revenueUsd, row.costUsd, row.grossMarginUsd, row.grossMarginPct]),
    ...summary.byStrategy.map((row) => ['strategy', row.strategy, row.entryCount, row.revenueUsd, row.costUsd, row.grossMarginUsd, row.grossMarginPct]),
  ];
  return `${rows.map((row) => row.map((cell) => JSON.stringify(cell)).join(',')).join('\n')}\n`;
}

export function renderPricingCohortHistoryCsv(summary = summarizePricingLedger()): string {
  const rows = [
    ['cohort', 'entryCount', 'revenueUsd', 'costUsd', 'grossMarginUsd', 'grossMarginPct', 'strategyMix'],
    ...summary.cohortHistory.map((row) => [row.cohort, row.entryCount, row.revenueUsd, row.costUsd, row.grossMarginUsd, row.grossMarginPct, row.strategyMix.join(' | ')]),
  ];
  return `${rows.map((row) => row.map((cell) => JSON.stringify(cell)).join(',')).join('\n')}\n`;
}
