export function GovernanceDiagram() {
  return (
    <pre>
      {`GovernanceLoop -> InvariantEngine -> Ledger
                     -> FaultJournal -> TriCoreBus`}
    </pre>
  );
}
