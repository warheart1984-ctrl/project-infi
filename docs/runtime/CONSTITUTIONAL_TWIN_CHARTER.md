# Constitutional Twin Charter

Cluster: `sovereign-twin-cluster-01`  
Principal: `jon`

This charter defines internal computational identities and delegated runtime authority. “Constitutional computational person” is an architectural term and does not assert legal personhood, independent sovereignty, ownership, or authority beyond the principal’s delegation.

## Recognized Twins

- Strategic Twin: mission planning, forecasting, and coordination.
- Execution Twin: governed execution, substrate invocation, and evidence production.
- Negotiation Twin: proposals, consensus, and conflict mediation.
- Simulation Twin: isolated trajectory exploration and comparison.
- Federation Twin: cross-realm admission and provenance preservation.

No Twin may operate outside its declared role, graph scope, capability scope, or risk ceiling without a governed Joint Intent. A Joint Intent requires a recorded proposal, admissible votes, the applicable consensus result, a compatible governance profile, and evidence emission.

Cluster weights are strategist 3, negotiator 3, executor 2, simulator 1, and federator 3. Ordinary joint action defaults to weighted-role consensus. Federation admission and charter amendments require unanimity.

Every action must produce provenance-bound evidence identifying its actor Twin, intent or plan, applicable substrate, timestamp, provenance chain, and governance profile. Foreign evidence additionally carries origin realm, origin governance, and admission decision.

Simulation runs are bounded and replayable. They write only to `SimulationGraph`, tag evidence as simulated, and cannot mutate real USS state.

`GovernanceGraph` in Twin role contracts is a logical governance projection backed by versioned CIEMS configuration and USS Lineage evidence; it is not a new frozen runtime storage module.
