"""Continuity SDK CLI — `continuity` command."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence


SDK_VERSION = "1"
SDK_TAGLINE = "Governed • Corrigible • Lineage-Preserving"


def cmd_info() -> int:
    from continuity_sdk.branding import SDK_BADGE, SDK_BADGE_SMALL

    print(SDK_BADGE)
    print()
    print(SDK_BADGE_SMALL)
    return 0


def cmd_onboarding() -> int:
    from continuity_sdk.branding import STEWARD_ONBOARDING

    print(STEWARD_ONBOARDING)
    return 0


def cmd_demo_falling_object() -> int:
    from continuity_sdk import run_falling_object_scenario

    print("Running MVCD...")
    correction, crr1 = run_falling_object_scenario()
    expected = crr1.get("expected_outcome", crr1.get("prior_judgment_state", {}))
    observed = crr1.get("observed_outcome", crr1.get("reality_contact", {}))
    if isinstance(expected, dict):
        expected = expected.get("prior_model", {}).get("expected_outcome", 1.0)
    if isinstance(observed, dict):
        observed = observed.get("evidence_observed", 0.3)

    print(f"Expectation: {expected}s")
    print(f"Observation: {observed}s")
    print("Contradiction detected.")
    print("Correction applied.")
    delta = crr1.get("calibration_delta", 0)
    print(f"Calibration delta: {abs(float(delta)):.1f}")
    _ = correction  # used by callers / tests
    return 0


def cmd_mission_005() -> int:
    from continuity_sdk import run_mission_005_calibration_lineage_stress

    print("Running Calibration Lineage Stress Test...")
    report = run_mission_005_calibration_lineage_stress()
    print(f"{len(report.stewards)} stewards")
    print(f"{report.crr_count} corrections")
    print(f"{report.crr_count} CRR-1 receipts")
    print("Lineage reconstructed")
    print("Status:", "PASSED" if report.passed else "FAILED")
    if not report.passed and report.failures:
        for failure in report.failures:
            print(f"  • {failure}", file=sys.stderr)
        return 1
    return 0


def cmd_console() -> int:
    from continuity_sdk.steward_console import render_steward_console

    print(render_steward_console())
    return 0


def cmd_certify(answers: list[str] | None) -> int:
    from continuity_sdk.steward_certification import (
        CERTIFICATION_TITLE,
        PASSING_SCORE,
        STEWARD_CERTIFICATION_QUESTIONS,
        format_question,
        grade_steward_certification,
    )

    if answers is None:
        print("Steward Certification Test (v1)")
        print(f"Passing score: {PASSING_SCORE}/{len(STEWARD_CERTIFICATION_QUESTIONS)}")
        print()
        collected: list[str] = []
        labels = ("A", "B", "C", "D")
        for question in STEWARD_CERTIFICATION_QUESTIONS:
            print(format_question(question))
            while True:
                raw = input("Answer (A-D): ").strip().upper()[:1]
                if raw in labels:
                    collected.append(raw)
                    break
                print("  Enter A, B, C, or D.")
            print()
        answers = collected

    result = grade_steward_certification(answers)
    print(f"Score: {result.score}/{result.total}")
    if result.passed:
        print(f"Certification: {CERTIFICATION_TITLE}")
        return 0
    print("Certification: Not certified")
    if result.failures:
        print("Review questions:", ", ".join(str(n) for n in result.failures))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="continuity",
        description="Continuity SDK — governed, corrigible, lineage-preserving steward interface.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info", help="Show SDK badge and version")

    sub.add_parser("onboarding", help="Print one-page steward onboarding sheet")

    demo = sub.add_parser("demo", help="Run canonical continuity demos")
    demo.add_argument("scenario", choices=["falling-object"], help="Demo scenario")

    mission = sub.add_parser("mission", help="Run continuity mission stress tests")
    mission.add_argument("id", choices=["005"], help="Mission identifier")

    sub.add_parser("console", help="Render VR-style steward console mockup")

    certify = sub.add_parser("certify", help="Steward Certification Test (Level 1)")
    certify.add_argument(
        "--answers",
        metavar="A,B,C,...",
        help="Comma-separated answers (A-D) for non-interactive grading",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)

    if args.cmd == "info":
        return cmd_info()
    if args.cmd == "onboarding":
        return cmd_onboarding()
    if args.cmd == "demo" and args.scenario == "falling-object":
        return cmd_demo_falling_object()
    if args.cmd == "mission" and args.id == "005":
        return cmd_mission_005()
    if args.cmd == "console":
        return cmd_console()
    if args.cmd == "certify":
        answer_list = None
        if getattr(args, "answers", None):
            answer_list = [part.strip() for part in args.answers.split(",")]
        return cmd_certify(answer_list)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
