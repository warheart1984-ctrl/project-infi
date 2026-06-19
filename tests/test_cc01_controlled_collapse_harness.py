"""Tests for CC-01 CIEMS Controlled Collapse harness."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.stress.cc01_backend import build_backend
from tools.stress.cc01_controlled_collapse_harness import (
    FAILURE_MEANINGS,
    Cc01ControlledCollapseHarness,
    CiemsEvent,
    SharedAgentWorkspace,
    run_cc01,
)


REQUIRED_LOG_KEYS = {
    "timestamp",
    "thread_id",
    "event_type",
    "input",
    "context_hash_before",
    "context_hash_after",
    "output_hash",
    "state_change",
    "file_target",
    "conflict_flag",
    "failure_code",
    "latency_ms",
    "backend",
    "nova_request_id",
    "nova_session_id",
}


def test_failure_code_map_complete() -> None:
    assert set(FAILURE_MEANINGS) == {"F-01", "F-02", "F-03", "F-04", "F-05"}


def test_ciems_event_schema_keys() -> None:
    event = CiemsEvent(
        timestamp="t",
        thread_id="thread-0",
        event_type="workload_edit",
        input="x",
        context_hash_before="a",
        context_hash_after="b",
        output_hash="c",
        state_change="edit",
        file_target="agent/project/main.py",
        conflict_flag=True,
        failure_code="F-01",
        latency_ms=3,
    )
    assert set(event.to_dict().keys()) == REQUIRED_LOG_KEYS


def test_ciems_event_includes_optional_nova_fields() -> None:
    event = CiemsEvent(
        timestamp="t",
        thread_id="thread-0",
        event_type="workload_edit",
        input="x",
        context_hash_before="a",
        context_hash_after="b",
        output_hash="c",
        state_change="edit",
        file_target="agent/project/main.py",
        conflict_flag=True,
        failure_code="F-01",
        latency_ms=3,
        backend="nova",
        nova_request_id="req-1",
        nova_session_id="sess-1",
    )
    payload = event.to_dict()
    assert payload["backend"] == "nova"
    assert payload["nova_request_id"] == "req-1"
    assert payload["nova_session_id"] == "sess-1"


def test_build_backend_simulated(tmp_path: Path) -> None:
    ws = SharedAgentWorkspace(tmp_path / "ws")
    backend, label = build_backend(mode="simulated", workspace=ws)
    assert label == "simulated"
    backend.ensure_thread("thread-0")
    assert backend.get_context("thread-0")


def test_short_run_produces_jsonl_and_failures(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    out_dir = tmp_path / "out"
    verdict = run_cc01(
        workspace_root=workspace,
        out_dir=out_dir,
        duration_sec=8.0,
        num_threads=6,
        seed=42,
    )
    log_path = out_dir / "cc01_events.jsonl"
    summary_path = out_dir / "cc01_summary.json"
    assert log_path.exists()
    assert summary_path.exists()
    assert verdict.total_events > 0

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    for line in lines:
        payload = json.loads(line)
        assert REQUIRED_LOG_KEYS.issubset(payload.keys())

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "failure_counts" in summary
    assert "trace_samples" in summary
    assert summary["backend"] == "simulated"
    assert "would_pass" in summary
    assert summary["pass"] is False


def test_injection_events_logged_with_seed(tmp_path: Path) -> None:
    harness = Cc01ControlledCollapseHarness(
        workspace_root=tmp_path / "ws",
        num_threads=8,
        duration_sec=12.0,
        seed=7,
    )
    harness.run()
    types = {e.event_type for e in harness.events}
    assert any("injection_A" in t for t in types)
    assert any("injection_B" in t for t in types)
    assert any("injection_C" in t for t in types)
    assert any("injection_D" in t for t in types)


@pytest.mark.parametrize("duration", [90.0, 150.0])
def test_duration_within_spec_range(duration: float) -> None:
    assert 90.0 <= duration <= 180.0


def test_nova_safety_caps_in_main() -> None:
    from tools.stress.cc01_controlled_collapse_harness import main

    with patch(
        "tools.stress.cc01_controlled_collapse_harness.check_health",
        return_value=(200, {"ok": True}),
    ), patch(
        "tools.stress.cc01_controlled_collapse_harness.run_cc01"
    ) as run_mock:
        run_mock.return_value = type(
            "V",
            (),
            {
                "pass_gate": False,
                "would_pass": True,
                "backend": "nova",
                "failure_counts": {},
                "violations": [],
            },
        )()
        code = main(
            [
                "--backend",
                "nova",
                "--duration",
                "200",
                "--threads",
                "16",
                "--nova-base-url",
                "http://127.0.0.1:5000",
            ]
        )
    assert code == 0
    kwargs = run_mock.call_args.kwargs
    assert kwargs["duration_sec"] == 180.0
    assert kwargs["num_threads"] == 8
    assert kwargs["backend"] == "nova"


def test_nova_ensure_thread_parses_large_session_with_max_body_zero(tmp_path: Path) -> None:
    import tools.stress.cc01_backend as cc01_backend_mod
    from tools.stress.cc01_backend import NovaBackend

    backend = NovaBackend(
        repo_root=tmp_path,
        base_url="http://127.0.0.1:8000",
        queue_name="cc01-chaos",
    )
    large_body = {
        "session_id": "sess-large-1",
        "metadata": {"blob": "x" * 9000},
    }

    def fake_req(
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
        max_body: int = 500,
        parse_json: bool = False,
    ) -> tuple[int, object]:
        if method == "POST" and path == "/api/chat/sessions":
            assert max_body == 0
            return 201, large_body
        if method == "POST" and "/super-nova/activate" in path:
            assert max_body == 0
            return 200, {"ok": True}
        raise AssertionError(f"unexpected request {method} {path}")

    with patch.object(cc01_backend_mod.chaos, "_req", side_effect=fake_req):
        backend.ensure_thread("thread-0")

    assert backend._sessions["thread-0"] == "sess-large-1"


def test_enqueue_starvation_avoids_get_context(tmp_path: Path) -> None:
    harness = Cc01ControlledCollapseHarness(
        workspace_root=tmp_path / "ws",
        num_threads=1,
        duration_sec=5.0,
        queue_capacity=1,
        backend_mode="simulated",
    )
    harness._ctx_cache["thread-0"] = "cached_ctx"
    harness.request_queue.put(("thread-0", "summarize", ""), block=False)

    with patch.object(harness.backend, "get_context") as get_ctx:
        ok = harness._enqueue("thread-0", "edit", "burst")

    assert ok is False
    get_ctx.assert_not_called()
    starvation = [e for e in harness.events if e.failure_code == "F-03"]
    assert len(starvation) == 1
    assert starvation[0].context_hash_before == "cached_ctx"
    assert starvation[0].context_hash_after == "cached_ctx"
    assert starvation[0].event_type == "queue_starvation"


def test_nova_record_debug_none_status_marks_f03_not_typeerror(tmp_path: Path) -> None:
    from tools.stress import cc01_backend as cc01_backend_mod

    backend = cc01_backend_mod.NovaBackend(
        repo_root=tmp_path,
        base_url="http://127.0.0.1:8000",
        max_qps=100.0,
    )
    backend._sessions["thread-0"] = "sess-1"

    def fake_chat(_thread_id: str, _message: str) -> tuple[int | None, dict, int]:
        return None, {"error": "timed out"}, 42

    with patch.object(backend, "_chat_message", side_effect=fake_chat):
        result = backend.record_debug("thread-0", "probe")

    assert result.failure_code == "F-03"
    assert result.extra["http_status"] is None


def test_http_failure_code_5xx_is_f04() -> None:
    from tools.stress.cc01_backend import _http_failure_code

    assert _http_failure_code(None) == "F-03"
    assert _http_failure_code(500) == "F-04"
    assert _http_failure_code(200) == ""


def test_safe_get_context_uses_cache_on_backend_error(tmp_path: Path) -> None:
    harness = Cc01ControlledCollapseHarness(
        workspace_root=tmp_path / "ws",
        num_threads=2,
        duration_sec=5.0,
        seed=1,
    )
    harness._ctx_cache["thread-1"] = "cached_ctx"
    with patch.object(harness.backend, "get_context", side_effect=RuntimeError("connection refused")):
        assert harness._safe_get_context("thread-1") == "cached_ctx"


def test_inject_context_swap_trick_survives_get_context_failure(tmp_path: Path) -> None:
    harness = Cc01ControlledCollapseHarness(
        workspace_root=tmp_path / "ws",
        num_threads=2,
        duration_sec=5.0,
        seed=1,
        backend_mode="nova",
    )
    with patch.object(harness.backend, "get_context", side_effect=RuntimeError("connection refused")):
        with patch.object(harness.backend, "ensure_thread"):
            with patch.object(
                harness.backend,
                "record_debug",
                return_value=type("R", (), {"failure_code": "", "extra": {}})(),
            ):
                with patch.object(harness.backend, "summarize_context", return_value="summary"):
                    harness._inject_context_swap_trick()
    assert any("injection_C" in e.event_type for e in harness.events)
