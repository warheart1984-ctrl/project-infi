import type { HardwareConsoleSummary } from '../../hardwareConsole.js';
import { Metric, gridStyle, sectionStyle, formatHardwareTemperature, formatHardwarePercent } from './shared.js';

export interface HardwareSummaryStripProps {
  hardwareConsole: HardwareConsoleSummary | null;
}

export function HardwareSummaryStrip({ hardwareConsole }: HardwareSummaryStripProps) {
  return (
    <section style={sectionStyle}>
      <h2>Hardware Console</h2>
      <p>Live CPU and GPU telemetry, constitutional replay, benchmark evidence, and routing justification appear here as operator-visible hardware evidence.</p>
      <div style={gridStyle}>
        <Metric label="Source" value={hardwareConsole?.source ?? 'loading'} />
        <Metric label="Nodes" value={String(hardwareConsole?.nodes.length ?? 0)} />
        <Metric label="Quarantined" value={String(hardwareConsole?.statusStrip.quarantinedNodes ?? 0)} />
        <Metric label="Throttle events" value={String(hardwareConsole?.statusStrip.throttlingEvents ?? 0)} />
        <Metric label="Avg utilization" value={formatHardwarePercent(hardwareConsole?.statusStrip.averageUtilization)} />
        <Metric label="Avg temps" value={`${formatHardwareTemperature(hardwareConsole?.statusStrip.averageCpuTempC)} / ${formatHardwareTemperature(hardwareConsole?.statusStrip.averageGpuTempC)}`} />
      </div>
    </section>
  );
}
