"""Steward Certification Test (v1) — Lawful Steward Level 1."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StewardCertificationQuestion:
    number: int
    prompt: str
    choices: tuple[str, str, str, str]
    correct: str  # A, B, C, or D


@dataclass
class StewardCertificationResult:
    score: int
    total: int
    passed: bool
    title: str
    failures: list[int]

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "total": self.total,
            "passed": self.passed,
            "title": self.title,
            "failures": list(self.failures),
        }


STEWARD_CERTIFICATION_QUESTIONS: tuple[StewardCertificationQuestion, ...] = (
    StewardCertificationQuestion(
        1,
        "What does K-∞ require?",
        (
            "That models remain accurate",
            "That reality can recalibrate future judgment",
            "That stewards agree with each other",
            "That lineage is optional",
        ),
        "B",
    ),
    StewardCertificationQuestion(
        2,
        "Which object preserves judgment?",
        ("CRR-1", "GRR-1", "ExpectationObject", "EvidenceObject"),
        "B",
    ),
    StewardCertificationQuestion(
        3,
        "Which object preserves correction?",
        ("GRR-1", "CRR-1", "CalibrationEvent", "SurpriseObject"),
        "B",
    ),
    StewardCertificationQuestion(
        4,
        "What must every steward emit before acting?",
        (
            "A lineage node",
            "A governance receipt",
            "A correction",
            "A surprise magnitude",
        ),
        "B",
    ),
    StewardCertificationQuestion(
        5,
        "What triggers CE-1?",
        ("A decision", "A contradiction", "A lineage update", "A steward request"),
        "B",
    ),
    StewardCertificationQuestion(
        6,
        "What is the purpose of CLG-1?",
        (
            "Store model weights",
            "Preserve calibration lineage",
            "Track steward identities",
            "Compute surprise",
        ),
        "B",
    ),
    StewardCertificationQuestion(
        7,
        "What is forbidden by CK-1?",
        ("Multiple stewards", "Hidden evidence", "Corrections", "Lineage queries"),
        "B",
    ),
    StewardCertificationQuestion(
        8,
        "What must a steward never do?",
        (
            "Emit expectations",
            "Accept evidence",
            "Insulate itself from contradiction",
            "Produce CRR-1 receipts",
        ),
        "C",
    ),
    StewardCertificationQuestion(
        9,
        "What does Mission #005 test?",
        (
            "Model accuracy",
            "Multi-steward calibration lineage",
            "Governance speed",
            "Evidence throughput",
        ),
        "B",
    ),
    StewardCertificationQuestion(
        10,
        "What is the core property of continuity?",
        ("Accuracy", "Stability", "Corrigibility", "Consensus"),
        "C",
    ),
)

PASSING_SCORE = 9
CERTIFICATION_TITLE = "Lawful Steward — Level 1"


def grade_steward_certification(answers: list[str]) -> StewardCertificationResult:
    """Grade answers (A–D). Requires 9/10 to pass."""
    total = len(STEWARD_CERTIFICATION_QUESTIONS)
    if len(answers) != total:
        raise ValueError(f"expected {total} answers, got {len(answers)}")

    normalized = [a.strip().upper()[:1] for a in answers]
    failures: list[int] = []
    score = 0

    for question, answer in zip(STEWARD_CERTIFICATION_QUESTIONS, normalized, strict=True):
        if answer == question.correct:
            score += 1
        else:
            failures.append(question.number)

    passed = score >= PASSING_SCORE
    title = CERTIFICATION_TITLE if passed else "Not certified"

    return StewardCertificationResult(
        score=score,
        total=total,
        passed=passed,
        title=title,
        failures=failures,
    )


def format_question(question: StewardCertificationQuestion) -> str:
    labels = ("A", "B", "C", "D")
    lines = [f"{question.number}. {question.prompt}"]
    for label, choice in zip(labels, question.choices, strict=True):
        lines.append(f"   {label}) {choice}")
    return "\n".join(lines)


__all__ = [
    "CERTIFICATION_TITLE",
    "PASSING_SCORE",
    "STEWARD_CERTIFICATION_QUESTIONS",
    "StewardCertificationQuestion",
    "StewardCertificationResult",
    "format_question",
    "grade_steward_certification",
]
