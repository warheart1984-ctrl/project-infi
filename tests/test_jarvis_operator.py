"""Tests for persistent Jarvis memory and workspace tools."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import uuid

from src.jarvis_memory_board import MemoryController, default_memory_slots
from src.jarvis_operator import JarvisMemoryStore, JarvisOperator, WorkspaceTools
from src.module_governance import module_governance
from src.phase_gate import reset_registry


RUNTIME_ROOT = Path.cwd() / ".runtime" / "pytest-temp"
RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)


def _make_runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}-{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=False)
    return target


class TestJarvisMemoryStore(unittest.TestCase):
    """Verify persistent memory storage behavior."""

    def test_memory_round_trip_and_relevance(self):
        """Memories should persist, search, and delete cleanly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = JarvisMemoryStore(memory_path=Path(tmp_dir) / "jarvis_memory.json")

            first = store.add_memory(
                "User wants Jarvis to stay private and local.",
                tags=["privacy", "jarvis"],
                pinned=True,
            )
            second = store.add_memory(
                "AAIS-main is the active local project.",
                tags=["project"],
            )

            self.assertEqual(len(store.list_memories()), 2)
            relevant = store.get_relevant_memories("private local jarvis", limit=2)
            self.assertEqual(relevant[0]["id"], first["id"])
            self.assertEqual(store.list_memories(query="active project", limit=1)[0]["id"], second["id"])

            self.assertTrue(store.delete_memory(first["id"]))
            self.assertEqual(len(store.list_memories()), 1)

    def test_relevant_memory_lookup_does_not_mutate_store_state(self):
        """Relevant-memory reads should stay side-effect free."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = JarvisMemoryStore(memory_path=Path(tmp_dir) / "jarvis_memory.json")
            created = store.add_memory(
                "Jarvis should keep governed memory reads side-effect free.",
                tags=["governance", "memory"],
            )

            relevant = store.get_relevant_memories("governed side-effect free", limit=1)

            self.assertEqual(relevant[0]["id"], created["id"])
            refreshed = store.get_memory(created["id"])
            self.assertIsNotNone(refreshed)
            self.assertIsNone(refreshed.get("last_used_at"))

    def test_memory_update_supports_tags_and_pinning(self):
        """Memories should support later categorization and pin updates."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = JarvisMemoryStore(memory_path=Path(tmp_dir) / "jarvis_memory.json")
            created = store.add_memory("Jarvis should remember coding context.")

            updated = store.update_memory(
                created["id"],
                tags=["coding", "workspace"],
                pinned=True,
            )

            self.assertIsNotNone(updated)
            self.assertEqual(updated["category"], "coding")
            self.assertEqual(updated["priority"], 80)
            self.assertEqual(updated["tags"], ["coding", "workspace"])
            self.assertTrue(updated["pinned"])

            rewritten = store.update_memory(
                created["id"],
                text="Jarvis should prefer the canonical memory bank editor.",
                category="operator",
                priority=92,
                active=False,
            )

            self.assertEqual(rewritten["content"], "Jarvis should prefer the canonical memory bank editor.")
            self.assertEqual(rewritten["text"], "Jarvis should prefer the canonical memory bank editor.")
            self.assertEqual(rewritten["category"], "operator")
            self.assertEqual(rewritten["priority"], 92)
            self.assertFalse(rewritten["active"])

    def test_override_memories_are_high_priority_and_filterable(self):
        """Override memories should stay active, high-priority, and queryable by category."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = JarvisMemoryStore(memory_path=Path(tmp_dir) / "jarvis_memory.json")
            store.add_memory(
                "Jarvis should default to the active project memory.",
                category="project",
                priority=40,
            )
            override = store.add_override(
                "Use the canonical Memory Bank page for editing long-term memories.",
                category="override",
            )

            self.assertTrue(override["override"])
            self.assertTrue(override["active"])
            self.assertGreaterEqual(override["priority"], 95)
            filtered = store.list_memories(category="override", active=True, limit=4)
            self.assertEqual([memory["id"] for memory in filtered], [override["id"]])

    def test_merge_memories_rejects_inactive_or_cross_scope_sources(self):
        """Canonical live memories should not absorb archived or non-live source notes."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = JarvisMemoryStore(memory_path=Path(tmp_dir) / "jarvis_memory.json")
            target = store.add_memory(
                "Keep operator truth anchored to the live AAIS workspace.",
                category="operator",
                state_class="live",
                truth_status="canonical",
            )
            demo_source = store.add_memory(
                "Demo note that should never merge into live operator truth.",
                category="operator",
                state_class="demo",
                truth_status="derived",
            )
            archived_source = store.add_memory(
                "Archived note that should not merge forward.",
                category="operator",
                state_class="live",
                truth_status="derived",
            )
            store.update_memory(archived_source["id"], active=False)

            with self.assertRaisesRegex(ValueError, "state class"):
                store.merge_memories(target_id=target["id"], source_ids=[demo_source["id"]])

            with self.assertRaisesRegex(ValueError, "inactive"):
                store.merge_memories(target_id=target["id"], source_ids=[archived_source["id"]])

    def test_memory_board_snapshot_starts_with_capability_board(self):
        """The persistent memory store should expose the linked capability-aware board."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = JarvisMemoryStore(memory_path=Path(tmp_dir) / "jarvis_memory.json")

            snapshot = store.get_memory_board_snapshot()

            self.assertEqual(snapshot["max_slots"], 10)
            self.assertEqual(snapshot["active_slots"], 6)
            self.assertEqual(snapshot["installed_slots"], 6)
            self.assertEqual(snapshot["reserved_slots"], 4)
            self.assertEqual(snapshot["board"]["board_label"], "Capability Adapter Board")
            self.assertEqual(snapshot["slots"][0]["module"]["module_id"], "capability_foundation_v2")
            self.assertEqual(snapshot["slots"][5]["module"]["module_id"], "capability_routing_preferences_v2")
            self.assertEqual(snapshot["slots"][6]["module"], None)

    def test_memory_board_snapshot_tracks_governed_memory_events(self):
        """Persistent memory writes, merges, and archive actions should leave board governance evidence."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = JarvisMemoryStore(memory_path=Path(tmp_dir) / "jarvis_memory.json")

            target = store.add_memory(
                "Keep operator truth anchored to the active AAIS workspace.",
                category="operator",
                why="Live operator truth.",
            )
            source = store.add_memory(
                "The active AAIS workspace remains the operator source of truth.",
                category="project",
                why="Duplicate operator note.",
            )
            archived = store.add_memory(
                "Old prompt-lab operator note.",
                category="operator",
                why="Archive seed.",
            )
            store.merge_memories(target_id=target["id"], source_ids=[source["id"]])
            store.archive_memory(archived["id"], reason="No longer current.")

            snapshot = store.get_memory_board_snapshot(truth_scope="all")
            governance = snapshot["governance"]

            self.assertGreaterEqual(governance["event_count"], 4)
            self.assertGreaterEqual(governance["action_counts"].get("write", 0), 3)
            self.assertGreaterEqual(governance["action_counts"].get("merge", 0), 1)
            self.assertGreaterEqual(governance["action_counts"].get("archive", 0), 1)
            self.assertIn(
                governance["last_event"]["action"],
                {"archive", "merge", "write"},
            )

    def test_protected_install_and_swap_record_board_events(self):
        """Board module installs and swaps should only enter through the protected controller path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = JarvisMemoryStore(memory_path=Path(tmp_dir) / "jarvis_memory.json")
            store.memory_board = MemoryController(default_memory_slots())

            installed = store.install_memory_module(
                "slot_02",
                {
                    "module_id": "operator_memory_v1",
                    "module_version": "1.0.0",
                    "module_class": "operational",
                    "supported_slot": "slot_02",
                    "capacity": 128,
                    "trust_class": "verified",
                    "retrieval_priority": 60,
                    "retention_policy": "persistent",
                    "eviction_policy": "age_and_rank",
                },
            )
            swapped = store.swap_memory_module(
                "slot_02",
                {
                    "module_id": "operator_memory_v2",
                    "module_version": "2.0.0",
                    "module_class": "operational",
                    "supported_slot": "slot_02",
                    "capacity": 256,
                    "trust_class": "verified",
                    "retrieval_priority": 80,
                    "retention_policy": "persistent",
                    "eviction_policy": "age_and_rank",
                },
                migration_records=[
                    {
                        "record_id": "memory-1",
                        "slot_id": "slot_02",
                        "slot_role": "operational",
                        "trust_class": "verified",
                        "text": "Verified operator truth.",
                    }
                ],
            )

            snapshot = store.get_memory_board_snapshot(truth_scope="all")
            governance = snapshot["governance"]

            self.assertEqual(installed["event"]["action"], "protected_install")
            self.assertEqual(swapped["event"]["action"], "protected_swap")
            self.assertEqual(governance["action_counts"].get("protected_install", 0), 1)
            self.assertEqual(governance["action_counts"].get("protected_swap", 0), 1)
            self.assertEqual(
                snapshot["slots"][1]["module"]["module_id"],
                "operator_memory_v2",
            )


class TestWorkspaceTools(unittest.TestCase):
    """Verify workspace listing, searching, and previewing."""

    def test_workspace_tools_cover_projects_search_and_read(self):
        """Workspace tools should list projects, search text, and preview files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_dir = root / "AAIS-main"
            project_dir.mkdir()
            (project_dir / "README.md").write_text(
                "# AAIS-main\nA private local Jarvis project.\n",
                encoding="utf-8",
            )
            (project_dir / "notes.txt").write_text(
                "Jarvis should search the workspace and remember project notes.",
                encoding="utf-8",
            )

            tools = WorkspaceTools(workspace_root=root)
            projects = tools.list_projects()
            self.assertEqual(projects[0]["name"], "AAIS-main")
            self.assertIn("Jarvis project", projects[0]["summary"])

            search = tools.search("remember project", limit=5)
            self.assertGreaterEqual(len(search["results"]), 1)
            self.assertEqual(search["results"][0]["project"], "AAIS-main")

            preview = tools.read_file("AAIS-main/notes.txt", max_chars=200)
            self.assertIn("remember project notes", preview["content"])

    def test_read_file_uses_query_centered_excerpt_for_code_context(self):
        """Query-aware previews should center on the relevant code instead of the file header."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            project_dir = root / "AAIS-main"
            (project_dir / "src").mkdir(parents=True)
            (project_dir / "src" / "api.py").write_text(
                "\"\"\"Flask API for multi-modal AI system.\"\"\"\n"
                "from flask import Flask\n\n"
                "@app.route('/api/chat/sessions/<session_id>/message')\n"
                "def chat_message(session_id):\n"
                "    return {'status': 'ok'}\n",
                encoding="utf-8",
            )

            tools = WorkspaceTools(workspace_root=root)
            preview = tools.read_file(
                "AAIS-main/src/api.py",
                max_chars=220,
                query="debug the chat message route in api.py",
            )

            self.assertIn("chat_message", preview["content"])
            self.assertIn("@app.route", preview["content"])


class TestJarvisOperator(unittest.TestCase):
    """Verify direct chat commands for memory and workspace actions."""

    def setUp(self):
        self.original_module_governance_runtime_dir = module_governance.runtime_dir
        self.module_governance_runtime_dir = _make_runtime_dir("jarvis-operator-governance")
        module_governance.configure_runtime_dir(self.module_governance_runtime_dir)
        module_governance.reset()
        reset_registry()

    def tearDown(self):
        module_governance.configure_runtime_dir(self.original_module_governance_runtime_dir)
        module_governance.reset()
        reset_registry()
        shutil.rmtree(self.module_governance_runtime_dir, ignore_errors=True)

    def test_apply_memory_expiry_review_prefers_explicit_target_ids(self):
        """Explicit target ids should archive only the governed stale blocker selection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            original_runtime_dir = module_governance.runtime_dir
            try:
                module_governance.configure_runtime_dir(root / "module-governance")
                module_governance.reset()
                reset_registry()
                operator = JarvisOperator(memory_path=root / "jarvis_memory.json", workspace_root=root)

                blocker = operator.memory_enforcer.add_memory(
                    "Pytest is failing on the verification lane.",
                    category="operator",
                    runtime_context="operator_runtime",
                )
                sibling = operator.memory_enforcer.add_memory(
                    "Another blocker is still open on the docs lane.",
                    category="operator",
                    runtime_context="operator_runtime",
                )

                result = operator._apply_memory_expiry_review(
                    {
                        "reason": "stale_blocker",
                        "message": "Latest tests passed, so the targeted blocker can expire.",
                        "target_ids": [blocker["id"]],
                    }
                )

                self.assertEqual(result["targeting_mode"], "explicit_id")
                self.assertEqual(result["archived_ids"], [blocker["id"]])
                self.assertEqual(result["skipped_target_ids"], [])
                self.assertFalse(
                    operator.memory_enforcer.get_memory(blocker["id"], runtime_context="operator_runtime")["active"]
                )
                self.assertTrue(
                    operator.memory_enforcer.get_memory(sibling["id"], runtime_context="operator_runtime")["active"]
                )
            finally:
                module_governance.configure_runtime_dir(original_runtime_dir)
                module_governance.reset()
                reset_registry()

    def test_apply_memory_expiry_review_heuristic_fallback_stays_narrow(self):
        """Heuristic fallback should ignore unrelated notes that only mention the word red."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            original_runtime_dir = module_governance.runtime_dir
            try:
                module_governance.configure_runtime_dir(root / "module-governance")
                module_governance.reset()
                reset_registry()
                operator = JarvisOperator(memory_path=root / "jarvis_memory.json", workspace_root=root)

                blocker = operator.memory_enforcer.add_memory(
                    "The pytest lane is red and failing in CI.",
                    category="operator",
                    runtime_context="operator_runtime",
                )
                design_note = operator.memory_enforcer.add_memory(
                    "Red interface accents are part of the design system.",
                    category="operator",
                    runtime_context="operator_runtime",
                )

                result = operator._apply_memory_expiry_review(
                    {
                        "reason": "stale_blocker",
                        "message": "Latest tests passed, so stale blocker state should expire.",
                    }
                )

                self.assertEqual(result["targeting_mode"], "heuristic_fallback")
                self.assertEqual(result["archived_ids"], [blocker["id"]])
                self.assertFalse(
                    operator.memory_enforcer.get_memory(blocker["id"], runtime_context="operator_runtime")["active"]
                )
                self.assertTrue(
                    operator.memory_enforcer.get_memory(design_note["id"], runtime_context="operator_runtime")["active"]
                )
            finally:
                module_governance.configure_runtime_dir(original_runtime_dir)
                module_governance.reset()
                reset_registry()

    def test_record_action_lifecycle_prefers_explicit_stale_blocker_targets_for_passing_pytest(self):
        """Passing pytest lifecycle events should seed explicit stale-blocker ids before MemorySmith review."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            original_runtime_dir = module_governance.runtime_dir
            try:
                module_governance.configure_runtime_dir(root / "module-governance")
                module_governance.reset()
                reset_registry()
                operator = JarvisOperator(memory_path=root / "jarvis_memory.json", workspace_root=root)

                blocker = operator.memory_enforcer.add_memory(
                    "The pytest lane is red and failing in CI.",
                    category="operator",
                    runtime_context="operator_runtime",
                )
                design_note = operator.memory_enforcer.add_memory(
                    "Red interface accents are part of the design system.",
                    category="operator",
                    runtime_context="operator_runtime",
                )

                operator.record_action_lifecycle(
                    "session-explicit-expiry",
                    {
                        "action_id": "run_pytest",
                        "action_instance_id": "run-pytest-explicit-expiry",
                        "stage": "executed",
                        "result_status": "completed",
                    },
                )

                review_payload = operator.memory_smith._load_payload()
                review = review_payload["reviews"][-1]
                expired_action = review["expired_actions"][0]
                self.assertEqual(expired_action["targeting_mode"], "explicit_id")
                self.assertEqual(expired_action["requested_target_ids"], [blocker["id"]])
                self.assertEqual(expired_action["archived_ids"], [blocker["id"]])
                self.assertFalse(
                    operator.memory_enforcer.get_memory(blocker["id"], runtime_context="operator_runtime")["active"]
                )
                self.assertTrue(
                    operator.memory_enforcer.get_memory(design_note["id"], runtime_context="operator_runtime")["active"]
                )
            finally:
                module_governance.configure_runtime_dir(original_runtime_dir)
                module_governance.reset()
                reset_registry()

    def test_handle_command_supports_memory_and_workspace_requests(self):
        """Jarvis operator commands should work without model generation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / "Ui jarvis").mkdir()
            (workspace / "Ui jarvis" / "index.html").write_text(
                "<html><body>voice orb prototype</body></html>",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            remember_result = operator.handle_command("remember that voice mode matters most")
            self.assertEqual(remember_result["tool_result"]["type"], "memory_add")

            memory_result = operator.handle_command("show my memories")
            self.assertIn("voice mode matters most", memory_result["response"])

            search_result = operator.handle_command("search workspace for voice orb")
            self.assertEqual(search_result["tool_result"]["type"], "workspace_search")
            self.assertIn("Ui jarvis", search_result["response"])
            self.assertIn("index.html", search_result["response"])

    def test_handle_command_returns_structured_block_when_memory_gateway_is_quarantined(self):
        """Direct memory-list commands should return a governed block instead of raising."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            operator.memory_enforcer.list_memories(runtime_context="operator_runtime")
            operator.memory_enforcer.module_governance_controller.report_runtime_signal(
                operator.memory_enforcer.component_id,
                signal_type="unauthorized_memory_creation",
                reason="Simulated bypass containment.",
            )

            result = operator.handle_command("show my memories")

            self.assertEqual(result["tool_result"]["type"], "memory_blocked")
            self.assertEqual(result["tool_result"]["status"], "blocked")
            self.assertIn("Memory reads are blocked because the gateway is not admitted.", result["response"])
            self.assertEqual(result["tool_result"]["memory_enforcer"]["decision"], "BLOCK")
            self.assertEqual(
                result["tool_result"]["memory_enforcer"]["module_governance"]["status"],
                "quarantined",
            )

    def test_build_forge_context_uses_workspace_previews_and_infers_language(self):
        """Forge context should stay task-local while preserving the most relevant code files."""
        root = _make_runtime_dir("jarvis-forge-context")
        try:
            project_dir = root / "AAIS-main"
            (project_dir / "src").mkdir(parents=True)
            (project_dir / "src" / "api.py").write_text(
                "def chat_message():\n    return {'status': 'ok'}\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=root,
            )
            workspace_context = operator.build_workspace_context(
                "Help me refactor chat_message in api.py.",
                reason="forge_request",
                auto_attached=False,
                force=True,
            )

            forge_context = operator.build_forge_context(
                "Refactor the chat route for clarity.",
                workspace_context=workspace_context,
                constraints=["no breaking changes"],
                style={"quotes": "single"},
            )

            self.assertEqual(forge_context["goal"], "Refactor the chat route for clarity.")
            self.assertEqual(forge_context["constraints"]["language"], "python")
            self.assertEqual(forge_context["constraints"]["requirements"], ["no breaking changes"])
            self.assertEqual(forge_context["constraints"]["style"]["quotes"], "single")
            self.assertEqual(forge_context["files"][0]["path"], "AAIS-main/src/api.py")
            self.assertIn("chat_message", forge_context["files"][0]["content"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_build_forge_context_applies_repo_manager_scope_controls_as_hard_limits(self):
        """Repo manager scope controls should clamp the attached Forge file slice before handoff."""
        operator = JarvisOperator()
        workspace_context = {
            "project_profile": {"languages": ["python"]},
            "files": [
                {
                    "relative_path": "AAIS-main/src/api.py",
                    "content": "def route():\n    return {'ok': True}\n",
                    "truncated": False,
                },
                {
                    "relative_path": "AAIS-main/src/deep/worker.py",
                    "content": "def worker():\n    return 'deep'\n",
                    "truncated": False,
                },
                {
                    "relative_path": "AAIS-main/frontend/src/App.jsx",
                    "content": "export default function App() { return null; }\n",
                    "truncated": False,
                },
            ],
            "results": [
                {"relative_path": "AAIS-main/src/api.py", "project": "AAIS-main"},
                {"relative_path": "AAIS-main/src/deep/worker.py", "project": "AAIS-main"},
                {"relative_path": "AAIS-main/frontend/src/App.jsx", "project": "AAIS-main"},
            ],
        }

        forge_context = operator.build_forge_context(
            "Inspect the backend route seam.",
            workspace_context=workspace_context,
            target_scope="AAIS-main/src",
            focus_files=["AAIS-main/src/api.py"],
            excluded_files=["AAIS-main/frontend/*"],
            change_intent="review_only",
            max_change_budget="one route seam",
            validation_target="route parity",
            operation_mode="inspect_only",
            max_files_to_inspect=2,
            max_directory_depth=2,
            file_path_allowlist=["AAIS-main/src/*"],
            explicit_denylist=["AAIS-main/src/deep/*"],
            no_execution_without_handoff=True,
        )

        self.assertEqual([item["path"] for item in forge_context["files"]], ["AAIS-main/src/api.py"])
        self.assertEqual(forge_context["operation_mode"], "inspect_only")
        self.assertEqual(forge_context["validation_target"], "route parity")
        self.assertEqual(forge_context["max_files_to_inspect"], 2)
        self.assertEqual(forge_context["max_directory_depth"], 2)
        self.assertEqual(forge_context["file_path_allowlist"], ["AAIS-main/src/*"])
        self.assertEqual(forge_context["explicit_denylist"], ["AAIS-main/src/deep/*"])
        self.assertTrue(forge_context["no_execution_without_handoff"])

    def test_request_forge_code_wraps_result_with_auto_approve_flag(self):
        """Forge requests should return the contractor payload plus the policy decision Jarvis needs."""
        operator = JarvisOperator()

        with patch(
            "src.jarvis_operator.forge_client.request",
            return_value={
                "ok": True,
                "task_id": "forge-task-operator",
                "kind": "generate_diff",
                "law_enforcement": {"contract_version": "aais.forge.ul.v1"},
                "ul_snapshot": {"count": 5},
                "result": {
                    "diffs": [
                        {
                            "path": "src/api.py",
                            "unified_diff": "diff --git a/src/api.py b/src/api.py",
                        }
                    ],
                },
            },
        ) as mock_run:
            payload = operator.request_forge_code(
                "Refactor the API route.",
                workspace_context={
                    "project_profile": {"languages": ["python"]},
                    "files": [
                        {
                            "relative_path": "AAIS-main/src/api.py",
                            "content": "def chat_message():\n    return {'status': 'ok'}\n",
                            "truncated": False,
                        }
                    ],
                },
            )

        self.assertFalse(payload["auto_approve"])
        self.assertEqual(payload["kind"], "generate_diff")
        self.assertTrue(payload["result"]["ok"])
        self.assertEqual(payload["forge_context"]["constraints"]["language"], "python")
        self.assertEqual(payload["law_enforcement"]["contract_version"], "aais.forge.ul.v1")
        self.assertEqual(payload["ul_snapshot"]["count"], 5)
        mock_run.assert_called_once()

    def test_request_evolution_job_wraps_result_with_hall_tracking(self):
        """EvolveEngine requests should preserve the bounded lane contract Jarvis needs."""
        operator = JarvisOperator()

        with patch(
            "src.jarvis_operator.evolve_client.evolve",
            return_value={
                "ok": True,
                "job_id": "evolve-job-operator",
                "task": "Improve this candidate.",
                "result": {
                    "best_score": 0.92,
                    "best_genome": {"candidate": "winner", "candidate_field": "program"},
                    "best_program": "winner",
                    "generations_run": 2,
                    "evaluations": 6,
                    "history": [],
                    "hall_of_fame_count": 2,
                    "hall_of_shame_count": 1,
                },
            },
        ) as mock_evolve:
            payload = operator.request_evolution_job(
                "Improve this candidate.",
                config={"seed_candidates": ["winner"]},
                constraints={"max_generations": 2},
                jarvis_run_id="jarvis-run-1",
            )

        self.assertEqual(payload["job_id"], "evolve-job-operator")
        self.assertEqual(payload["task"], "Improve this candidate.")
        self.assertEqual(payload["evaluation"]["mode"], "forge_eval")
        self.assertEqual(payload["result"]["result"]["hall_of_fame_count"], 2)
        self.assertEqual(payload["result"]["result"]["hall_of_shame_count"], 1)
        mock_evolve.assert_called_once()

    def test_handle_command_rejects_governed_memory_store_with_structured_reason(self):
        """Chat-command memory stores should reject governed truth claims without mutating canonical memory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            operator = JarvisOperator(memory_path=root / "jarvis_memory.json", workspace_root=root / "workspace")

            result = operator.handle_command("Jarvis, store this: the workspace is read-only.")

            self.assertEqual(result["tool_result"]["type"], "memory_rejection")
            decision = result["tool_result"]["memory_rejection"]
            self.assertFalse(decision["stored"])
            self.assertEqual(decision["reason"], "canonical_protection")
            self.assertEqual(
                len(operator.memory_enforcer.list_memories(runtime_context="operator_runtime")),
                0,
            )

    def test_handle_command_supports_otem_without_model_or_side_effects(self):
        """Explicit OTEM prompts should return a deterministic operator-task plan."""
        operator = JarvisOperator()
        before_memory_count = len(
            operator.memory_enforcer.list_memories(runtime_context="operator_runtime")
        )
        before_run_count = len(operator.list_runs(limit=200, truth_scope="all"))

        result = operator.handle_command("Before anything else, use OTEM to break this migration down.")

        self.assertEqual(result["tool_result"]["type"], "otem")
        otem = result["tool_result"]["otem"]
        self.assertEqual(result["tool_result"]["status"], "complete")
        self.assertTrue(3 <= len(otem["plan"]) <= 7)
        self.assertTrue(all(step["status"] == "pending" for step in otem["plan"]))
        self.assertTrue(otem["session_scoped"])
        self.assertFalse(otem["persistent"])
        self.assertEqual(otem["restated_task"], "Handle this operator task: break this migration down.")
        self.assertEqual(
            len(operator.memory_enforcer.list_memories(runtime_context="operator_runtime")),
            before_memory_count,
        )
        self.assertEqual(len(operator.list_runs(limit=200, truth_scope="all")), before_run_count)

    def test_build_otem_turn_result_adds_workflow_handoff_without_creating_runs(self):
        """OTEM v3 should propose a workflow handoff without creating workflow or run state."""
        operator = JarvisOperator()
        before_run_count = len(operator.list_runs(limit=200, truth_scope="all"))

        result = operator.build_otem_turn_result(
            "Use OTEM to design a daily brief workflow that emails the operator every morning.",
        )

        self.assertEqual(result["status"], "complete")
        self.assertIsNotNone(result["workflow_handoff"])
        self.assertEqual(result["workflow_handoff"]["workflow_template_id"], "daily-ai-brief")
        self.assertGreaterEqual(result["execution_awareness"]["workflow_catalog"]["count"], 1)
        self.assertEqual(len(operator.list_runs(limit=200, truth_scope="all")), before_run_count)

    def test_build_otem_turn_result_keeps_session_continuity_and_tool_cold(self):
        """OTEM v4-v5 should keep a session task thread and only suggest tools as proposals."""
        operator = JarvisOperator()
        initial = operator.build_otem_turn_result(
            "Use OTEM to break this backend failure into steps and decide whether pytest is the right verification move.",
            session_id="session-otem",
        )

        followup = operator.build_otem_turn_result(
            "Use OTEM to focus on step 2.",
            session_id="session-otem",
            prior_state=initial,
        )

        self.assertEqual(initial["status"], "active")
        self.assertEqual(followup["status"], "active")
        self.assertEqual(
            followup["restated_task"],
            initial["restated_task"],
        )
        self.assertEqual(followup["session_context"]["focus_step_index"], 2)
        self.assertTrue(
            any(suggestion["tool_id"] == "run_pytest" for suggestion in initial["tool_awareness"]["suggestions"])
        )
        self.assertTrue(all(suggestion["proposal_only"] for suggestion in initial["tool_awareness"]["suggestions"]))

    def test_build_otem_turn_result_keeps_signal_language_out_of_plan(self):
        """Mixed signal language should survive as metadata instead of contaminating the OTEM plan."""
        operator = JarvisOperator()

        result = operator.build_otem_turn_result(
            "Use OTEM to identify the blocking seam in the response pipeline near OTEM, "
            "but I mostly feel the block is close and the confidence is high.",
        )

        self.assertEqual(
            result["restated_task"],
            "Handle this operator task: identify the blocking seam in the response pipeline near OTEM.",
        )
        self.assertEqual(
            result["task_clauses"],
            ["identify the blocking seam in the response pipeline near OTEM"],
        )
        self.assertEqual(
            result["signal_clauses"],
            ["I mostly feel the block is close and the confidence is high"],
        )
        self.assertEqual(result["operator_signals"]["proximity"], "near OTEM")
        self.assertEqual(result["operator_signals"]["confidence"], "high")
        self.assertFalse(
            any("confidence is high" in step["description"].lower() for step in result["plan"]),
        )

    def test_handle_command_supports_structured_spatial_reason_tool(self):
        """Structured spatial tool envelopes should run without model generation."""
        operator = JarvisOperator()

        build_request = json.dumps(
            {
                "tool": "spatial_reason",
                "args": {
                    "mode": "build",
                    "space_id": "throne_chamber",
                    "nodes": [
                        {"id": "balcony", "type": "elevated", "tags": ["cover"]},
                        {"id": "throne", "type": "seat_of_power"},
                        {"id": "pillar", "type": "obstacle", "tags": ["stone"]},
                        {"id": "assassin", "type": "entity"},
                    ],
                    "edges": [
                        {"from": "balcony", "to": "pillar", "weight": 4, "obstacle": True, "name": "stone pillar"},
                        {"from": "pillar", "to": "throne", "weight": 6},
                        {"from": "balcony", "to": "throne", "weight": 12},
                    ],
                },
            }
        )
        visibility_request = json.dumps(
            {
                "tool": "spatial_reason",
                "args": {
                    "mode": "visibility",
                    "space_id": "throne_chamber",
                    "from": "assassin",
                    "to": "throne",
                    "line_of_sight": True,
                },
            }
        )

        build_result = operator.handle_command(build_request)
        visibility_result = operator.handle_command(visibility_request)

        self.assertEqual(build_result["tool_result"]["type"], "spatial_reason")
        self.assertEqual(build_result["tool_result"]["status"], "completed")
        self.assertEqual(build_result["tool_result"]["result"]["node_count"], 4)
        self.assertEqual(visibility_result["tool_result"]["type"], "spatial_reason")
        self.assertEqual(visibility_result["tool_result"]["mode"], "visibility")
        self.assertFalse(visibility_result["tool_result"]["result"]["visible"])
        self.assertIn("blocked", visibility_result["response"].lower())

    def test_handle_command_supports_mystic_reading_requests(self):
        """Mystic reading requests should bypass model generation and return structured output."""
        operator = JarvisOperator()

        natural_language = operator.handle_command(
            "Give me a mystic reading: I feel stuck and nothing is moving.",
        )
        structured = operator.handle_command(
            json.dumps(
                {
                    "tool": "mystic_reading",
                    "args": {
                        "input": "I have an idea that could change everything, but I need direction.",
                    },
                }
            )
        )

        self.assertEqual(natural_language["tool_result"]["type"], "mystic_reading")
        self.assertEqual(natural_language["tool_result"]["result"]["state"], "lost")
        self.assertIn("Next action", natural_language["response"])

        self.assertEqual(structured["tool_result"]["type"], "mystic_reading")
        self.assertEqual(structured["tool_result"]["result"]["state"], "awakening")
        self.assertEqual(structured["tool_result"]["status"], "completed")

    def test_handle_command_routes_explicit_forge_requests_through_contractor(self):
        """Explicit Forge phrasing should bypass internal build eagerness and use the contractor lane."""
        operator = JarvisOperator()
        workspace_context = {
            "project_scope": "AAIS-main",
            "results": [{"relative_path": "AAIS-main/src/api.py", "project": "AAIS-main"}],
            "files": [
                {
                    "relative_path": "AAIS-main/src/api.py",
                    "content": "def chat_message():\n    return {'status': 'ok'}\n",
                    "truncated": False,
                }
            ],
        }
        forge_payload = {
            "task_id": "forge-direct-tool",
            "task": "refactor the API route",
            "kind": "generate_diff",
            "result": {
                "ok": True,
                "kind": "generate_diff",
                "result": {
                    "diffs": [
                        {
                            "path": "src/api.py",
                            "unified_diff": "diff --git a/src/api.py b/src/api.py",
                        }
                    ]
                },
            },
            "auto_approve": False,
            "forge_context": {
                "goal": "refactor the API route",
                "files": [{"path": "AAIS-main/src/api.py", "truncated": False}],
                "constraints": {"language": "python", "max_output_chars": 20000},
            },
        }
        forge_summary = {
            "goal": "refactor the API route",
            "file_count": 1,
            "files": [{"path": "AAIS-main/src/api.py", "truncated": False}],
            "constraints": {"language": "python", "max_output_chars": 20000},
        }

        with patch.object(operator, "build_workspace_context", return_value=workspace_context) as mock_workspace:
            with patch.object(operator, "request_forge_code", return_value=forge_payload) as mock_request:
                with patch.object(operator, "summarize_forge_context", return_value=forge_summary):
                    result = operator.handle_command("Use Forge for this: refactor the API route.")

        self.assertEqual(result["tool_result"]["type"], "forge_result")
        self.assertEqual(result["tool_result"]["forge"]["matched_trigger"], "use forge for this")
        self.assertEqual(result["tool_result"]["forge"]["task"], "refactor the API route")
        self.assertTrue(result["tool_result"]["forge"]["lane_guardrail"]["allowed"])
        self.assertEqual(result["tool_result"]["forge"]["lane_guardrail"]["active_lane"], "JARVIS")
        self.assertIn("Forge handled the request", result["response"])
        mock_workspace.assert_called_once()
        mock_request.assert_called_once_with(
            "refactor the API route",
            workspace_context=workspace_context,
        )

    def test_handle_command_blocks_explicit_forge_requests_in_tiny_lane(self):
        """Tiny Nova should not be allowed to hand the turn directly to the Forge execution lane."""
        operator = JarvisOperator()

        result = operator.handle_command(
            "Use Forge for this: refactor the API route.",
            response_mode="tiny",
        )

        self.assertEqual(result["tool_result"]["type"], "lane_guardrail")
        self.assertEqual(result["tool_result"]["status"], "blocked")
        self.assertEqual(
            result["tool_result"]["lane_guardrail"]["reason"],
            "RULE_TINY_NOVA_STAYS_CONVERSATIONAL",
        )
        self.assertEqual(result["tool_result"]["lane_guardrail"]["requested_lane"], "FORGE")
        self.assertIn("Tiny Nova stays in a conversational lane", result["response"])

    def test_handle_command_blocks_explicit_forge_requests_in_small_lane(self):
        """Small Nova should not be allowed to hand the turn directly to the Forge execution lane."""
        operator = JarvisOperator()

        result = operator.handle_command(
            "Use Forge for this: refactor the API route.",
            response_mode="small",
        )

        self.assertEqual(result["tool_result"]["type"], "lane_guardrail")
        self.assertEqual(result["tool_result"]["status"], "blocked")
        self.assertEqual(
            result["tool_result"]["lane_guardrail"]["reason"],
            "RULE_SMALL_NOVA_STAYS_CONVERSATIONAL",
        )
        self.assertEqual(result["tool_result"]["lane_guardrail"]["requested_lane"], "FORGE")
        self.assertIn("Small Nova stays in a conversational lane", result["response"])

    def test_handle_command_blocks_explicit_forge_requests_in_super_lane(self):
        """Super Nova should not be allowed to hand the turn directly to the Forge execution lane."""
        operator = JarvisOperator()

        result = operator.handle_command(
            "Use Forge for this: refactor the API route.",
            response_mode="governed_full",
        )

        self.assertEqual(result["tool_result"]["type"], "lane_guardrail")
        self.assertEqual(result["tool_result"]["status"], "blocked")
        self.assertEqual(
            result["tool_result"]["lane_guardrail"]["reason"],
            "RULE_SUPER_NOVA_STAYS_CONVERSATIONAL",
        )
        self.assertEqual(result["tool_result"]["lane_guardrail"]["requested_lane"], "FORGE")
        self.assertIn("Super Nova stays in a conversational lane", result["response"])

    def test_handle_command_does_not_treat_forge_questions_as_execution_requests(self):
        """Forge routing should stay narrow and ignore descriptive questions."""
        operator = JarvisOperator()

        result = operator.handle_command("What is Forge and when should we use it?")

        self.assertIsNone(result)

    def test_build_workspace_context_for_coding_request(self):
        """Coding prompts should auto-attach useful workspace context."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            project = workspace / "AAIS-main"
            project.mkdir()
            (project / "src").mkdir()
            (project / "src" / "api.py").write_text(
                "def chat_message():\n    return {'status': 'ok'}\n",
                encoding="utf-8",
            )
            (project / "README.md").write_text(
                "# AAIS-main\nPrivate Jarvis workspace.\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            context = operator.build_workspace_context(
                "Help me debug the chat_message flow in api.py for Jarvis.",
            )

            self.assertIsNotNone(context)
            self.assertEqual(context["reason"], "coding_request")
            self.assertGreaterEqual(len(context["results"]), 1)
            self.assertIn("api.py", context["prompt_block"])

    def test_build_workspace_context_skips_current_docs_questions(self):
        """Fresh docs/news questions should not auto-attach local code context."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            project = workspace / "AAIS-main"
            project.mkdir()
            (project / "src").mkdir()
            (project / "src" / "api.py").write_text(
                "def chat_message():\n    return {'status': 'ok'}\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            context = operator.build_workspace_context(
                "Compare the latest OpenAI API docs and tell me what changed recently.",
            )

            self.assertIsNone(context)

    def test_build_workspace_context_skips_general_idea_planning_prompts(self):
        """Broad planning prompts should not auto-attach source files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            project = workspace / "AAIS-main"
            project.mkdir()
            (project / "src").mkdir()
            (project / "src" / "api.py").write_text(
                "def chat_message():\n    return {'status': 'ok'}\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            context = operator.build_workspace_context(
                "I have a crazy idea for Jarvis. What should I build first?",
            )

            self.assertIsNone(context)

    def test_build_workspace_context_can_be_forced_for_debug_mode(self):
        """Debug-style modes should be able to force workspace grounding even on terse error prompts."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            project = workspace / "AAIS-main"
            (project / "src").mkdir(parents=True)
            (project / "src" / "api.py").write_text(
                "def chat_message():\n    raise RuntimeError('boom')\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            context = operator.build_workspace_context(
                "Traceback exploded in the chat route.",
                reason="debug_request",
                auto_attached=False,
                force=True,
                query_hint="traceback chat route api error",
            )

            self.assertIsNotNone(context)
            self.assertEqual(context["reason"], "debug_request")
            self.assertIn("forced for this mode", context["prompt_block"])
            self.assertTrue(context["results"])

    def test_build_workspace_context_handles_package_relative_imports(self):
        """Repo-map inspection should not crash on `from . import ...` package imports."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            project = workspace / "AAIS-main"
            (project / "src").mkdir(parents=True)
            (project / "src" / "__init__.py").write_text(
                "from . import api\n",
                encoding="utf-8",
            )
            (project / "src" / "api.py").write_text(
                "def chat_message():\n    return {'status': 'ok'}\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            context = operator.build_workspace_context(
                "Help me debug the chat_message flow in api.py for Jarvis.",
            )

            self.assertIsNotNone(context)
            self.assertIsNotNone(context["repo_map"])
            self.assertIn("AAIS-main/src/api.py", context["repo_map"]["focus_paths"])

    def test_workspace_search_prefers_aais_main_when_matches_are_ambiguous(self):
        """AAIS-main should outrank reference projects when both match the same query."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()

            primary = workspace / "AAIS-main"
            primary.mkdir()
            (primary / "src").mkdir()
            (primary / "src" / "api.py").write_text(
                "def chat_message():\n    return {'status': 'ok'}\n",
                encoding="utf-8",
            )

            reference = workspace / "jarvis"
            reference.mkdir()
            (reference / "api.py").write_text(
                "def chat_message():\n    return {'status': 'reference'}\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            results = operator.workspace_tools.search("chat_message api", limit=5)["results"]
            self.assertEqual(results[0]["project"], "AAIS-main")

    def test_workspace_search_prioritizes_exact_aais_main_file_for_api_prompts(self):
        """Exact file mentions should lift the AAIS-main source file above sibling repo matches."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()

            primary = workspace / "AAIS-main"
            (primary / "src").mkdir(parents=True)
            (primary / "src" / "api.py").write_text(
                "@app.route('/api/chat/sessions/<session_id>/message')\n"
                "def chat_message(session_id):\n"
                "    return {'status': 'ok'}\n",
                encoding="utf-8",
            )

            reference = workspace / "jarvis"
            (reference / "services" / "apps" / "api" / "app" / "routes").mkdir(parents=True)
            (reference / "services" / "apps" / "api" / "app" / "routes" / "chat.py").write_text(
                "def message_route():\n"
                "    return {'status': 'reference'}\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            results = operator.workspace_tools.search(
                "api.py debug chat message route api",
                limit=5,
            )["results"]

            self.assertEqual(results[0]["project"], "AAIS-main")
            self.assertTrue(results[0]["relative_path"].replace("/", "\\").endswith("AAIS-main\\src\\api.py"))

    def test_build_workspace_context_scopes_to_primary_project_when_matches_exist(self):
        """Auto-attached coding context should stay inside AAIS-main before falling back wider."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()

            primary = workspace / "AAIS-main"
            (primary / "src").mkdir(parents=True)
            (primary / "src" / "api.py").write_text(
                "@app.route('/api/chat/sessions/<session_id>/message')\n"
                "def chat_message(session_id):\n"
                "    return {'status': 'ok'}\n",
                encoding="utf-8",
            )

            reference = workspace / "jarvis"
            (reference / "services" / "apps" / "api" / "app" / "routes").mkdir(parents=True)
            (reference / "services" / "apps" / "api" / "app" / "routes" / "chat.py").write_text(
                "def message_route():\n"
                "    return {'status': 'reference'}\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            context = operator.build_workspace_context(
                "Help me debug the chat message route in api.py",
            )

            self.assertIsNotNone(context)
            self.assertEqual(context["project_scope"], "AAIS-main")
            self.assertTrue(context["results"])
            self.assertTrue(all(result["project"] == "AAIS-main" for result in context["results"]))
            self.assertTrue(
                context["results"][0]["relative_path"].replace("/", "\\").endswith("AAIS-main\\src\\api.py")
            )

    def test_build_browser_verification_links_route_to_workspace_and_action(self):
        """Browser verification should map a rendered route back to local files and a safe next step."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()

            frontend_project = workspace / "AAIS-main"
            (frontend_project / "frontend" / "src" / "pages").mkdir(parents=True)
            (frontend_project / "frontend" / "src" / "pages" / "ImageAnalyzer.jsx").write_text(
                "export default function ImageAnalyzer() {\n"
                "  return <main><h1>Image Analyzer</h1><button>Analyze Image</button></main>;\n"
                "}\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            verification = operator.build_browser_verification(
                {
                    "url": "http://localhost:3000/image-analyzer",
                    "path": "/image-analyzer",
                    "title": "AAIS | Image Analyzer",
                    "headings": ["Image Analyzer"],
                    "buttons": ["Analyze Image", "Upload Screenshot"],
                    "alerts": [],
                    "main_text": "Image Analyzer Upload Screenshot Analyze Image",
                    "route_markers": ["image analyzer"],
                    "dom_counts": {"headings": 1, "buttons": 2, "links": 1, "forms": 1, "inputs": 1},
                    "viewport": {"width": 1440, "height": 900},
                    "capture_mode": "iframe",
                    "load_state": "loaded",
                },
                expectation="The image analyzer screen should load and show the upload flow.",
            )

            self.assertEqual(verification["status"], "healthy")
            self.assertEqual(verification["target_path"], "/image-analyzer")
            self.assertEqual(verification["surface_type"], "ui_screenshot")
            self.assertEqual(verification["suggested_action"]["id"], "build_frontend")
            self.assertIsNotNone(verification["workspace_context"])
            self.assertTrue(
                verification["workspace_context"]["results"][0]["relative_path"].replace("/", "\\").endswith(
                    "AAIS-main\\frontend\\src\\pages\\ImageAnalyzer.jsx"
                )
            )
            self.assertEqual(verification["expectation_fit"]["status"], "aligned")

    def test_browser_verification_prefers_frontend_route_files_over_mobile_matches(self):
        """Live browser routes should bias toward web frontend files when both web and mobile screens match."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()

            project = workspace / "AAIS-main"
            (project / "frontend" / "src" / "pages").mkdir(parents=True)
            (project / "mobile" / "src" / "screens").mkdir(parents=True)
            (project / "tests").mkdir()

            (project / "frontend" / "src" / "pages" / "ImageAnalyzer.jsx").write_text(
                "export default function ImageAnalyzer() {\n"
                "  return <main><h1>Image Analyzer</h1><button>Upload Screenshot</button></main>;\n"
                "}\n",
                encoding="utf-8",
            )
            (project / "mobile" / "src" / "screens" / "ImageAnalyzerScreen.tsx").write_text(
                "export const ImageAnalyzerScreen = () => <Text>Upload Screenshot</Text>;\n",
                encoding="utf-8",
            )
            (project / "tests" / "test_image_analyzer.py").write_text(
                "def test_image_analyzer():\n    assert True\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            verification = operator.build_browser_verification(
                {
                    "url": "http://localhost:3000/image-analyzer",
                    "path": "/image-analyzer",
                    "title": "AAIS | Image Analyzer",
                    "headings": ["Image Analyzer"],
                    "buttons": ["Analyze Image", "Upload Screenshot"],
                    "alerts": [],
                    "main_text": "Image Analyzer Upload Screenshot Analyze Image",
                    "route_markers": ["image analyzer"],
                    "dom_counts": {"headings": 1, "buttons": 2, "links": 1, "forms": 1, "inputs": 1},
                    "viewport": {"width": 1440, "height": 900},
                    "capture_mode": "iframe",
                    "load_state": "loaded",
                },
                expectation="The image analyzer route should show the upload flow.",
            )

            self.assertTrue(
                verification["workspace_context"]["results"][0]["relative_path"].replace("/", "\\").endswith(
                    "AAIS-main\\frontend\\src\\pages\\ImageAnalyzer.jsx"
                )
            )
            self.assertEqual(verification["suggested_action"]["id"], "build_frontend")

    def test_browser_verification_can_infer_route_expectation_when_manual_text_is_missing(self):
        """Known AAIS routes should still get a meaningful expected UI signature without a manual prompt."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()

            project = workspace / "AAIS-main"
            (project / "frontend" / "src" / "pages").mkdir(parents=True)
            (project / "frontend" / "src" / "pages" / "Settings.jsx").write_text(
                "export default function Settings() {\n"
                "  return <main><h1>Settings</h1><button>Save Settings</button><button>Reset to Default</button></main>;\n"
                "}\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            verification = operator.build_browser_verification(
                {
                    "url": "http://localhost:3000/settings",
                    "path": "/settings",
                    "title": "AAIS | Settings",
                    "headings": ["Settings"],
                    "buttons": ["Save Settings", "Reset to Default"],
                    "alerts": [],
                    "main_text": "Settings API URL Default Model Save Settings Reset to Default",
                    "route_markers": ["settings"],
                    "dom_counts": {"headings": 1, "buttons": 2, "links": 0, "forms": 1, "inputs": 3},
                    "viewport": {"width": 1440, "height": 900},
                    "capture_mode": "iframe",
                    "load_state": "loaded",
                },
            )

            self.assertEqual(verification["expectation_source"], "auto")
            self.assertEqual(verification["route_expectation"]["route_key"], "settings")
            self.assertEqual(verification["route_expectation"]["fit"]["status"], "aligned")
            self.assertEqual(verification["expectation_fit"]["status"], "aligned")
            self.assertTrue(
                verification["workspace_context"]["results"][0]["relative_path"].replace("/", "\\").endswith(
                    "AAIS-main\\frontend\\src\\pages\\Settings.jsx"
                )
            )
            self.assertEqual(verification["suggested_action"]["id"], "build_frontend")

    def test_workspace_search_ignores_training_outputs(self):
        """Generated training artifacts should not surface as workspace evidence."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()

            project = workspace / "AAIS-main"
            (project / "src").mkdir(parents=True)
            (project / "training" / "out" / "checkpoint-1").mkdir(parents=True)
            (project / "src" / "jarvis_operator.py").write_text(
                "def build_workspace_context():\n    return 'source'\n",
                encoding="utf-8",
            )
            (project / "training" / "out" / "checkpoint-1" / "README.md").write_text(
                "Model Card for generated checkpoint\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            results = operator.workspace_tools.search("build workspace context", limit=10)["results"]
            paths = [result["relative_path"] for result in results]

            self.assertTrue(any(path.endswith("src\\jarvis_operator.py") for path in paths))
            self.assertFalse(any("training\\out" in path for path in paths))

    def test_build_visual_operator_assist_maps_code_screenshot_to_workspace_and_pytest(self):
        """Screenshot-derived debugging clues should map back to AAIS-main and a safe test action."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()

            project = workspace / "AAIS-main"
            (project / "src").mkdir(parents=True)
            (project / "src" / "api.py").write_text(
                "@app.route('/api/chat/sessions/<session_id>/message')\n"
                "def chat_message(session_id):\n"
                "    raise RuntimeError('Traceback from screenshot')\n",
                encoding="utf-8",
            )

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            assist = operator.build_visual_operator_assist(
                {
                    "description": "Code screenshot with traceback output.",
                    "top_matches": [{"label": "screenshot", "score": 0.61}],
                    "ocr": {
                        "status": "available",
                        "text_preview": "Traceback in api.py line 2 chat_message RuntimeError",
                    },
                    "ui": {
                        "status": "available",
                        "surface_type": "code_screenshot",
                        "code_language": "python",
                        "readable_targets": ["api.py", "chat_message", "Traceback"],
                        "layout_clues": ["editor", "stack trace"],
                    },
                },
                operator_context="debug the chat route in api.py",
            )

            self.assertEqual(assist["suggested_action"]["id"], "run_pytest")
            self.assertIn("python_traceback", assist["debug_signals"])
            self.assertIsNotNone(assist["workspace_context"])
            self.assertTrue(assist["workspace_context"]["results"])
            self.assertTrue(
                assist["workspace_context"]["results"][0]["relative_path"].replace("/", "\\").endswith(
                    "AAIS-main\\src\\api.py"
                )
            )

    def test_action_commands_require_approval_and_can_execute(self):
        """Natural language action requests should propose actions before execution."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            request_result = operator.handle_command("run tests for this project")
            self.assertEqual(request_result["tool_result"]["type"], "action_request")
            self.assertEqual(request_result["tool_result"]["action"]["id"], "run_pytest")

            with patch.object(operator.action_runner, "execute_action", return_value={
                "action": operator.action_runner.get_action("run_pytest"),
                "status": "completed",
                "exit_code": 0,
                "stdout": "27 passed",
                "stderr": "",
                "summary": "27 passed",
                "ran_at": "2026-04-01T00:00:00+00:00",
            }):
                execute_result = operator.handle_command(
                    "approve action run_pytest",
                    allow_approval_commands=True,
                )

            self.assertEqual(execute_result["tool_result"]["type"], "action_result")
            self.assertIn("Run Pytest finished", execute_result["response"])

    def test_operator_mode_can_suggest_actions_without_exact_command_phrases(self):
        """Operator mode should lean toward safe local actions even when the request is phrased loosely."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workspace = root / "workspace"
            workspace.mkdir()

            operator = JarvisOperator(
                memory_path=root / "jarvis_memory.json",
                workspace_root=workspace,
            )

            request_result = operator.handle_command(
                "Can you verify the repo before we keep going?",
                response_mode="operator",
            )

            self.assertEqual(request_result["tool_result"]["type"], "action_request")
            self.assertEqual(request_result["tool_result"]["action"]["id"], "git_status")

    def test_execute_action_wraps_runtime_actions_in_project_infi_law(self):
        """Shared runtime actions should emit one governed law contract and one structured event log."""
        operator = JarvisOperator()
        mocked_result = {
            "action": dict(operator.action_runner.get_action("run_pytest") or {"id": "run_pytest", "label": "Run Pytest"}),
            "status": "completed",
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "summary": "364 passed, 6 subtests passed.",
            "ran_at": "2026-04-14T00:00:00+00:00",
        }

        with patch.object(operator.action_runner, "execute_action", return_value=mocked_result):
            payload = operator.execute_action("run_pytest", session_id="session-law")

        tool_result = payload["tool_result"]
        self.assertEqual(tool_result["law_enforcement"]["contract_version"], "aais.project_infi.ul.v1")
        self.assertGreaterEqual(tool_result["ul_snapshot"]["count"], 1)
        self.assertEqual(tool_result["law_event_log"]["event_type"], "runtime_action_completed")
        self.assertEqual(tool_result["law_event_log"]["details"]["cisiv_stage"], "verification")
        self.assertEqual(tool_result["law_event_log"]["details"]["action_id"], "run_pytest")

    def test_execute_action_exposes_governed_cycle_stage_logs_and_carryover_state(self):
        """Runtime actions should surface the governed cycle instead of hiding it behind one summary event."""
        operator = JarvisOperator()
        mocked_result = {
            "action": dict(operator.action_runner.get_action("run_pytest") or {"id": "run_pytest", "label": "Run Pytest"}),
            "status": "completed",
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "summary": "364 passed, 6 subtests passed.",
            "ran_at": "2026-04-14T00:00:00+00:00",
        }

        with patch.object(operator.action_runner, "execute_action", return_value=mocked_result):
            payload = operator.execute_action("run_pytest", session_id="session-law")

        governed_cycle = payload["tool_result"]["law_enforcement"]["governed_cycle"]
        stage_types = {entry["event_type"] for entry in governed_cycle["stage_logs"]}
        self.assertEqual(governed_cycle["status"], "success")
        self.assertTrue(governed_cycle["truthful"])
        self.assertTrue(
            {
                "gamma_legitimacy",
                "l1_verification",
                "1010_design_judgment",
                "1111_debt_reckoning",
                "l2_final_truth",
                "admit",
                "delta_stabilization",
                "voss_binding",
                "next_1000",
            }.issubset(stage_types)
        )
        self.assertIn("debt", governed_cycle["carryover_state"])
        self.assertIn("risk_profile", governed_cycle["carryover_state"])
        self.assertIn("prime_depth", governed_cycle["carryover_state"])
        self.assertTrue(governed_cycle["carryover_state"]["bound_flag"])

    def test_execute_action_preserves_governed_cycle_carryover_for_same_session(self):
        """Carryover state should persist across governed runtime actions instead of resetting every turn."""
        operator = JarvisOperator()
        mocked_overload = {
            "action": dict(operator.action_runner.get_action("run_pytest") or {"id": "run_pytest", "label": "Run Pytest"}),
            "status": "overload",
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "summary": "Pytest overloaded the local lane.",
            "ran_at": "2026-04-14T00:00:00+00:00",
        }
        mocked_success = {
            "action": dict(operator.action_runner.get_action("run_pytest") or {"id": "run_pytest", "label": "Run Pytest"}),
            "status": "completed",
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "summary": "364 passed, 6 subtests passed.",
            "ran_at": "2026-04-14T00:05:00+00:00",
        }

        with patch.object(operator.action_runner, "execute_action", side_effect=[mocked_overload, mocked_success]):
            first = operator.execute_action("run_pytest", session_id="session-carryover")
            second = operator.execute_action("run_pytest", session_id="session-carryover")

        first_cycle = first["tool_result"]["law_enforcement"]["governed_cycle"]
        second_cycle = second["tool_result"]["law_enforcement"]["governed_cycle"]
        first_carryover = first["tool_result"]["law_enforcement"]["governed_cycle"]["carryover_state"]
        second_carryover = second["tool_result"]["law_enforcement"]["governed_cycle"]["carryover_state"]
        self.assertEqual(first_cycle["status"], "wait")
        self.assertGreaterEqual(first_carryover["wait_count"], 1)
        self.assertIsNotNone(first_carryover["next_check_at"])
        self.assertEqual(second_carryover["cycle_count"], first_carryover["cycle_count"] + 1)
        self.assertGreaterEqual(second_carryover["risk_profile"], 0)
        self.assertGreaterEqual(second_carryover["wait_count"], first_carryover["wait_count"])
        self.assertTrue(second_carryover["bound_flag"])

    def test_execute_action_blocks_raw_external_adoption_without_law_filter(self):
        """Runtime actions should fail closed if an external suggestion is marked for adoption without admission context."""
        operator = JarvisOperator()
        mocked_result = {
            "action": dict(operator.action_runner.get_action("run_pytest") or {"id": "run_pytest", "label": "Run Pytest"}),
            "status": "completed",
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "summary": "364 passed, 6 subtests passed.",
            "ran_at": "2026-04-14T00:00:00+00:00",
        }

        with patch.object(operator.action_runner, "execute_action", return_value=mocked_result) as mocked_execute:
            with self.assertRaisesRegex(
                ValueError,
                "external_suggestion_law_filter, admitted_external_form",
            ):
                operator.execute_action(
                    "run_pytest",
                    action={
                        "external_suggestion": {
                            "source": "outside_note",
                            "summary": "Adopt this raw command suggestion.",
                        },
                        "external_suggestion_usage": "adoption",
                    },
                    session_id="session-law",
                )
        mocked_execute.assert_not_called()

    def test_execute_action_records_admitted_external_suggestion_when_filtered(self):
        """Runtime actions should carry admitted external suggestion state once the law filter and admitted form are present."""
        operator = JarvisOperator()
        mocked_result = {
            "action": dict(operator.action_runner.get_action("run_pytest") or {"id": "run_pytest", "label": "Run Pytest"}),
            "status": "completed",
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "summary": "364 passed, 6 subtests passed.",
            "ran_at": "2026-04-14T00:00:00+00:00",
        }

        with patch.object(operator.action_runner, "execute_action", return_value=mocked_result):
            payload = operator.execute_action(
                "run_pytest",
                action={
                    "external_suggestion": {
                        "source": "outside_note",
                        "summary": "Adopt this filtered command suggestion.",
                    },
                    "external_suggestion_usage": "adoption",
                    "law_filter_applied": True,
                    "admitted_external_form": "Keep the existing run_pytest action, but allow the outside suggestion to influence only the execution timing.",
                },
                session_id="session-law",
            )

        admission = payload["tool_result"]["law_enforcement"]["external_suggestion_admission"]
        self.assertEqual(admission["status"], "admitted")
        self.assertTrue(admission["law_filter_applied"])
        self.assertTrue(admission["admitted_form_documented"])


if __name__ == "__main__":
    unittest.main()
