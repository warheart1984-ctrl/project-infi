"""CRK-1 / CRK-T1 static compliance helpers."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CANONICAL_OBJECTS = frozenset(
    {
        "IdentityObject",
        "EvidenceObject",
        "DecisionObject",
        "ResourceObject",
        "OutcomeObject",
    }
)

SCHEMA_TITLE_ALIASES = {"EvidenceRecord": "EvidenceObject"}

CANONICAL_CONTRACTS = frozenset(
    {
        "EvidenceContract",
        "GovernanceContract",
        "ResourceContract",
        "RuntimeContract",
    }
)

CANONICAL_RUNTIME_METHODS = frozenset(
    {
        "propose_decision",
        "approve_decision",
        "allocate_resources_for_decision",
        "execute_decision",
        "advance_epoch",
    }
)

FORBIDDEN_INVARIANT_OBJECT_PATTERNS = (
    re.compile(r"\bCITObject\b"),
    re.compile(r"\bMITObject\b"),
    re.compile(r"\bEITObject\b"),
    re.compile(r"\bAITObject\b"),
    re.compile(r"\bSITObject\b"),
    re.compile(r"\bGITObject\b"),
    re.compile(r"\bPITObject\b"),
    re.compile(r"\bAttentionObject\b"),
)


def scan_schema_titles() -> set[str]:
    titles: set[str] = set()
    schema_dir = REPO_ROOT / "fixtures" / "continuity"
    for path in schema_dir.glob("*.schema.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        title = str(payload.get("title") or "")
        if title:
            titles.add(SCHEMA_TITLE_ALIASES.get(title, title))
    runtime_path = REPO_ROOT / "src" / "continuity" / "identity_object.py"
    if runtime_path.is_file() and "class IdentityObject" in runtime_path.read_text(encoding="utf-8"):
        titles.add("IdentityObject")
    return titles


def scan_contract_classes() -> set[str]:
    found: set[str] = set()
    runtime_path = REPO_ROOT / "src" / "continuity" / "constitutional_runtime.py"
    tree = ast.parse(runtime_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in CANONICAL_CONTRACTS:
            found.add(node.name)
    resource_path = REPO_ROOT / "src" / "continuity" / "resource_contract.py"
    if resource_path.is_file():
        tree = ast.parse(resource_path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "ResourceContract":
                found.add(node.name)
    return found


def scan_extra_object_names() -> set[str]:
    extra: set[str] = set()
    for path in (REPO_ROOT / "fixtures" / "continuity").glob("*.schema.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        title = str(payload.get("title") or "")
        canonical = SCHEMA_TITLE_ALIASES.get(title, title)
        if canonical.endswith("Object") and canonical not in CANONICAL_OBJECTS:
            extra.add(canonical)
    return extra


def scan_forbidden_invariant_objects() -> list[str]:
    violations: list[str] = []
    scan_roots = [
        REPO_ROOT / "src" / "continuity",
        REPO_ROOT / "fixtures" / "continuity",
    ]
    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix not in {".py", ".json"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in FORBIDDEN_INVARIANT_OBJECT_PATTERNS:
                if pattern.search(text):
                    violations.append(f"{path.relative_to(REPO_ROOT)}: {pattern.pattern}")
    return sorted(set(violations))


def scan_fitness_routes() -> list[str]:
    routes_path = REPO_ROOT / "src" / "constitutional_cockpit_routes.py"
    text = routes_path.read_text(encoding="utf-8")
    required = (
        "/api/fitness/comprehension/",
        "/api/fitness/meaning/",
        "/api/fitness/evidence/",
        "/api/fitness/outcome/",
        "/api/fitness/attention",
    )
    return [route for route in required if route not in text]


def check_objects() -> tuple[set[str], set[str]]:
    found = scan_schema_titles()
    missing = set(CANONICAL_OBJECTS) - found
    extra = {name for name in found if name.endswith("Object") and name not in CANONICAL_OBJECTS}
    extra |= scan_extra_object_names()
    return missing, extra


def check_contracts() -> set[str]:
    found = scan_contract_classes()
    return set(CANONICAL_CONTRACTS) - found


def check_runtime_methods() -> set[str]:
    runtime_path = REPO_ROOT / "src" / "continuity" / "constitutional_runtime.py"
    tree = ast.parse(runtime_path.read_text(encoding="utf-8"))
    runtime_class = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "ConstitutionalRuntime"
    )
    public_methods = {
        node.name
        for node in runtime_class.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    return set(CANONICAL_RUNTIME_METHODS) - public_methods


def run_static_compliance_report() -> dict[str, object]:
    missing_objects, extra_objects = check_objects()
    missing_contracts = check_contracts()
    missing_transitions = check_runtime_methods()
    return {
        "compliant": not (
            missing_objects or extra_objects or missing_contracts or missing_transitions
        ),
        "missing_objects": sorted(missing_objects),
        "extra_objects": sorted(extra_objects),
        "missing_contracts": sorted(missing_contracts),
        "missing_transitions": sorted(missing_transitions),
        "invariant_object_violations": scan_forbidden_invariant_objects(),
        "fitness_route_gaps": scan_fitness_routes(),
    }
