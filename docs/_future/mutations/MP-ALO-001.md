# MP-ALO-001: adaptive_lane_organ — Lane mutation golden path

- gene: adaptive_lane_organ
- status: promoted
- backward_compatible: true
- mutation_kind: lane_dna
- operator_lanes_delta_ref: schemas/deltas/adaptive_lane_organ_MP-ALO-001.json
- schema_delta_ref: schemas/deltas/adaptive_lane_organ_MP-ALO-001.json
- fabric_genes: [adaptive_lane_organ]
- post_apply_wake: true
- post_apply_gate: alt6-governed-gate
- affected_subsystems: []

Adds a stable `audit_lane_mutation` capability to the existing `operator` lane without
changing `lane_id`, weight, or authority alignment. Documents the Alt-6.1 lane DNA
mutation path with post-apply wake and fabric re-validation.
