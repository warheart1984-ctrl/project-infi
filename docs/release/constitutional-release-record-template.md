# Constitutional Release Record Template

This is the reusable Constitutional Release Record (CRR) template for repository releases.
Every future release should instantiate this record with the same core artifact set so the
release itself becomes a governed, replayable artifact instead of a bare Git tag.

## Release Identity

- Release record ID: `{{release_record_id}}`
- Release candidate version: `{{release_candidate_version}}`
- Promotion state: `{{promotion_state}}`
- Source commit: `{{source_commit}}`
- Release boundary commit: `{{release_boundary_commit}}`
- Steward: `{{steward_name}}`
- Assessment date: `{{assessment_date}}`

## Constitutional Decision

- Decision ID: `{{decision_id}}`
- Decision result: `{{decision_result}}`
- Promotion path: `{{from_state}}` -> `{{to_state}}`
- LRS reference: [Launch Readiness Specification](./launch-readiness-specification.md)

## Required Core Artifacts

| Artifact | Required content | Evidence location |
| --- | --- | --- |
| Release Readiness Record | Summary of the release decision and lifecycle state | `{{release_readiness_record_link}}` |
| Constitutional Requirements Matrix | Requirement-by-requirement readiness and evidence mapping | `{{requirements_matrix_link}}` |
| Companion Specification Traceability | Links to the companion specs referenced by the release | `{{companion_traceability_link}}` |
| Build/Test/Smoke Evidence | Build, test, and smoke execution evidence with commands and results | `{{verification_evidence_link}}` |
| Conformance Report | Requirement-level conformance status and gaps | `{{conformance_report_link}}` |
| Replay Reference | Replay artifacts or replayable references used in review | `{{replay_reference_link}}` |
| Constitutional Receipts | Signed receipt artifacts for the release bundle | `{{constitutional_receipts_link}}` |
| Stewardship Approval | Steward sign-off and any conditions attached to the approval | `{{stewardship_approval_link}}` |
| Release Manifest | Machine-readable artifact inventory for the release | `{{release_manifest_link}}` |
| Evidence Package | Checksums, signatures, receipts, logs, and proof surfaces | `{{evidence_package_link}}` |

## Release Readiness Record

### Summary

- Release boundary: `{{release_boundary}}`
- Scope: `{{release_scope}}`
- Release intent: `{{release_intent}}`
- Operational readiness notes: `{{operational_readiness_notes}}`

### Constitutional Requirements Matrix

| Requirement | State | Evidence |
| --- | --- | --- |
| `{{requirement_1}}` | `{{requirement_1_state}}` | `{{requirement_1_evidence}}` |
| `{{requirement_2}}` | `{{requirement_2_state}}` | `{{requirement_2_evidence}}` |
| `{{requirement_3}}` | `{{requirement_3_state}}` | `{{requirement_3_evidence}}` |

### Companion Specification Traceability

- `{{companion_spec_1}}`
- `{{companion_spec_2}}`
- `{{companion_spec_3}}`

### Build / Test / Smoke Evidence

| Surface | Command | Result | Evidence |
| --- | --- | --- | --- |
| `{{build_surface_1}}` | `{{build_command_1}}` | `{{build_result_1}}` | `{{build_evidence_1}}` |
| `{{test_surface_1}}` | `{{test_command_1}}` | `{{test_result_1}}` | `{{test_evidence_1}}` |
| `{{smoke_surface_1}}` | `{{smoke_command_1}}` | `{{smoke_result_1}}` | `{{smoke_evidence_1}}` |

### Conformance Report

- Conformance state: `{{conformance_state}}`
- Conformance gaps: `{{conformance_gaps}}`
- Conformance evidence: `{{conformance_evidence}}`

### Replay Reference

- Replay report ID: `{{replay_report_id}}`
- Replay scope: `{{replay_scope}}`
- Replay outcome: `{{replay_outcome}}`
- Replay evidence: `{{replay_evidence}}`

### Constitutional Receipts

- Receipt artifact: `{{receipt_artifact}}`
- Signature artifact: `{{signature_artifact}}`
- Verification result: `{{receipt_verification_result}}`

### Stewardship Approval

- Steward: `{{steward_name}}`
- Approval state: `{{stewardship_state}}`
- Approval notes: `{{stewardship_notes}}`
- Approval timestamp: `{{approval_timestamp}}`

### Release Manifest

- Manifest artifact: `{{release_manifest_artifact}}`
- Included packages: `{{included_packages}}`
- Included docs/specs: `{{included_docs}}`
- Bundle location: `{{bundle_location}}`

### Evidence Package

- Evidence bundle ID: `{{evidence_bundle_id}}`
- Checksums: `{{checksums_artifact}}`
- Receipts: `{{receipts_artifact}}`
- Logs: `{{logs_artifact}}`
- Replay references: `{{replay_artifacts}}`

## Known Limitations

- `{{known_limitations}}`

## Remaining Follow-Up Items

- `{{follow_up_items}}`

## Constitutional Requirements Satisfied

- Evidence before assertion
- Build evidence, test evidence, and smoke evidence are all recorded
- Conformance outcomes are explicit and queryable
- Replay evidence is linked and reproducible
- Stewardship approval is recorded separately from the merge decision
- Release manifest and evidence package are immutable references

## Release Lifecycle Notes

The release record is not a decorative checklist. It is the governed evidence record
used to advance the release through the Launch Readiness Specification lifecycle.
The formal promotion state `Approved Constitutional Merge` marks the point at which
the merge has been constitutionally approved, but the release may still need freeze,
packaging, verification, and publication before it is considered a completed release.

