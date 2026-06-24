"""Tests for reconstruction operator R — trace to judgment dynamics."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.crk1.errors import ConstitutionalError
from src.crk1.judgment_trace import JudgmentTrace
from src.crk1.reconstruction_operator import (
    decode_context,
    decode_evidence,
    decode_outcome,
    infer_update_rule,
    reconstruct,
    reconstruction_sufficient,
    reconstruct_or_report,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "crk1"


def _sample_trace() -> JudgmentTrace:
    payload = json.loads((FIXTURES / "sample_judgment_trace.json").read_text(encoding="utf-8"))
    return JudgmentTrace.model_validate(payload)


def test_decode_steps() -> None:
    trace = _sample_trace()
    e_hat = decode_evidence(trace)
    w_hat_t = decode_context(trace)
    f_hat = infer_update_rule(trace)
    w_hat_next = decode_outcome(trace)

    assert e_hat["signal"] == pytest.approx(0.72)
    assert w_hat_t.valuation == pytest.approx(0.4)
    assert f_hat.target_dimension == "valuation"
    assert w_hat_next.valuation == pytest.approx(0.49)


def test_reconstruct_coherent_trace() -> None:
    result = reconstruct(_sample_trace(), tolerance=0.15)
    assert result.coherent is True
    assert result.reconstruction_error <= 0.15
    predicted = result.f_hat.apply(result.w_t, result.evidence_decoded)
    assert predicted.l2_distance(result.w_t_plus_1) <= 0.15


def test_reconstruct_fails_when_incoherent() -> None:
    trace = _sample_trace()
    trace.correction.postCorrectionState["valuation"] = 0.9
    with pytest.raises(ConstitutionalError, match="Reconstruction failed"):
        reconstruct(trace, tolerance=0.05)


def test_reconstruction_sufficiency_sequence() -> None:
    trace = _sample_trace()
    assert reconstruction_sufficient([trace], tolerance=0.15) is True

    bad = _sample_trace()
    bad.correction.postCorrectionState["valuation"] = 0.95
    assert reconstruction_sufficient([trace, bad], tolerance=0.05) is False


def test_reconstruct_or_report_non_throwing() -> None:
    trace = _sample_trace()
    trace.correction.postCorrectionState["valuation"] = 0.95
    report = reconstruct_or_report(trace, tolerance=0.05)
    assert report.coherent is False
    assert report.reconstruction_error > 0.05
