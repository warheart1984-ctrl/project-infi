import type { SkillzMcgeeCapability, SkillzMcgeeSliceState } from '../state/studioState.js';

export function CapabilityTable({
  capabilities,
  state,
}: {
  capabilities: SkillzMcgeeCapability[];
  state: Record<string, SkillzMcgeeSliceState>;
}) {
  return (
    <table>
      <thead><tr><th>Capability</th><th>Governed</th><th>Receipt</th><th>Last run</th></tr></thead>
      <tbody>
        {capabilities.map((capability) => (
          <tr key={capability.name}>
            <td title={capability.description}>{capability.name}</td>
            <td>{capability.governed ? 'yes' : 'no'}</td>
            <td>{capability.receiptRequired ? 'required' : 'optional'}</td>
            <td>{findLastRun(capability.name, state)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function findLastRun(capability: string, state: Record<string, SkillzMcgeeSliceState>): string {
  const direct = state[capability];
  if (direct) {
    return direct.last_run_id;
  }
  const llm = capability === 'ask_llm'
    ? Object.entries(state).find(([slice]) => slice.startsWith('llm:'))?.[1]
    : undefined;
  return llm?.last_run_id ?? 'none';
}
