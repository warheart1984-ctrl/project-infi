"""Stewardship Legitimacy Panel — steward-facing legitimacy status."""

from __future__ import annotations

import sys
from typing import IO

from constitutional.legitimacy.legitimacy_drift import LegitimacyDriftState
from constitutional.legitimacy.legitimacy_exam import LegitimacyExamResult
from constitutional.legitimacy.legitimacy_register import StewardshipLegitimacyRegister
from constitutional.legitimacy.spec import JUDGMENT_LAYER_DESCRIPTIONS, JUDGMENT_STACK_LAYERS, LEGITIMACY_REFERENCE


def format_legitimacy_panel(
    *,
    register: StewardshipLegitimacyRegister,
    exam: LegitimacyExamResult | None,
    drift: LegitimacyDriftState | None,
) -> str:
    lines: list[str] = [
        "",
        f"=== STEWARDSHIP LEGITIMACY ({LEGITIMACY_REFERENCE}) ===",
        "Authority by reconstruction — not title, vote, or founder preference.",
        "----------------------------------------",
        "",
        "Judgment stack:",
    ]
    for layer in JUDGMENT_STACK_LAYERS:
        lines.append(f"  {layer}: {JUDGMENT_LAYER_DESCRIPTIONS[layer]}")

    active = register.active_stewards()
    lines.extend(
        [
            "",
            f"Certified stewards: {len(active)} (plurality min: {register.minimum_plurality})",
            f"Plurality satisfied: {register.plurality_satisfied()}",
        ]
    )
    for entry in active:
        certifiers = ", ".join(entry.certified_by) or "none"
        process_flag = "yes" if entry.process_passed else "no"
        lines.append(
            f"  - {entry.steward_id}: index={entry.legitimacy_index:.2f}, "
            f"process={process_flag}, certified_by=[{certifiers}]"
        )

    if exam is not None:
        lines.extend(
            [
                "",
                f"Legitimacy exam ({exam.steward_id}): {'PASS' if exam.passed else 'FAIL'}",
                f"  Index: {exam.legitimacy_index:.2f}",
                f"  JPSS formation: {exam.jpss_formation_ready}",
                f"  JPSS-I balancing: {exam.jpss_i_balancing_passed}",
                f"  JPSS-C constitutional: {exam.jpss_c_passed}",
                f"  Reconstruction criterion: {exam.reconstruction_criterion_passed}",
            ]
        )
        if exam.blockers:
            lines.append(f"  Blockers: {exam.blockers}")

    if drift is not None:
        lines.extend(
            [
                "",
                f"Legitimacy drift index: {drift.drift_index:.2f}",
                f"Failed surfaces: {[f.value for f in drift.failed_surfaces] or 'none'}",
            ]
        )
        if drift.over_concentration_signals:
            lines.append(f"  Over-concentration: {drift.over_concentration_signals}")
        if drift.competence_signals:
            lines.append(f"  Competence: {drift.competence_signals}")
        if drift.capture_signals:
            lines.append(f"  Capture: {drift.capture_signals}")

    lines.extend(["========================================", ""])
    return "\n".join(lines)


def render_legitimacy_panel(
    *,
    register: StewardshipLegitimacyRegister,
    exam: LegitimacyExamResult | None,
    drift: LegitimacyDriftState | None,
    stream: IO[str] | None = None,
) -> str:
    text = format_legitimacy_panel(register=register, exam=exam, drift=drift)
    out = stream if stream is not None else sys.stdout
    out.write(text)
    if stream is None:
        out.flush()
    return text
