import { useEffect, useState } from 'react';

import type { HardwareConsoleSummary } from '../../hardwareConsole.js';
import { sectionStyle, gridStyle } from './shared.js';
import { HardwareSummaryStrip } from './HardwareSummaryStrip.js';
import { HardwareNodeGrid } from './HardwareNodeGrid.js';
import { HardwareReplayPanel } from './HardwareReplayPanel.js';
import { HardwareBenchmarkConsole } from './HardwareBenchmarkConsole.js';
import { HardwareEvidencePanel } from './HardwareEvidencePanel.js';

export interface HardwareConsolePageProps {
  hardwareConsole: HardwareConsoleSummary | null;
  onHardwareRefreshRequested: () => void;
}

export function HardwareConsolePage({ hardwareConsole, onHardwareRefreshRequested }: HardwareConsolePageProps) {
  const [selectedHardwareNodeId, setSelectedHardwareNodeId] = useState<string | null>(null);

  useEffect(() => {
    if (!hardwareConsole || hardwareConsole.nodes.length === 0) {
      setSelectedHardwareNodeId(null);
      return;
    }

    const stillExists = selectedHardwareNodeId
      ? hardwareConsole.nodes.some((node) => node.nodeId === selectedHardwareNodeId)
      : false;

    if (!stillExists) {
      setSelectedHardwareNodeId(hardwareConsole.nodes[0].nodeId);
    }
  }, [hardwareConsole, selectedHardwareNodeId]);

  const latestReplayComparison = hardwareConsole?.latestReplayComparison ?? null;
  const hardwareEvidenceRefs = hardwareConsole?.hardwareEvidenceRefs ?? [];

  const runHardwareBenchmarks = async (benchmarkId: string, routes: ('cpu' | 'gpu' | 'mixed')[]) => {
    await fetch('/hardware/benchmarks/run', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ benchmarkId, routes }),
    });
    onHardwareRefreshRequested();
  };

  const runHardwareReplay = async (workloadId: string, currentRoute: 'cpu' | 'gpu', counterfactualRoute: 'cpu' | 'gpu') => {
    await fetch('/hardware/replay', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ workloadId, currentRoute, counterfactualRoute }),
    });
    onHardwareRefreshRequested();
  };

  return (
    <section id="hardware-console" style={sectionStyle}>
      <HardwareSummaryStrip hardwareConsole={hardwareConsole} />
      <div style={gridStyle}>
        <HardwareNodeGrid
          hardwareConsole={hardwareConsole}
          selectedHardwareNodeId={selectedHardwareNodeId}
          onSelectHardwareNode={setSelectedHardwareNodeId}
          onRunReplay={runHardwareReplay}
        />
        <HardwareReplayPanel
          hardwareConsole={hardwareConsole}
          latestReplayComparison={latestReplayComparison}
          hardwareEvidenceRefs={hardwareEvidenceRefs}
          onRunReplay={runHardwareReplay}
        />
      </div>
      <div style={gridStyle}>
        <HardwareBenchmarkConsole hardwareConsole={hardwareConsole} onRunBenchmarks={runHardwareBenchmarks} />
        <HardwareEvidencePanel hardwareConsole={hardwareConsole} />
      </div>
    </section>
  );
}
