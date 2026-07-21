import type { HardwareConsoleSummary } from '../../hardwareConsole.js';
import { Panel, barFillStyle, barTrackStyle, gridStyle, subtleTextStyle, formatHardwareTemperature, formatHardwarePercent, buttonStyle } from './shared.js';

export interface HardwareNodeGridProps {
  hardwareConsole: HardwareConsoleSummary | null;
  selectedHardwareNodeId: string | null;
  onSelectHardwareNode: (nodeId: string) => void;
  onRunReplay: (workloadId: string, currentRoute: 'cpu' | 'gpu', counterfactualRoute: 'cpu' | 'gpu') => void;
}

export function HardwareNodeGrid({ hardwareConsole, selectedHardwareNodeId, onSelectHardwareNode, onRunReplay }: HardwareNodeGridProps) {
  const nodes = hardwareConsole?.nodes ?? [];
  const selectedNode = nodes.find((node) => node.nodeId === selectedHardwareNodeId) ?? nodes[0] ?? null;

  return (
    <div style={gridStyle}>
      <Panel title="Cluster Overview">
        <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))' }}>
          {nodes.map((node) => (
            <button
              key={node.nodeId}
              type="button"
              onClick={() => onSelectHardwareNode(node.nodeId)}
              style={{
                border: node.nodeId === selectedNode?.nodeId ? '2px solid #1d4ed8' : '1px solid #d9e0ea',
                borderRadius: 10,
                padding: 12,
                textAlign: 'left',
                background: node.nodeId === selectedNode?.nodeId ? '#eff6ff' : '#fff',
                cursor: 'pointer',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
                <strong>{node.nodeId}</strong>
                <span>{node.quarantineState}</span>
              </div>
              <p style={subtleTextStyle}>{node.backend} · {node.routePreference.toUpperCase()}</p>
              <div style={barTrackStyle}>
                <span style={{ ...barFillStyle, width: `${Math.min(100, node.cpuUtilization)}%`, background: '#2563eb' }} />
              </div>
              <div style={barTrackStyle}>
                <span style={{ ...barFillStyle, width: `${Math.min(100, node.gpuUtilization)}%`, background: '#0f766e' }} />
              </div>
              <p style={subtleTextStyle}>CPU {formatHardwareTemperature(node.cpuTempC)}</p>
              <p style={subtleTextStyle}>GPU {formatHardwareTemperature(node.gpuTempC)}</p>
              <p style={subtleTextStyle}>Memory {formatHardwarePercent(node.memoryPressure)}</p>
              <p style={subtleTextStyle}>{node.thermalWarnings.length ? node.thermalWarnings.join(', ') : 'No thermal warnings'}</p>
            </button>
          ))}
        </div>
      </Panel>
      <Panel title="Node Detail">
        {selectedNode ? (
          <div style={{ display: 'grid', gap: 8 }}>
            <div style={gridStyle}>
              <div>
                <strong>Node</strong>
                <div>{selectedNode.nodeId}</div>
              </div>
              <div>
                <strong>Backend</strong>
                <div>{selectedNode.backend}</div>
              </div>
              <div>
                <strong>Quarantine</strong>
                <div>{selectedNode.quarantineState}</div>
              </div>
              <div>
                <strong>Route</strong>
                <div>{selectedNode.routePreference}</div>
              </div>
            </div>
            <p style={subtleTextStyle}>Observed {new Date(selectedNode.lastObservedAtMs).toISOString()}</p>
            <p>CPU utilization {formatHardwarePercent(selectedNode.cpuUtilization)}</p>
            <p>GPU utilization {formatHardwarePercent(selectedNode.gpuUtilization)}</p>
            <p>Voltage {selectedNode.voltageMv === null ? 'n/a' : `${selectedNode.voltageMv.toFixed(0)} mV`}</p>
            <p>Warnings {selectedNode.thermalWarnings.length ? selectedNode.thermalWarnings.join(', ') : 'none'}</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              <button
                type="button"
                style={buttonStyle}
                onClick={() => onRunReplay(
                  `workload:${selectedNode.nodeId}`,
                  selectedNode.routePreference === 'gpu' ? 'gpu' : 'cpu',
                  selectedNode.routePreference === 'gpu' ? 'cpu' : 'gpu',
                )}
              >
                Replay counterfactual
              </button>
            </div>
          </div>
        ) : (
          <p style={subtleTextStyle}>Select a node to inspect metrics and replay hooks.</p>
        )}
      </Panel>
    </div>
  );
}
