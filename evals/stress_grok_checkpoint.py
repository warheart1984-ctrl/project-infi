#!/usr/bin/env python3
"""Stress harness: Grok imagine path + planning checkpoint + tool-call parsing.

Emits JSON lines to stdout for reproducible traces. No network calls unless
STRESS_GROK_LIVE=1 and keys are set.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def emit(trace_id: str, scenario: str, status: str, **payload: Any) -> None:
    record = {
        "trace_id": trace_id,
        "scenario": scenario,
        "status": status,
        "at": _utc(),
        **payload,
    }
    print(json.dumps(record, sort_keys=True))


def stress_tool_call_parsing(trace_id: str) -> None:
    from src.providers.http_chat_provider import parse_tool_calls

    cases = [
        ("empty", {}),
        ("malformed_args", {"tool_calls": [{"id": "t1", "function": {"name": "grep", "arguments": "{not json"}}]}),
        ("nested_raw", {"tool_calls": [{"id": "t2", "type": "function", "function": {"name": "read", "arguments": '{"path": "e:/a"}'}}]}),
        ("duplicate_ids", {"tool_calls": [{"id": "dup", "function": {"name": "a", "arguments": "{}"}}, {"id": "dup", "function": {"name": "b", "arguments": "{}"}}]}),
        ("missing_name", {"tool_calls": [{"id": "t3", "function": {"arguments": "{}"}}]}),
    ]
    for label, message in cases:
        try:
            parsed = parse_tool_calls(message, provider_id="xai")
            emit(
                trace_id,
                f"tool_parse.{label}",
                "ok",
                count=len(parsed or []),
                names=[getattr(t, "name", None) for t in (parsed or [])],
            )
        except Exception as exc:
            emit(trace_id, f"tool_parse.{label}", "fail", error=str(exc), tb=traceback.format_exc())


def stress_checkpoint_verification(trace_id: str) -> None:
    from src.cog_runtime.execution import _verify_execution

    checkpoints = [
        "Focus visible in opening lines",
        "Decision or arc next action stated when applicable",
        "Alignment check before send",
    ]
    bodies = [
        ("pass_like", "Focus: option A or B\n\nRecommend Postgres for durable cache with alignment check before send."),
        ("miss_focus", "Here is a long answer without the required opening vocabulary."),
        ("partial_overlap", "Focus and alignment are mentioned but decision arc next action is thin."),
        ("empty", ""),
    ]
    for label, body in bodies:
        status, gaps = _verify_execution(
            bound_action="Recommend Postgres for durable cache",
            speak_body=body,
            focus_artifact={"primary_focus": "Postgres durable cache"},
            checkpoints=checkpoints,
        )
        emit(trace_id, f"checkpoint.{label}", status, gaps=gaps, body_len=len(body))


def stress_grok_key_matrix(trace_id: str) -> None:
    from src import imagine_grok as ig

    saved = {k: os.environ.get(k) for k in ig.XAI_ENV_KEYS}
    try:
        for k in ig.XAI_ENV_KEYS:
            os.environ.pop(k, None)
        none_ok = ig.resolve_xai_api_key() is None
        emit(
            trace_id,
            "grok.keys.none",
            "ok" if none_ok else "fail",
            configured=not none_ok,
            note="fail when host env leaks XAI keys into isolated test",
        )

        os.environ["XAI_API_KEY"] = "stress-test-key"
        emit(trace_id, "grok.keys.xai_only", "ok", configured=bool(ig.resolve_xai_api_key()))

        os.environ.pop("XAI_API_KEY", None)
        os.environ["STORY_FORGE_XAI_API_KEY"] = "forge-key"
        emit(trace_id, "grok.keys.story_forge_first", "ok", key_prefix=ig.resolve_xai_api_key()[:6])
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def stress_grok_render_chain(trace_id: str) -> None:
    from src.imagine_grok import KeysRequiredError, grok_render_pattern

    pattern = {"pattern_id": "stress-001", "prompt_frame": "test frame", "imagine_generator_version": "v1"}
    try:
        grok_render_pattern(pattern)
        emit(trace_id, "grok.render.no_keys", "unexpected_ok")
    except KeysRequiredError as exc:
        emit(trace_id, "grok.render.no_keys", "ok", error_type="KeysRequired", message=str(exc)[:120])
    except Exception as exc:
        emit(trace_id, "grok.render.no_keys", "fail", error=str(exc), tb=traceback.format_exc())

    # 1x1 PNG — same fixture as tests/test_imagine_grok.py FakeTransport
    _PNG_B64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )

    class MockTransport:
        def post_json(self, url: str, body: dict, headers: dict, timeout_seconds: float) -> dict:
            return {"data": [{"b64_json": _PNG_B64}], "model": "grok-imagine-image-mock"}

    with tempfile.TemporaryDirectory(prefix="stress_grok_") as tmp:
        root = Path(tmp)
        os.environ["XAI_API_KEY"] = "mock-key"
        try:
            from src.imagine_generator import build_pattern_from_fixture, persist_pattern

            pattern = build_pattern_from_fixture("scene-seed-demo")
            persist_pattern(pattern, root=root)
            result = grok_render_pattern(
                pattern,
                transport=MockTransport(),
                imagine_root=root,
            )
            artifact = result.get("artifact") or {}
            emit(
                trace_id,
                "grok.render.mock_chain",
                "ok",
                render_status=result.get("status"),
                provider=artifact.get("provider"),
                claim_label=artifact.get("claim_label"),
                has_artifact_path=bool(artifact.get("artifact_path")),
            )
        except Exception as exc:
            emit(trace_id, "grok.render.mock_chain", "fail", error=str(exc), tb=traceback.format_exc())
        finally:
            os.environ.pop("XAI_API_KEY", None)


def stress_multi_file_route_consistency(trace_id: str) -> None:
    """Correlate HTTP status codes across API docstring vs capability vs tests."""
    issues: list[str] = []
    api_path = ROOT / "src" / "api.py"
    cap_path = ROOT / "src" / "capabilities" / "imagine_generator.py"
    api_text = api_path.read_text(encoding="utf-8")
    cap_text = cap_path.read_text(encoding="utf-8")
    if "428" not in api_text or "keys_required" not in api_text:
        issues.append("api_missing_428_keys_required")
    if 'error_type": "KeysRequired"' not in cap_text and "KeysRequired" not in cap_text:
        issues.append("capability_missing_KeysRequired")
    if "blocked" not in (ROOT / "src" / "capability_service_bridge.py").read_text(encoding="utf-8"):
        issues.append("bridge_missing_blocked_status")
    emit(trace_id, "multi_file.route_consistency", "ok" if not issues else "fail", issues=issues)


def main() -> int:
    trace_id = os.environ.get("STRESS_TRACE_ID", f"grok-stress-{int(datetime.now().timestamp())}")
    emit(trace_id, "harness.start", "ok", root=str(ROOT))
    stress_tool_call_parsing(trace_id)
    stress_checkpoint_verification(trace_id)
    stress_grok_key_matrix(trace_id)
    stress_grok_render_chain(trace_id)
    stress_multi_file_route_consistency(trace_id)
    if os.environ.get("STRESS_GROK_LIVE") == "1":
        emit(trace_id, "grok.live", "skipped", reason="live path not implemented in harness")
    emit(trace_id, "harness.end", "ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
