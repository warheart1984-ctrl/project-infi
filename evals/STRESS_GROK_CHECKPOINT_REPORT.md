# Grok build + planning checkpoint stress report

**Trace IDs:** `grok-stress-r2` (harness), pytest run `2026-06-04`  
**Harness:** `evals/stress_grok_checkpoint.py`  
**Scope:** Imagine Grok render path (v1.24 frontier + Story Forge adapter), planning checkpoint verification, HTTP tool-call parsing (xAI chat lane).

---

## Executive summary

| Area | Result |
|------|--------|
| Unit: `imagine_grok` + capability bridge (no API import) | **PASS** (3/3 core tests) |
| Unit: planning → execution checkpoint loop | **PASS** |
| Unit: governed pipeline tool_call isolation | **PASS** |
| API import (`import src.api`) | **FAIL** — genome boot blocks Flask |
| Checkpoint verifier on “good” copy | **PARTIAL** — brittle token overlap |
| Tool-call parser | **PASS** with silent degradation on bad JSON |
| End-to-end mock Grok chain (harness) | **PASS** after valid PNG b64 (see harness fix) |

---

## Failure mode 1 — Genome boot blocks API / Grok HTTP tests

**Symptom:** `TestImagineGrokAPI` fails on `import src.api` with `GenomeValidationError: genome boot validation failed`.

**Reproduce:**

```powershell
cd E:\project-infi
python -c "from src.governance_organs import Alt4Runtime; Alt4Runtime.boot_validate()"
```

**Root cause:** 26 registry errors; 5 genomes missing `activation` / `lineage` / `mutation` blocks, plus asymmetric parent/child links (e.g. `aris_standalone_service`, `coding_organs_stack`, `otem_execution_substrate`).

**Sample errors (first 5):**

```
aris_standalone_service.genome.v1.json: missing top-level keys: ['activation', 'mutation']
coding_organs_stack.genome.v1.json: missing top-level keys: ['activation', 'mutation']
dreamspace_organ.genome.v1.json: missing top-level keys: ['activation', 'lineage', 'mutation']
...
```

**Mitigation for local stress:** `AAIS_GENOME_BOOT=warn` before importing API (not used in CI by default).

**Impact:** Any stress path that loads `src.api` (Grok `/grok-render`, `/keys-status` integration tests) cannot run until genomes are repaired or boot mode relaxed.

---

## Failure mode 2 — Checkpoint verifier false negatives (token overlap)

**Symptom:** Body that mentions Focus, Postgres, alignment still gets `partial` with `checkpoint_missed:Decision or arc next action stated when`.

**Reproduce:**

```powershell
cd E:\project-infi
$env:STRESS_TRACE_ID="checkpoint-only"
python evals/stress_grok_checkpoint.py
# Inspect JSONL line: scenario checkpoint.pass_like
```

**Mechanism:** `_verify_execution` in `src/cog_runtime/execution.py` only checks **first two** checkpoints and requires **word-token intersection** between checkpoint phrase and reply body. Phrasing like “Decision or arc next action” rarely appears verbatim in operator-style answers.

**Risk:** Execution runtime may over-trigger rollback/recovery on otherwise acceptable replies.

**Trace excerpt:**

```json
{"scenario": "checkpoint.pass_like", "status": "partial", "gaps": ["checkpoint_missed:Decision or arc next action stated when "]}
```

---

## Failure mode 3 — Tool-call parser silent degradation

**Symptom:** Malformed tool `arguments` JSON does not fail parsing; raw string is wrapped.

**Reproduce:** harness scenario `tool_parse.malformed_args` or:

```python
from src.providers.http_chat_provider import parse_tool_calls
parse_tool_calls({"tool_calls": [{"id": "t1", "function": {"name": "grep", "arguments": "{not json"}}]}, provider_id="xai")
# -> ToolResult with arguments={"raw": "{not json"}
```

**Risk:** Downstream tool executors receive `arguments.raw` instead of structured fields; multi-step tool chains can noop or mis-route without a hard error.

---

## Failure mode 4 — Dual Grok model surfaces (chat vs imagine)

**Multi-file chain traced:**

1. `src/providers/frontier_catalog.py` — chat default `grok-2-latest`
2. `external/story_forge/.../grok_adapter.py` — image `grok-imagine-image`, analysis `grok-4.20-reasoning`
3. `src/imagine_grok.py` — persists artifact model from adapter result

**Risk:** Operators selecting provider `xai` / alias `grok` for **chat** are not on the same model family as **Imagine Grok render**; stress tests must not conflate the two paths.

---

## Failure mode 5 — Host env leaks xAI keys into “no key” scenarios

**Symptom:** First harness run reported `grok.keys.none` with `configured: true` while keys were popped in-process — keys remained in parent shell.

**Reproduce:** Run harness without clearing `XAI_API_KEY` / `STORY_FORGE_XAI_API_KEY` in the shell.

**Mitigation:** Clear env in the invoking shell (as in `grok-stress-r2` run) or run inside isolated CI job.

---

## Pass paths (reproducible)

### Grok render unit chain (no API)

```powershell
cd E:\project-infi
python -m pytest tests/test_imagine_grok.py::TestImagineGrok -q
```

### Capability bridge keys gate

```powershell
python -m pytest tests/test_capability_bridge_alt3.py::TestCapabilityBridgeAlt3::test_imagine_grok_render_blocked_without_keys -q
```

### Full harness JSONL trace

```powershell
Remove-Item Env:XAI_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:STORY_FORGE_XAI_API_KEY -ErrorAction SilentlyContinue
$env:STRESS_TRACE_ID="grok-stress-r2"
python evals/stress_grok_checkpoint.py | Tee-Object evals/traces/grok-stress-r2.jsonl
```

### Planning checkpoint + execution (companion turn)

```powershell
python -m pytest tests/test_cortex_arcs.py::TestCortexArcs::test_companion_turn_runs_reflection_planning_execution_loop -q
```

---

## Multi-file reasoning map (Grok render)

```
POST /api/jarvis/imagine/grok-render  (src/api.py)
  -> run_imagine_generator_capability(action=grok_render)
       (src/capabilities/imagine_generator.py)
  -> grok_render_pattern / render_grok_for_pattern
       (src/imagine_grok.py)
  -> GrokImageAdapter.execute("generate")
       (external/story_forge/.../grok_adapter.py)
  -> artifact grok_render.json under pattern_dir
```

Capability bridge parallel path: `CapabilityServiceBridge._handle_imagine_grok_render` → same capability runner; maps `KeysRequired` → tool status `blocked`.

---

## Recommended next stress waves

1. Fix or gate the 5 broken genomes → unblock API-level Grok tests.
2. Add checkpoint verifier fixtures for paraphrased compliance (reduce token-overlap false negatives).
3. Fail or metric `parse_tool_calls` when `arguments` contains only `raw`.
4. Optional `STRESS_GROK_LIVE=1` live xAI smoke (not run in this pass).
