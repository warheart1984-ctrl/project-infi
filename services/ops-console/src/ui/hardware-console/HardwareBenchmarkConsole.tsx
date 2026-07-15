import type { HardwareConsoleSummary, HardwareRoute } from '../../hardwareConsole.js';
import { Panel, gridStyle, subtleTextStyle, buttonStyle, secondaryButtonStyle } from './shared.js';

export interface HardwareBenchmarkConsoleProps {
  hardwareConsole: HardwareConsoleSummary | null;
  onRunBenchmarks: (benchmarkId: string, routes: HardwareRoute[]) => void;
}

export function HardwareBenchmarkConsole({ hardwareConsole, onRunBenchmarks }: HardwareBenchmarkConsoleProps) {
  return (
    <Panel title="Benchmark Console">
      {hardwareConsole ? (
        <div style={{ display: 'grid', gap: 12 }}>
          <div style={gridStyle}>
            {hardwareConsole.benchmarkSpecs.map((spec) => (
              <Panel key={spec.id} title={spec.name}>
                <p style={subtleTextStyle}>{spec.description ?? 'Standard hardware benchmark'}</p>
                <p>Type {spec.workloadType}</p>
                <p>Targets {spec.targetRoutes.join(', ')}</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  <button type="button" style={buttonStyle} onClick={() => onRunBenchmarks(spec.id, ['cpu'])}>Run CPU</button>
                  <button type="button" style={buttonStyle} onClick={() => onRunBenchmarks(spec.id, ['gpu'])}>Run GPU</button>
                  <button type="button" style={secondaryButtonStyle} onClick={() => onRunBenchmarks(spec.id, ['cpu', 'gpu'])}>Run both</button>
                </div>
              </Panel>
            ))}
          </div>
          {hardwareConsole.latestBenchmarkRun ? (
            <Panel title="Latest Benchmark Evidence">
              <p>Artifact {hardwareConsole.hardwareEvidenceRefs[0] ?? 'latest-benchmark-evidence'}</p>
              <p>Route {hardwareConsole.latestBenchmarkRun.route}</p>
              <p>Evidence refs {hardwareConsole.latestBenchmarkRun.evidenceRefs.join(', ') || 'none'}</p>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{JSON.stringify(hardwareConsole.latestBenchmarkRun.metrics, null, 2)}</pre>
            </Panel>
          ) : (
            <p style={subtleTextStyle}>No benchmark runs recorded yet.</p>
          )}
        </div>
      ) : (
        <p style={subtleTextStyle}>Benchmark console is loading.</p>
      )}
    </Panel>
  );
}
