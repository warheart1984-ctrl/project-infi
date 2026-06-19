# CCS Core Schema v0.1

This contract defines the Core Continuity Substrate objects shared by AAIS,
CSLEIS, DZI-1, and DAR-Z handshakes.

Machine-readable schema: [`../../schemas/ccs_core_objects.v1.json`](../../schemas/ccs_core_objects.v1.json)

Test-ready exemplars live in [`../../fixtures/ccs/`](../../fixtures/ccs/), with
YAML and JSON examples for each core object.

End-to-end scenario bundle:
[`../../fixtures/ccs/river_bend_scenario.v1.json`](../../fixtures/ccs/river_bend_scenario.v1.json).

Executable harness:
[`../../tests/test_ccs_continuity_harness.py`](../../tests/test_ccs_continuity_harness.py).

## CCS.Identity.v1

Purpose: canonical identity spine for human, institutional, AI, and
land/resource entities.

Required fields:

- `id`: globally unique, non-recycled string.
- `kind`: one of `person`, `group`, `institution`, `agent`, `system`,
  `land_body`, `resource`, or `jurisdiction`.
- `display_name`: human-readable label.
- `lineage`: parent, family, organization, and jurisdiction context.
- `authority_surface`: roles, scopes, and constraints.
- `cultural_surface`: community, land relation, and sovereignty context.
- `technical_surface`: AAIS, provider, and runtime identifiers.
- `created_at`: timestamp.
- `updated_at`: timestamp.

Key invariants:

- One real-world entity maps to one `CCS.Identity` with multiple surfaces.
- `id` is never reused.

## CCS.Event.v1

Purpose: canonical record of what happened in continuity space.

Required fields:

- `id`: unique event ID.
- `kind`: one of `cognitive`, `governance`, `operational`, `ceremonial`,
  `ecological`, or `institutional`.
- `actors`: `CCS.Identity.id` references.
- `targets`: `CCS.Identity.id` or resource IDs.
- `time`: start, optional end, and optional timezone.
- `context`: AAIS, CSLEIS, or external context IDs.
- `law_surface`: AAIS, CSLEIS, or other law modules.
- `description`: event summary.
- `linked_evaluations`: `CCS.Evaluation.id` references.
- `linked_evidence`: `CCS.Evidence.id` references.
- `created_at`: timestamp.

Key invariants:

- Every continuity-relevant action is a `CCS.Event`.
- No orphaned events: at least one potential evaluation path must exist.

## CCS.Evaluation.v1

Purpose: canonical governance or assessment record over events.

Required fields:

- `id`: unique evaluation ID.
- `kind`: one of `technical`, `cultural`, `legal`, `ecological`,
  `institutional`, or `mixed`.
- `evaluator_id`: `CCS.Identity.id`.
- `evaluated_event_ids`: `CCS.Event.id` references.
- `law_surface`: AAIS, CSLEIS, or other law modules.
- `finding`: one of `compliant`, `non_compliant`, `conditional`, or
  `indeterminate`.
- `reasoning`: reasoning text or reference to the CCS Reasoning Contract fields.
- `uncertainty`: integer from 0-100.
- `risks`: risk notes.
- `recommended_actions`: governed next actions.
- `linked_evidence_ids`: `CCS.Evidence.id` references.
- `created_at`: timestamp.

Key invariants:

- No important event should remain permanently unevaluated.
- Evaluations must reference law surfaces and evidence.

## CCS.Evidence.v1

Purpose: canonical proof or trace object.

Required fields:

- `id`: unique evidence ID.
- `type`: one of `log`, `trace`, `transcript`, `recording`, `attestation`,
  `signature`, `hash_bundle`, `continuity_trace_fragment`,
  `governance_record`, or `ecological_impact`.
- `source`: source module or witness, such as `AAIS.Theta`, `DZI-1`,
  `CSLEIS.Council`, or `HumanWitness`.
- `integrity`: hash, optional signature, algorithm, and optional chain of
  custody.
- `linked_identity_ids`: `CCS.Identity.id` references.
- `linked_event_ids`: `CCS.Event.id` references.
- `law_surface`: AAIS, CSLEIS, or other law modules.
- `payload_ref`: pointer to storage, not raw payload.
- `created_at`: timestamp.

Key invariants:

- No evidence without integrity metadata.
- No evidence without at least one linked identity or event.
- No orphaned evidence.

## AAIS.CCS.Adapter.v1

Purpose: map AAIS runtime artifacts into CCS canonical objects and back.

Responsibilities:

- Register AAIS identities as `CCS.Identity` with `technical_surface`
  populated.
- Emit AAIS events as `CCS.Event` with `kind=cognitive` or
  `kind=operational`.
- Emit AAIS evaluations as `CCS.Evaluation` with `kind=technical`.
- Emit AAIS logs and traces as `CCS.Evidence` with `source=AAIS.*`.

Mappings:

- AAIS `operator_id`, `agent_id`, `provider_id`, and `workflow_id` become
  stable CCS identities.
- AAIS turn logs, tool calls, state transitions, and invariant checks become
  `CCS.Event` records.
- AAIS invariant results, law decisions, and drift outcomes become
  `CCS.Evaluation` records.
- AAIS Theta transforms, logs, traces, and signatures become `CCS.Evidence`
  records.

## CSLEIS.CCS.Adapter.v1

Purpose: map CSLEIS governance and cultural artifacts into CCS canonical
objects.

Responsibilities:

- Register CSLEIS people, councils, institutions, and land-bodies as
  `CCS.Identity`.
- Emit governance actions as `CCS.Event` records with governance,
  institutional, ecological, or ceremonial kind.
- Emit CSLEIS evaluations as `CCS.Evaluation` records with cultural, legal,
  ecological, institutional, or mixed kind.
- Emit DZI-1 continuity evidence as `CCS.Evidence`.

## CCS.ContinuityTrace.v1

Purpose: canonical, reproducible view over identities, events, evaluations, and
evidence for a continuity-relevant scenario.

Required fields:

- `id`: unique trace ID.
- `scope`: identity IDs, event IDs, and time window.
- `timeline`: event IDs with associated evaluations, evidence, and law
  surfaces.
- `continuity_summary`: identity, governance, cultural, ecological, long-term
  risk, and recommended-path summaries.
- `reproducibility_metadata`: input, law, and evidence signatures plus last
  verification timestamp.

Key invariants:

- A `CCS.ContinuityTrace` must be reconstructable from CCS objects alone.
- Same inputs plus same law plus same evidence produce the same
  `CCS.ContinuityTrace`.

## AAIS.Theta.CCSRegistration.v1

Purpose: register Theta as a governed transformation and evidence source in
CCS.

Theta registration object: `CCS.Transform.Theta.v1`.

Required fields:

- `id`: `AAIS.Theta.v1`.
- `kind`: `governed_transform`.
- `description`: deterministic encode/decode profile.
- `law_surface.aais_laws`: Theta-related law modules.
- `threat_model_ref`: pointer to Theta threat model doc.
- `test_coverage_ref`: pointer to test suite.
- `determinism_guarantee`: same-input, same-output statement.

Invariant: no Theta transform used in continuity analysis may exist outside CCS
as a registered `CCS.Evidence` object.
