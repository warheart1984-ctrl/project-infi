"""Meta Architect Lawbook engine — constitutional spine for AAIS substrate."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any

from src.aais_composed_runtime import SPINE_PRECEDENCE

LAWBOOK_REL = Path("lawbook") / "META_ARCHITECT_LAWBOOK.md"
ENGINE_ID = "meta_law_engine"
ENGINE_VERSION = "meta_law_engine.v1"
CLAIM_LABELS = frozenset({"asserted", "proven", "rejected"})


class ConstitutionalLawbookError(RuntimeError):
    """Raised when constitutional lawbook is required but unavailable."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _lawbook_path() -> Path:
    return _repo_root() / LAWBOOK_REL


def _env_flag(name: str) -> bool:
    return str(os.environ.get(name) or "").strip() == "1"


def _invariant_check(
    *,
    invariant_id: str,
    title: str,
    core_principle: str,
    passed: bool,
    status: str,
    action: str,
    detail: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "invariant_id": invariant_id,
        "title": title,
        "core_principle": core_principle,
        "passed": bool(passed),
        "status": status,
        "action": action,
        "detail": detail,
        "metadata": dict(metadata or {}),
    }


def load_lawbook_text() -> str | None:
    path = _lawbook_path()
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def compute_lawbook_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def emit_constitutional_invariants(*, lawbook_text: str, repo_root: Path | None = None) -> list[dict[str, Any]]:
    root = repo_root or _repo_root()
    text_lower = lawbook_text.lower()
    readme = root / "README.md"
    readme_text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    stage2_doc = root / "docs" / "runtime" / "STAGE2_COPILOT_DOCTRINE.md"

    precedence_ok = "law > blueprint > contract > implementation > pipeline > tool" in text_lower
    proof_ok = "proof-of-reality" in text_lower or "proof of reality" in text_lower
    trust_ok = "trust bundle" in text_lower or "doctrine xi" in text_lower
    fail_closed_ok = "fail-safe" in text_lower or "fail closed" in text_lower or "no-bypass" in text_lower

    ma12_header = bool(re.search(r"how to start operations", readme_text, re.IGNORECASE))
    ma12_commands = bool(
        re.search(r"how to start operations", readme_text, re.IGNORECASE)
        and re.search(r"```", readme_text)
    )
    ma12_ok = readme.is_file() and ma12_header and ma12_commands

    ma13_ok = (
        "doctrine xiii" in text_lower or "ma-13" in text_lower
    ) and stage2_doc.is_file()

    return [
        _invariant_check(
            invariant_id="constitutional_precedence",
            title="Constitutional Precedence",
            core_principle="Law > Blueprint > Contract > Implementation > Pipeline > Tool",
            passed=precedence_ok and len(SPINE_PRECEDENCE) == 6,
            status="enforced" if precedence_ok else "blocked",
            action="spine_precedence_alignment",
            detail=(
                "Spine precedence matches Meta Architect Lawbook order."
                if precedence_ok
                else "Constitutional precedence text or spine alignment is missing."
            ),
            metadata={"spine_precedence": list(SPINE_PRECEDENCE)},
        ),
        _invariant_check(
            invariant_id="proof_of_reality",
            title="Proof-of-Reality",
            core_principle="No proof, no claim; asserted until evidence exists.",
            passed=proof_ok and all(label in text_lower for label in CLAIM_LABELS),
            status="enforced" if proof_ok else "blocked",
            action="claim_taxonomy_required",
            detail=(
                "Claim taxonomy and proof-of-reality doctrine are present."
                if proof_ok
                else "Proof-of-reality doctrine or claim labels are incomplete."
            ),
            metadata={"claim_labels": sorted(CLAIM_LABELS)},
        ),
        _invariant_check(
            invariant_id="trust_bundle",
            title="Simple Trust (Trust Bundle)",
            core_principle="Acceptance-critical claims require one-click verification bundles.",
            passed=trust_ok,
            status="enforced" if trust_ok else "blocked",
            action="trust_bundle_doctrine",
            detail=(
                "Doctrine XI trust bundle requirements are declared in the lawbook."
                if trust_ok
                else "Trust bundle doctrine is not discoverable in the lawbook."
            ),
        ),
        _invariant_check(
            invariant_id="fail_closed",
            title="Fail-Closed Posture",
            core_principle="Missing governance context stops action before trust can drift.",
            passed=fail_closed_ok,
            status="armed" if fail_closed_ok else "blocked",
            action="mandatory_no_bypass",
            detail=(
                "Fail-safe and no-bypass posture is declared in the lawbook."
                if fail_closed_ok
                else "Fail-closed or no-bypass posture is not declared."
            ),
        ),
        _invariant_check(
            invariant_id="ma_12_operational_primer",
            title="MA-12 Operational Primer Mandate",
            core_principle="Completed deliverables include README How to Start Operations.",
            passed=ma12_ok,
            status="enforced" if ma12_ok else "degraded",
            action="readme_operational_primer",
            detail=(
                "README contains How to Start Operations with command evidence."
                if ma12_ok
                else "README operational primer section or command block is incomplete."
            ),
            metadata={"readme_present": readme.is_file()},
        ),
        _invariant_check(
            invariant_id="ma_13_copilot_integrator",
            title="MA-13 Stage 2 Copilot Integrator Mandate",
            core_principle="Human origination, governed integration, bounded actuation.",
            passed=ma13_ok,
            status="enforced" if ma13_ok else "degraded",
            action="stage2_doctrine_reference",
            detail=(
                "Doctrine XIII and Stage 2 copilot doctrine reference are present."
                if ma13_ok
                else "MA-13 doctrine or Stage 2 specification reference is incomplete."
            ),
            metadata={"stage2_doc_present": stage2_doc.is_file()},
        ),
    ]


