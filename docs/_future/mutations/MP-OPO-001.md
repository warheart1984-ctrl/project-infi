# MP-OPO-001: operator_profile_organ — Profile invariant golden path

- gene: operator_profile_organ
- status: promoted
- backward_compatible: true
- mutation_kind: profile_invariant
- schema_delta_ref: schemas/deltas/operator_profile_organ_MP-OPO-001.json
- post_apply_gate: operator-profile-gate
- post_apply_snapshot_check: true
- fabric_genes: [operator_profile_organ]
- affected_subsystems: [operator_cognition_coherence_fabric]

Documents the Alt-7.2 profile-plane MP-X path with post-apply operator-profile-gate
and alt7 coherence re-validation via snapshot check.
