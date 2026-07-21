import type { HardwareConsoleSummary, HardwareReplayArtifact } from '../../hardwareConsole.js';
import { Metric, Panel, gridStyle, subtleTextStyle } from './shared.js';

export interface HardwareReplayPanelProps {
  hardwareConsole: HardwareConsoleSummary | null;
  latestReplayComparison: HardwareReplayArtifact | null;
  hardwareEvidenceRefs: string[];
  onRunReplay: (workloadId: string, currentRoute: 'cpu' | 'gpu', counterfactualRoute: 'cpu' | 'gpu') => void;
}

export function HardwareReplayPanel({
  hardwareConsole,
  latestReplayComparison,
  hardwareEvidenceRefs,
  onRunReplay,
}: HardwareReplayPanelProps) {
  return (
    <Panel title="Replay Comparison">
      {latestReplayComparison ? (
        <div style={{ display: 'grid', gap: 8 }}>
          <p>Artifact {hardwareEvidenceRefs[1] ?? hardwareEvidenceRefs[0] ?? 'latest-replay-evidence'}</p>
          <p>{latestReplayComparison.currentRoute.toUpperCase()} vs {latestReplayComparison.counterfactualRoute.toUpperCase()}</p>
          <p>Evidence refs {hardwareConsole?.latestReplayComparison?.evidenceRefs.join(', ') || 'none'}</p>
          <div style={gridStyle}>
            <Metric label="Current p95" value={`${latestReplayComparison.comparison.currentMetrics.latencyP95Ms.toFixed(1)} ms`} />
            <Metric label="Counterfactual p95" value={`${latestReplayComparison.comparison.counterfactualMetrics.latencyP95Ms.toFixed(1)} ms`} />
            <Metric label="Delta" value={`${latestReplayComparison.comparison.delta.latencyP95Ms.toFixed(1)} ms`} />
            <Metric label="Cost delta" value={`$${latestReplayComparison.comparison.delta.costPerRequestUsd.toFixed(4)}`} />
          </div>
          <button
            type="button"
            style={actionButtonStyle}
            onClick={() => onRunReplay(
              latestReplayComparison.workloadId,
              latestReplayComparison.currentRoute,
              latestReplayComparison.counterfactualRoute,
            )}
          >
            Re-run latest replay
          </button>
        </div>
      ) : (
        <p style={subtleTextStyle}>No replay comparison has been recorded yet.</p>
      )}
    </Panel>
  );
}

const actionButtonStyle: React.CSSProperties = {
  border: 0,
  borderRadius: 8,
  padding: '8px 12px',
  background: '#1d4ed8',
  color: '#fff',
  cursor: 'pointer',
};
