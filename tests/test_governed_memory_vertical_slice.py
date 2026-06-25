"""Governed vertical slice — intent → authority → span → trace → replay (Python)."""

from __future__ import annotations

from pathlib import Path

import pytest

from governed_memory import (
    AuthorityLedger,
    ExecutionSpanManager,
    GovernanceEnforcementEngine,
    IntentLedger,
    complete_span,
    create_intent,
    issue_authority,
    record_trace,
    replay,
    start_span,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "coordination_bottlenecks.md"


def _fresh_stack() -> tuple[IntentLedger, AuthorityLedger, ExecutionSpanManager, GovernanceEnforcementEngine]:
    intents = IntentLedger()
    authority = AuthorityLedger()
    spans = ExecutionSpanManager()
    governance = GovernanceEnforcementEngine(intents, authority)
    return intents, authority, spans, governance


def _summarize_top_three_bottlenecks(text: str) -> str:
    headings = [line.replace("## ", "").strip() for line in text.splitlines() if line.startswith("## ")]
    return "; ".join(headings[:3])


def test_vertical_slice_intent_authority_span_replay() -> None:
    intents, authority, spans, governance = _fresh_stack()

    intent = create_intent(
        "Summarize the top 3 coordination bottlenecks in this document.",
        ["read_fixture_only", "no_destructive_writes"],
        "operator-test",
        intent_ledger=intents,
    )
    token = issue_authority(
        intent.version,
        ["read_document", "summarize", "cluster"],
        "governance-test",
        authority_ledger=authority,
    )
    span = start_span(intent.version, token.token_id, span_manager=spans)

    fixture_text = FIXTURE.read_text(encoding="utf-8")
    summary = _summarize_top_three_bottlenecks(fixture_text)
    assert "Handoffs between teams" in summary
    assert "Unclear priorities" in summary
    assert "Tool fragmentation" in summary

    record_trace(
        span.span_id,
        step_type="reasoning",
        content=summary,
        justification="Fixture-driven stub summarizer cites three ## headings.",
        intent_version=intent.version,
        authority_token_id=token.token_id,
        span_manager=spans,
        governance=governance,
    )
    record_trace(
        span.span_id,
        step_type="tool",
        content=fixture_text[:200],
        justification="Read fixture for deterministic bottleneck extraction.",
        intent_version=intent.version,
        authority_token_id=token.token_id,
        span_manager=spans,
        governance=governance,
    )
    complete_span(span.span_id, span_manager=spans)

    result = replay(
        span.span_id,
        span_manager=spans,
        intent_ledger=intents,
        authority_ledger=authority,
        governance=governance,
    )
    assert result.success is True
    assert result.violations == []


def test_replay_fails_after_authority_revocation() -> None:
    intents, authority, spans, governance = _fresh_stack()
    intent = create_intent("goal", [], "op", intent_ledger=intents)
    token = issue_authority(intent.version, ["execute"], "gov", authority_ledger=authority)
    span = start_span(intent.version, token.token_id, span_manager=spans)
    record_trace(
        span.span_id,
        step_type="reasoning",
        content="step",
        justification="justified",
        intent_version=intent.version,
        authority_token_id=token.token_id,
        span_manager=spans,
        governance=governance,
    )
    complete_span(span.span_id, span_manager=spans)
    authority.revoke(token.token_id)

    result = replay(
        span.span_id,
        span_manager=spans,
        intent_ledger=intents,
        authority_ledger=authority,
        governance=governance,
    )
    assert result.success is False
    assert any(v.code == "AUTHORITY_FAULT" for v in result.violations)