def resolve_constitutional_context() -> dict[str, Any]:
    """Load lawbook, compute digest, and emit constitutional invariant envelope."""
    path = _lawbook_path()
    text = load_lawbook_text()
    required = _env_flag("AAIS_REQUIRE_CONSTITUTIONAL_LAW")

    if text is None:
        return {
            "engine_id": ENGINE_ID,
            "engine_version": ENGINE_VERSION,
            "status": "required_missing" if required else "absent",
            "lawbook_present": False,
            "path": str(path.relative_to(_repo_root())).replace("\\", "/"),
            "digest": None,
            "precedence": list(SPINE_PRECEDENCE),
            "invariants": [],
            "claim_label": "asserted",
            "required": required,
        }

    invariants = emit_constitutional_invariants(lawbook_text=text)
    blocking = [item for item in invariants if not item["passed"] and item["status"] == "blocked"]
    status = "active" if not blocking else "degraded"

    return {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "status": status,
        "lawbook_present": True,
        "path": str(path.relative_to(_repo_root())).replace("\\", "/"),
        "digest": compute_lawbook_digest(text),
        "precedence": list(SPINE_PRECEDENCE),
        "invariants": invariants,
        "blocking_invariants": [item["invariant_id"] for item in blocking],
        "claim_label": "proven" if not blocking else "asserted",
        "required": required,
    }


def build_law_0_supreme_precedence_check(constitutional_context: dict[str, Any]) -> dict[str, Any]:
    """Emit law_0 check envelope when constitutional lawbook is present."""
    from src.project_infi_law import _law_check

    present = bool(constitutional_context.get("lawbook_present"))
    blocking = list(constitutional_context.get("blocking_invariants") or [])
    passed = present and not blocking
    return _law_check(
        law_id="law_0_supreme_precedence",
        title="Supreme Constitutional Precedence",
        core_principle="Meta Architect Lawbook governs precedence above Project Infi law without replacing it.",
        passed=passed if present else True,
        status=(
            "not_applicable"
            if not present
            else "enforced"
            if passed
            else "blocked"
        ),
        action="constitutional_spine_attachment",
        detail=(
            "Constitutional lawbook is absent; Project Infi law proceeds without supreme precedence attachment."
            if not present
            else "Constitutional spine is active and precedence invariants passed."
            if passed
            else f"Constitutional spine blocked: {', '.join(blocking)}."
        ),
        metadata={
            "digest": constitutional_context.get("digest"),
            "precedence": constitutional_context.get("precedence"),
            "status": constitutional_context.get("status"),
        },
    )


def bootstrap_constitutional_lawbook() -> dict[str, Any]:
    """Bootstrap hook — refuse start when lawbook is required but missing."""
    context = resolve_constitutional_context()
    if context["status"] == "required_missing":
        raise ConstitutionalLawbookError(
            f"Constitutional lawbook required but missing at {context['path']}"
        )

    try:
        from src.aais_ul_substrate import attach_ul_substrate

        attach_ul_substrate(
            {
                "constitutional_layer": {
                    "status": context["status"],
                    "digest": context.get("digest"),
                    "lawbook_present": context.get("lawbook_present"),
                }
            }
        )
    except Exception:
        pass

    return context
