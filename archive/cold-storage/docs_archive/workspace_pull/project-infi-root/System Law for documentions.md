# STORY FORGE / AAIS — PROJECT LAW

## Core Law

No change is considered complete unless it is:

1. Implemented
2. Verified
3. Documented

All three are required. Missing any one = incomplete work.

---

## Documentation Requirements

For every mission, Codex MUST:

### 1. Create or update a mission report

File format:
`docs/reports/MISSION_<ID>_REPORT.md`

This report must include:

* Mission ID
* Scope
* Files changed
* What changed
* Why (system/law impact)
* Verification steps and results
* Remaining gaps
* Next recommended mission

---

### 2. Update the global build log

File:
`docs/STORY_FORGE_BUILD_LOG.md`

Append:

* Date
* Mission ID
* Summary of result
* Verification status
* Known risks
* System impact

---

### 3. Update relevant system docs (if needed)

If the mission changes system behavior, Codex MUST update:

* world pack docs
* runtime docs
* module docs
* architecture notes

---

## Enforcement Rule

A mission is NOT complete if:

* tests pass but no documentation exists
* code compiles but no report exists
* behavior changes but docs are not updated

---

## Folder Structure

docs/
reports/
STORY_FORGE_BUILD_LOG.md
architecture/
world_packs/

---

## Codex Execution Rule

Every mission must end with:

1. Code complete
2. Tests passing
3. Documentation written
4. Build log updated

If any step is missing → mission is incomplete.

---

## Design Doctrine

We do not rely on memory.
We do not rely on guessing.
We do not rely on “we’ll document later.”

The system must always explain itself.

---

## Final Rule

If it is not written down,
it does not exist.
