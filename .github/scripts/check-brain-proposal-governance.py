#!/usr/bin/env python3
"""Brain proposal / session / deliberation governance gate (structure layer)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "docs/contracts/BRAIN_PROPOSAL_CONTRACT.md",
    "docs/contracts/BRAIN_SESSION_CONTRACT.md",
    "docs/contracts/BRAIN_DELIBERATION_CONTRACT.md",
    "docs/proof/platform/BRAIN_SCORING_SESSIONS_V1_PROOF.md",
    "docs/proof/platform/BRAIN_DELIBERATION_V1_PROOF.md",
    "docs/operators/OPERATOR_WORKFLOW_SKILLS.md",
    "governance/fixtures/brain/brain_proposal_routing_sample.v1.json",
    "governance/fixtures/brain/brain_session_sample.v1.json",
    "governance/fixtures/brain/brain_deliberation_sample.v1.json",
]

FORBIDDEN_AUTHORITY_KEYS = ("execute", "authorized", "approved", "tool_call", "shell_command")
FORBIDDEN_STATUS = re.compile(r'"status"\s*:\s*"(?!proposal_only)[^"]+"')


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_proposal_only(doc: dict, label: str, errors: list[str]) -> None:
    status = str(doc.get("status") or "")
    if status != "proposal_only":
        errors.append(f"{label}:status must be proposal_only, got {status!r}")

    serialized = json.dumps(doc)
    for key in FORBIDDEN_AUTHORITY_KEYS:
        if f'"{key}": true' in serialized:
            errors.append(f"{label}:forbidden authority key {key}=true")


def _validate_proposal_fixture(doc: dict, errors: list[str]) -> None:
    _assert_proposal_only(doc, "proposal_fixture", errors)
    if doc.get("brain_proposal_version") != "brain_proposal.v1":
        errors.append("proposal_fixture:invalid brain_proposal_version")

    routing = doc.get("routing") or {}
    organs = list(routing.get("organ_rankings") or [])
    chains = list(routing.get("chain_rankings") or [])
    if organs and organs[0].get("family_id") != "knowledge_work":
        errors.append("proposal_fixture:expected knowledge_work top organ ranking")
    if chains and chains[0].get("workflow_id") != "research_brief":
        errors.append("proposal_fixture:expected research_brief top chain ranking")


def _validate_session_fixture(doc: dict, errors: list[str]) -> None:
    if doc.get("brain_session_version") != "brain_session.v1":
        errors.append("session_fixture:invalid brain_session_version")
    if doc.get("operator_decision") not in {"pending", "accepted", "rejected", "deferred"}:
        errors.append("session_fixture:invalid operator_decision")
    proposals = list(doc.get("proposals") or [])
    if not proposals:
        errors.append("session_fixture:missing proposals")
    for proposal in proposals:
        _assert_proposal_only(proposal, "session_fixture.proposal", errors)


def _validate_deliberation_fixture(doc: dict, errors: list[str]) -> None:
    _assert_proposal_only(doc, "deliberation_fixture", errors)
    if doc.get("brain_deliberation_version") != "brain_deliberation.v1":
        errors.append("deliberation_fixture:invalid brain_deliberation_version")
    stages = [str(item.get("stage_kind") or "") for item in (doc.get("stage_chain") or [])]
    if stages[:2] != ["options", "tradeoffs"] or "commit" not in stages:
        errors.append("deliberation_fixture:invalid stage_chain order")


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (REPO / rel).is_file():
            errors.append(f"missing:{rel}")

    readme = (REPO / "README.md").read_text(encoding="utf-8", errors="replace")
    if "Operator Workflow Skills (Infinity 1)" not in readme:
        errors.append("readme:missing Operator Workflow Skills section")

    for rel in (
        "docs/contracts/BRAIN_PROPOSAL_CONTRACT.md",
        "docs/contracts/BRAIN_DELIBERATION_CONTRACT.md",
    ):
        text = (REPO / rel).read_text(encoding="utf-8", errors="replace")
        if "proposal_only" not in text:
            errors.append(f"contract:{rel}:missing proposal_only invariant")
        if FORBIDDEN_STATUS.search(text):
            errors.append(f"contract:{rel}:contains non-proposal_only status example")

    proposal = _load_json(REPO / "governance/fixtures/brain/brain_proposal_routing_sample.v1.json")
    session = _load_json(REPO / "governance/fixtures/brain/brain_session_sample.v1.json")
    deliberation = _load_json(REPO / "governance/fixtures/brain/brain_deliberation_sample.v1.json")

    _validate_proposal_fixture(proposal, errors)
    _validate_session_fixture(session, errors)
    _validate_deliberation_fixture(deliberation, errors)

    bundles = _load_json(REPO / "governance/workflow_plugin_bundles.v1.json")
    bundle_ids = {
        str(item.get("workflow_id"))
        for item in (bundles.get("bundles") or [])
        if item.get("workflow_id")
    }
    top_chain = str(
        ((proposal.get("routing") or {}).get("suggested_workflow_chain") or {}).get("workflow_id") or ""
    )
    if top_chain and top_chain not in bundle_ids:
        errors.append(f"proposal_fixture:unknown workflow_id:{top_chain}")

    if errors:
        print("[brain-proposal-gate] FAIL")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("[brain-proposal-gate] PASS (contracts + fixtures + authority invariants)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
