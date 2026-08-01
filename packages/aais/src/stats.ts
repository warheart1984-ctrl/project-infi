import type { AAISPreferredModel } from './capabilities.js';

export interface AAISRoutingEvent {
  capabilityName: string;
  model: AAISPreferredModel;
  overrideApplied: boolean;
  hintUsed: boolean;
  heuristicFallback: boolean;
}

export interface AAISRoutingStatsEntry {
  capabilityName: string;
  total: number;
  byModel: Record<AAISPreferredModel, number>;
  overrides: number;
  hintsUsed: number;
  heuristicFallbacks: number;
}

export interface AAISRoutingStatsSnapshot {
  byCapability: AAISRoutingStatsEntry[];
}

const routingStats = new Map<string, AAISRoutingStatsEntry>();

export function recordRoutingEvent(event: AAISRoutingEvent): void {
  const entry =
    routingStats.get(event.capabilityName) ??
    {
      capabilityName: event.capabilityName,
      total: 0,
      byModel: { 'qwen-3b': 0, 'qwen-7b': 0 },
      overrides: 0,
      hintsUsed: 0,
      heuristicFallbacks: 0,
    };

  entry.total += 1;
  entry.byModel[event.model] += 1;
  if (event.overrideApplied) {
    entry.overrides += 1;
  }
  if (event.hintUsed) {
    entry.hintsUsed += 1;
  }
  if (event.heuristicFallback) {
    entry.heuristicFallbacks += 1;
  }

  routingStats.set(event.capabilityName, entry);
}

export function getAAISRoutingStats(): AAISRoutingStatsSnapshot {
  return {
    byCapability: Array.from(routingStats.values()).map((entry) => ({
      capabilityName: entry.capabilityName,
      total: entry.total,
      byModel: { ...entry.byModel },
      overrides: entry.overrides,
      hintsUsed: entry.hintsUsed,
      heuristicFallbacks: entry.heuristicFallbacks,
    })),
  };
}

export function resetAAISRoutingStats(): void {
  routingStats.clear();
}
