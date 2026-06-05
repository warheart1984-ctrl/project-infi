"""Human-AI Co-Collaboration Charter membrane — turn ingress collaboration law."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

CHARTER_REL = Path("lawbook") / "HUMAN_AI_CO_COLLABORATION_CHARTER.md"
MEMBRANE_ID = "collaboration_membrane"
MEMBRANE_VERSION = "collaboration_membrane.v1"
CLAIM_LABELS = frozenset({"asserted", "proven", "rejected"})


class CollaborationCharterError(RuntimeError):
    """Raised when collaboration charter is required but unavailable."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _charter_path() -> Path:
    return _repo_root() / CHARTER_REL


def _env_flag(name: str) -> bool:
    return str(os.environ.get(name) or "").strip() == "1"


def _membrane_check(
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


def load_charter_text() -> str | None:
    path = _charter_path()
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def compute_charter_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def emit_collaboration_invariants(
    *,
    charter_text: str,
    details: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    payload = dict(details or {})
    text_lower = charter_text.lower()

    claim_label = str(payload.get("claim_label") or "asserted").strip().lower()
    claim_ok = claim_label in CLAIM_LABELS

    human_authority_ok = "humans hold final authority" in text_lower or "human authority" in text_lower
    override_ok = "humans may override" in text_lower or "human override" in text_lower
    epistemic_ok = "epistemic" in text_lower and ("escalate" in text_lower or "ambiguity" in text_lower)
    reversibility_ok = "reversible" in text_lower or "undoable" in text_lower

    escalate_requested = bool(payload.get("epistemic_escalation_required"))
    escalate_ack = bool(payload.get("epistemic_escalation_acknowledged"))
    epistemic_passed = epistemic_ok and (not escalate_requested or escalate_ack)

    reversible_requested = payload.get("reversible")
    if reversible_requested is None:
        reversible_passed = reversibility_ok
    else:
        reversible_passed = reversibility_ok and bool(reversible_requested)

    return [
        _membrane_check(
            invariant_id="claim_labels",
            title="Claim Label Taxonomy",
            core_principle="Every AI output carries asserted, proven, or rejected claim labels.",
            passed=claim_ok,
            status="enforced" if claim_ok else "blocked",
            action="claim_label_validation",
            detail=(
                f"Claim label {claim_label!r} is admissible."
                if claim_ok
                else f"Claim label {claim_label!r} is not admissible."
            ),
            metadata={"claim_label": claim_label, "allowed": sorted(CLAIM_LABELS)},
        ),
        _membrane_check(
            invariant_id="human_authority",
            title="Human Final Authority",
            core_principle="Humans decide; AIs advise under law, subordinate to the Meta Architect Lawbook.",
            passed=human_authority_ok,
            status="enforced" if human_authority_ok else "blocked",
            action="human_authority_posture",
            detail=(
                "Charter declares human final authority and AI subordination to law."
                if human_authority_ok
                else "Human authority posture is not declared in the charter."
            ),
        ),
        _membrane_check(
            invariant_id="override",
            title="Human Override Path",
            core_principle="Humans may override AI instantly; debt is tracked when blueprint breaks.",
            passed=override_ok,
            status="enforced" if override_ok else "blocked",
            action="human_override_posture",
            detail=(
                "Charter declares instant human override without ceremony."
                if override_ok
                else "Human override posture is not declared in the charter."
            ),
            metadata={"override_acknowledged": bool(payload.get("human_override_acknowledged", True))},
        ),
        _membrane_check(
            invariant_id="epistemic_escalation",
            title="Epistemic Escalation",
            core_principle="Ambiguity, conflict, or elevated risk must escalate rather than silently assume.",
            passed=epistemic_passed,
            status="enforced" if epistemic_passed else "blocked",
            action="epistemic_boundary_escalation",
            detail=(
                "Epistemic escalation posture is satisfied for this turn."
                if epistemic_passed
                else "Turn requires epistemic escalation acknowledgment before admission."
            ),
            metadata={
                "escalation_required": escalate_requested,
                "escalation_acknowledged": escalate_ack,
            },
        ),
        _membrane_check(
            invariant_id="reversibility",
            title="Reversible Collaboration",
            core_principle="AI actions remain undoable; collaboration must not silently drift.",
            passed=reversible_passed,
            status="enforced" if reversible_passed else "blocked",
            action="reversibility_posture",
            detail=(
                "Reversibility posture is declared and satisfied for this turn."
                if reversible_passed
                else "Reversibility requirements are not satisfied for this turn."
            ),
            metadata={"reversible": payload.get("reversible")},
        ),
    ]


def resolve_collaboration_context(*, details: dict[str, Any] | None = None) -> dict[str, Any]:
    path = _charter_path()
    text = load_charter_text()
    required = _env_flag("AAIS_REQUIRE_COLLABORATION_CHARTER")

    if text is None:
        return {
            "membrane_id": MEMBRANE_ID,
            "membrane_version": MEMBRANE_VERSION,
            "status": "required_missing" if required else "absent",
            "charter_present": False,
            "path": str(path.relative_to(_repo_root())).replace("\\", "/"),
            "digest": None,
            "invariants": [],
            "admitted": not required,
            "claim_label": "asserted",
            "required": required,
        }

    invariants = emit_collaboration_invariants(charter_text=text, details=details)
    blocking = [item for item in invariants if not item["passed"]]
    admitted = not blocking

    return {
        "membrane_id": MEMBRANE_ID,
        "membrane_version": MEMBRANE_VERSION,
        "status": "active" if admitted else "blocked",
        "charter_present": True,
        "path": str(path.relative_to(_repo_root())).replace("\\", "/"),
        "digest": compute_charter_digest(text),
        "invariants": invariants,
        "blocking_invariants": [item["invariant_id"] for item in blocking],
        "admitted": admitted,
        "claim_label": "proven" if admitted else "asserted",
        "required": required,
    }


def evaluate_turn_collaboration_membrane(
    *,
    session_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate charter invariants at turn ingress."""
    payload = dict(details or {})
    if session_id and not payload.get("session_id"):
        payload["session_id"] = session_id
    context = resolve_collaboration_context(details=payload)
    context["surface"] = "chat_turn"
    return context


def bootstrap_collaboration_charter() -> dict[str, Any]:
    """Bootstrap hook — verify charter readiness for governed harness."""
    context = resolve_collaboration_context()
    if context["status"] == "required_missing":
        raise CollaborationCharterError(
            f"Collaboration charter required but missing at {context['path']}"
        )

    try:
        from src.aais_ul_substrate import attach_ul_substrate

        attach_ul_substrate(
            {
                "collaboration_membrane": {
                    "status": context["status"],
                    "digest": context.get("digest"),
                    "charter_present": context.get("charter_present"),
                }
            }
        )
    except Exception:
        pass

    return context
