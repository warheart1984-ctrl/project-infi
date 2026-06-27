import {
  DriftMetrics,
  FaultJournal,
  PatternLedger,
} from '@aaes-os/aaes-governance';

export function buildMetrics(journal: FaultJournal, patterns: PatternLedger): string {
  const faults = journal.getAll();
  const patternList = patterns.getAll();
  const drift = new DriftMetrics().computeDrift(faults, patternList);

  const lines: string[] = [];

  lines.push('# HELP aaes_drift_score Drift score (0–1).');
  lines.push('# TYPE aaes_drift_score gauge');
  lines.push(`aaes_drift_score ${drift.score}`);

  lines.push('# HELP aaes_fault_events_total Total fault events by code.');
  lines.push('# TYPE aaes_fault_events_total counter');
  const byCode = new Map<string, number>();
  for (const fault of faults) {
    byCode.set(fault.faultCode, (byCode.get(fault.faultCode) ?? 0) + 1);
  }
  for (const [code, count] of byCode.entries()) {
    lines.push(`aaes_fault_events_total{fault_code="${code}"} ${count}`);
  }

  lines.push('# HELP aaes_fault_pattern_recurrence Recurrence per pattern.');
  lines.push('# TYPE aaes_fault_pattern_recurrence gauge');
  for (const pattern of patternList) {
    lines.push(
      `aaes_fault_pattern_recurrence{pattern_id="${pattern.patternId}"} ${pattern.recurrence}`,
    );
  }

  return `${lines.join('\n')}\n`;
}
