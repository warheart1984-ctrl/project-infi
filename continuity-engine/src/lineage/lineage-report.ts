import type { ThresholdRegistry } from "../registry/threshold-registry";
import type { ThresholdVersion } from "../css2/types";

export async function pullThresholdHistory(
  registry: ThresholdRegistry,
  thresholdId: string,
): Promise<ThresholdVersion[]> {
  const history = await registry.getHistory(thresholdId);
  return history.sort((a, b) => a.version - b.version);
}

export function generateLineageReport(history: ThresholdVersion[]): string {
  if (history.length === 0) return "# No history found.\n";

  const thId = history[0]!.thresholdId;
  let md = `# Threshold Lineage Report\n\n`;
  md += `**Threshold ID:** ${thId}\n\n`;
  md += `## Version History\n\n`;

  for (const v of history) {
    md += `### Version ${v.version}\n`;
    md += `- **Timestamp:** ${v.snapshot.lastUpdatedAt}\n`;
    md += `- **Value:** ${String(v.snapshot.value)}\n`;
    md += `- **Comparator:** ${v.snapshot.comparator}\n`;
    md += `- **Intent:** ${v.snapshot.intent}\n`;
    md += `- **Rationale:** ${v.deltaRationale}\n`;
    if (v.recalibrationEventId) {
      md += `- **Recalibration Event:** ${v.recalibrationEventId}\n`;
    }
    md += `- **Updated By:** ${v.snapshot.lastUpdatedBy}\n\n`;
  }

  return md;
}
