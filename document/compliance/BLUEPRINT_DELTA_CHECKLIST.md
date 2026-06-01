# Blueprint Delta Checklist (Binding-Law Pass)

This checklist was derived from binding blueprint sources and executed in order.

## 1) Blueprint Sources Discovered

Primary sources used for this pass:

1. `document/blueprints/PROJECT_BLUEPRINTS_MASTER.md`
2. `document/law/REPO_LAWBOOK.md`
3. `docs/contracts/*.md` (law and doctrine contracts referenced by `document/law/REPO_LAWBOOK.md`)
4. Runtime enforcement files referenced by the lawbook:
   - `src/project_infi_law.py`
   - `src/module_governance.py`
   - `src/phase_gate.py`
   - `src/verification_gate.py`
   - `src/immune_protocol.py`
   - `src/memory_board_enforcer.py`
   - `src/governance_layer.py`
   - `src/project_infi_state_machine.py`

## 2) Ordered Action Checklist

### Completed

1. [x] Add explicit blueprint-named ARIS cognitive upgrade module alias.
   - Evidence: `aris/evolving_ai/aris/aris_cognitive_upgrade.py`
2. [x] Add a focused alias verification test.
   - Evidence: `aris/tests/test_aris_cognitive_upgrade_alias.py`
3. [x] Add `AudioPlan.json` source-of-truth artifact for BeatBox/Speakers lane.
   - Evidence: `external/beatbox_speakers/AudioPlan.json`

### Verified

1. [x] ARIS cognitive-upgrade tests pass on supported runtime:
   - `py -3.12 -m unittest tests.test_aris_cognitive_upgrade_alias tests.test_aris_cognitive_upgrade`
   - Result: `Ran 6 tests ... OK`
2. [x] `AudioPlan.json` validates as JSON.
   - Check: `python -c "import json, pathlib; json.loads(pathlib.Path('external/beatbox_speakers/AudioPlan.json').read_text(encoding='utf-8')); print('AudioPlan.json: OK')"`
   - Result: `AudioPlan.json: OK`

## 3) Outstanding Items Requiring User Judgment (Blockers)

1. [ ] **Canonical runtime lane is ambiguous across duplicated trees.**
   - Evidence: parallel structures exist in root and mirrored trees (`Project-Infinity-main`, `Aris--main`), including duplicated contracts and runtime code.
   - Why blocked: applying “binding law” updates to one tree can diverge the others; applying to all trees risks broad, non-minimal edits.
   - Decision required:
     - Option A: treat root (`E:/project-infi`) as sole canonical lane and ignore mirrors.
     - Option B: keep mirrors synchronized as binding surfaces.

2. [ ] **`POST /aais/run` contract mapping is underspecified versus current runtime API.**
   - Blueprint contract: `persona`, `session_id`, `message` with persona set `{tiny_nova, small_nova, nova}`.
   - Current runtime surface: session-scoped chat route with persona handling in `/api/chat/sessions/<session_id>/message`, and persona naming includes `super_nova` rather than plain `nova`.
   - Why blocked: there is no unambiguous law-defined mapping for:
     - `nova` -> `super_nova` (or a distinct persona),
     - behavior when `session_id` does not exist (create vs fail),
     - expected response envelope shape for `/aais/run`.
   - Decision required:
     - Option A: implement `/aais/run` adapter mapping `nova -> super_nova`, auto-create missing sessions, return simplified envelope.
     - Option B: implement strict contract (`nova` distinct, no auto-create), fail on missing sessions.
     - Option C: amend blueprint contract to match existing `/api/chat/sessions/<session_id>/message` surface.

3. [ ] **Blueprint memory namespace paths are specified as filesystem directories, current implementation is metadata/session based.**
   - Blueprint paths: `memory/tiny_nova/`, `memory/small_nova/`, `memory/nova/`.
   - Current implementation stores companion memory in session metadata keys (e.g., `tiny_nova_memories`, `small_nova_memories`, `super_nova_memories`) in `src/conversation_memory.py`.
   - Why blocked: unclear whether law requires physical on-disk namespace directories, virtual namespaces, or both.
   - Decision required:
     - Option A: enforce on-disk namespace directories + persistence layer.
     - Option B: treat current in-memory namespaces as compliant and update docs to clarify.

