import type { HardwareConsoleSummary } from '../../hardwareConsole.js';
import { Panel, subtleTextStyle } from './shared.js';

export interface HardwareEvidencePanelProps {
  hardwareConsole: HardwareConsoleSummary | null;
}

export function HardwareEvidencePanel({ hardwareConsole }: HardwareEvidencePanelProps) {
  return (
    <Panel title="Hardware Evidence Viewer">
      {hardwareConsole ? (
        <ul>
          <li>Latest benchmark refs: {hardwareConsole.latestBenchmarkRun ? hardwareConsole.latestBenchmarkRun.evidenceRefs.join(', ') || 'none' : 'none'}</li>
          <li>Latest replay refs: {hardwareConsole.latestReplayComparison ? hardwareConsole.latestReplayComparison.evidenceRefs.join(', ') || 'none' : 'none'}</li>
          <li>Hardware evidence refs: {hardwareConsole.hardwareEvidenceRefs.join(', ') || 'none'}</li>
          <li>Cluster decision: {hardwareConsole.clusterDecision.reason}</li>
        </ul>
      ) : (
        <p style={subtleTextStyle}>Hardware evidence is loading.</p>
      )}
    </Panel>
  );
}
