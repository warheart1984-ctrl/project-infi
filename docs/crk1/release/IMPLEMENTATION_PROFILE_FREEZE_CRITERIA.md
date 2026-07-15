# Implementation Profile Freeze Criteria

**Release family:** CRK-1 companion specification  
**Status:** Frozen  
**Depends on:** CIS Core v1.0 and Implementation Profiles  
**Stewardship:** CIS release maintainers  
**Constitutional sections:** 1-6  
**Informative sections:** 7

---

## 1. Purpose

This specification defines the objective criteria required to promote any `profile-*` implementation profile from `Draft` to `Frozen`.

The criteria exist to keep implementation profiles as active adaptation surfaces until they have enough evidence, traceability, and governed release history to justify a frozen companion baseline.

## 2. Scope

These criteria apply to all implementation profile artifacts, including:

- `profile-government`
- `profile-healthcare`
- `profile-finance`
- `profile-research`
- `profile-education`
- `profile-infrastructure`
- `profile-regenerative-intelligence`

## 3. Freeze criteria

A profile MAY be promoted to `Frozen` only when all of the following are complete:

1. The profile scope and boundary are explicit.
2. The profile inherits CIS Core terminology without redefining constitutional terms.
3. The profile maps to the CIS requirements it adapts.
4. The profile has traceability links to the Standards Traceability Matrix and governing hierarchy artifacts.
5. The profile-specific evidence bundle is complete.
6. Build verification, test verification, and runtime smoke verification pass for the profile slice.
7. Conformance validation passes against the frozen constitutional baseline.
8. Launch Readiness records the promotion as evidence-based rather than subjective.
9. The Constitutional Release Record, Merge Readiness Record, and Evidence Package are complete.
10. No unresolved constitutional ambiguity, scope conflict, or traceability gap remains.
11. A formal freeze notice has been prepared and added to the release surface.

## 4. Non-frozen rule

If any criterion is missing, the profile SHALL remain `Draft`.

Draft status in this context means the profile is still an active adaptation surface and has not yet earned frozen companion-baseline status.

## 5. Freeze decision

When all criteria are satisfied, the profile freeze decision SHALL be recorded in the governed registry and release index.

The freeze decision SHALL identify:

- the profile artifact
- the evidence bundle
- the traceability references
- the verification results
- the release record
- the freeze notice

## 6. Change control

Any future change to these criteria must proceed through the governed constitutional change process.

No local implementation preference may waive a required criterion or mark a profile frozen without the recorded evidence.

## 7. Informative note

This specification is intentionally strict so the profile family can graduate one artifact at a time without blurring the line between adaptation surfaces and frozen companion baselines.
