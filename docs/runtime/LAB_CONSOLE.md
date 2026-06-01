# Lab-Grade Coding Console

**Governed code experimentation bench** — Nova AI Factory patterns applied to repositories, tests, and tools.

| Field | Value |
|-------|-------|
| **Console ID** | `lab.v1` |
| **Version** | 1.0 |
| **Authority** | Meta Architect Lawbook · Stage 2 Copilot Doctrine (MA-13) |
| **Claim posture (v1)** | `asserted` — single-machine pytest + optional init smoke |

## What this is

The Lab Console gives coding agents a **bench**, not a raw shell:

- Isolated git **worktree** or **clone** per project under `.runtime/lab/<project_id>/workspace`
- **Governed instruments** only (`read_file`, `write_file`, `run_pytest`, …)
- **Session receipts** and **experiment folders** with diffs and tool logs
- Append-only **`lab_ledger.jsonl`**

## What this is not

- Unbounded shell access for agents
- In-place edits to the operator’s live checkout (workspace is isolated)
- HTTP agent API in v1 (Python `LabSession` only)

## Operator commands

```bash
python -m lab init --spec lab/specs/default.yaml --source .
python -m lab status --project nova-ai-factory
python -m lab session start --project nova-ai-factory --agent coding-agent-v1
python -m lab session end --project nova-ai-factory --session-id sess-2026-05-31-120000
python -m lab experiments list --project nova-ai-factory
python -m lab experiment show --project nova-ai-factory --exp exp-001-session-edit
python -m lab experiment revert --project nova-ai-factory --exp exp-001-session-edit --confirm
make lab-gate
```

Artifacts: `.runtime/lab/<project_id>/` — see plan layout in proof bundle.

## Agent API (v1)

```python
from lab.session import LabSession

with LabSession.open(project_id="nova-ai-factory", agent="coding-agent-v1") as sess:
    tools = sess.list_tools()
    ctx = sess.project_context()
    sess.invoke_tool("read_file", args={"path": "ai_factory/orchestrator.py"})
    sess.confirm("ai_factory/ledger.py")  # high-impact path
    sess.write_file("ai_factory/foo.py", content="# ...", experiment_tag="add-foo")
```

Agents must **not** call `subprocess` or write outside the workspace.

## Doctrine boundaries (MA-13)

| Failure class | Lab guard |
|---------------|-----------|
| Class I — Usurpation | Manifest/spine not writable by agents; receipts have no binding goals |
| Class II — Distortion | Explicit paths; high-impact writes need `confirm()` |
| Class III — Leakage | Path jail, forbidden commands, default no network |

## v1 exclusions

- FastAPI routes
- Cross-machine replay (debt: INV-9)

## v1.1 (asserted)

- **Lab ↔ Forge bridge:** instruments `forge_patch_plan`, `create_patch_review` via `lab/forge_bridge.py`
- Session receipts include `patch_review_ids` and `stage2_metrics`
- Forge / Cursor SDK HTTP integration remains future work

## Proof

See [`docs/proof/lab/LAB_V1_PROOF_BUNDLE.md`](../proof/lab/LAB_V1_PROOF_BUNDLE.md).

## Related docs

- [AI_FACTORY.md](./AI_FACTORY.md)
- [STAGE2_COPILOT_DOCTRINE.md](./STAGE2_COPILOT_DOCTRINE.md)
- [NOVA_CAPABILITY_INVENTORY.md](./NOVA_CAPABILITY_INVENTORY.md)

## Windows note

Git worktree paths should be absolute. Cross-machine worktree proof remains **debt** until a Windows + Linux replay bundle exists.
