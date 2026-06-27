import type { SkillzMcgeeLedgerSummary } from '../state/studioState.js';

export function DriftVisualizer({ skillzmcgee }: { skillzmcgee: SkillzMcgeeLedgerSummary }) {
  const driftRows = Object.entries(skillzmcgee.state).map(([slice, state]) => ({
    slice,
    verdict: state.last_status === 'ok' ? 'expected-aligned' : 'review',
    lastRun: state.last_run_id,
  }));
  return (
    <div>
      <h3 style={{ marginTop: 0 }}>Drift Visualizer</h3>
      <table>
        <thead><tr><th>Slice</th><th>Expected vs actual</th><th>Receipt</th></tr></thead>
        <tbody>
          {driftRows.map((row) => (
            <tr key={row.slice}><td>{row.slice}</td><td>{row.verdict}</td><td>{row.lastRun}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
