"""Steward certification tests."""

from __future__ import annotations

import pytest

from continuity_sdk.steward_certification import (
    CERTIFICATION_TITLE,
    PASSING_SCORE,
    grade_steward_certification,
)


def test_certification_passing_answers() -> None:
    answers = ["B", "B", "B", "B", "B", "B", "B", "C", "B", "C"]
    result = grade_steward_certification(answers)
    assert result.score == 10
    assert result.passed
    assert result.title == CERTIFICATION_TITLE


def test_certification_minimum_pass() -> None:
    # 9 correct, 1 wrong (question 1)
    answers = ["A", "B", "B", "B", "B", "B", "B", "C", "B", "C"]
    result = grade_steward_certification(answers)
    assert result.score == PASSING_SCORE
    assert result.passed


def test_certification_fail() -> None:
    answers = ["A"] * 10
    result = grade_steward_certification(answers)
    assert not result.passed
    assert result.failures


def test_certification_wrong_count_raises() -> None:
    with pytest.raises(ValueError):
        grade_steward_certification(["B"])


def test_cli_certify_batch(capsys) -> None:
    from continuity_sdk.cli import main

    code = main(["certify", "--answers", "B,B,B,B,B,B,B,C,B,C"])
    out = capsys.readouterr().out
    assert code == 0
    assert CERTIFICATION_TITLE in out
