"""CRK-T1 boundary — kernel mutations go through canonical transitions."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PATH = REPO_ROOT / "src" / "continuity" / "constitutional_runtime.py"

CANONICAL_RUNTIME_METHODS = {
    "propose_decision",
    "approve_decision",
    "allocate_resources_for_decision",
    "execute_decision",
    "advance_epoch",
}


def test_constitutional_runtime_public_transitions() -> None:
    tree = ast.parse(RUNTIME_PATH.read_text(encoding="utf-8"))
    runtime_class = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "ConstitutionalRuntime"
    )
    public_methods = {
        node.name
        for node in runtime_class.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    assert CANONICAL_RUNTIME_METHODS.issubset(public_methods)


def test_check_crk1_invariants_exists() -> None:
    from src.continuity.constitutional_runtime import check_crk1_invariants

    report = check_crk1_invariants()
    assert report["compliant"] is True
    assert report["objects_ok"] is True
    assert report["contracts_ok"] is True
    assert report["transitions_ok"] is True
