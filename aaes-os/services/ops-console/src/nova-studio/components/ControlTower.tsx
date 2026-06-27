import type { OperatorContext } from '../state/studioState.js';

export function ControlTower({ operatorContext }: { operatorContext: OperatorContext }) {
  return (
    <div>
      <h3 style={{ marginTop: 0 }}>Control Tower</h3>
      <table>
        <tbody>
          <tr><th>Operator</th><td>{operatorContext.operatorId}</td></tr>
          <tr><th>Active slice</th><td>{operatorContext.activeSlice ?? 'none'}</td></tr>
          <tr><th>Checkpoint</th><td>{operatorContext.continuity.checkpoint}</td></tr>
          <tr><th>Substrate health</th><td>{operatorContext.substrateHealth.ledgerAvailable ? 'ledger-live' : 'ledger-offline'}</td></tr>
        </tbody>
      </table>
    </div>
  );
}
