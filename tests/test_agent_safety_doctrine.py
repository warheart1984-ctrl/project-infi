from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "validate-agent-safety-doctrine.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_agent_safety_doctrine", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _write_manifest(path: Path, **overrides: object) -> Path:
    manifest = {
        "agent_safety_doctrine_version": "agent_safety_doctrine.v1",
        "change_id": "ASD-001",
        "claim_label": "proven",
        "authority_chain": ["Law", "Blueprint", "Contract", "Implementation", "Pipeline", "Tool"],
        "blueprint_refs": ["document/blueprints/PROJECT_BLUEPRINTS_MASTER.md"],
        "change_boundary": {
            "what_changed": "Added an agent safety validator.",
            "why_changed": "Prevent implementation drift from bypassing lawbook authority.",
            "evidence_refs": ["tests/test_agent_safety_doctrine.py"],
            "assumptions": ["JSON manifests are the enforcement input."],
            "reversal": "Remove the validator script and CI step.",
        },
        "prohibited_actions": {
            "rewrite_architecture_without_blueprint_approval": False,
            "delete_governance_artifacts": False,
            "remove_validation_gates": False,
            "weaken_tests_to_pass": False,
            "replace_determinism_with_convenience": False,
            "introduce_hidden_dependencies": False,
            "claim_completion_without_proof": False,
        },
        "uncertainty": {
            "level": "low",
            "authority_delta": "unchanged",
            "resolution_path": "Escalate to Meta Architect if blueprint authority is disputed.",
        },
    }
    manifest.update(overrides)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def test_valid_agent_change_manifest_passes(tmp_path: Path):
    validator = _load_validator()
    manifest_path = _write_manifest(tmp_path / "valid.json")

    findings, errors = validator.validate_manifest(manifest_path)

    assert errors == []
    assert any("passed" in finding.message for finding in findings)


def test_manifest_rejects_missing_evidence_and_reversal(tmp_path: Path):
    validator = _load_validator()
    manifest_path = _write_manifest(
        tmp_path / "invalid.json",
        change_boundary={
            "what_changed": "Changed governance.",
            "why_changed": "Convenience.",
            "evidence_refs": [],
            "assumptions": [],
            "reversal": "",
        },
    )

    _findings, errors = validator.validate_manifest(manifest_path)

    messages = [error.message for error in errors]
    assert any("change_boundary.evidence_refs" in message for message in messages)
    assert any("change_boundary.assumptions" in message for message in messages)
    assert any("change_boundary.reversal" in message for message in messages)


def test_manifest_rejects_prohibited_agent_drift(tmp_path: Path):
    validator = _load_validator()
    manifest_path = _write_manifest(
        tmp_path / "drift.json",
        prohibited_actions={
            "rewrite_architecture_without_blueprint_approval": False,
            "delete_governance_artifacts": False,
            "remove_validation_gates": True,
            "weaken_tests_to_pass": False,
            "replace_determinism_with_convenience": False,
            "introduce_hidden_dependencies": False,
            "claim_completion_without_proof": False,
        },
    )

    _findings, errors = validator.validate_manifest(manifest_path)

    assert any("remove_validation_gates" in error.message for error in errors)


def test_manifest_blocks_authority_increase_under_high_uncertainty(tmp_path: Path):
    validator = _load_validator()
    manifest_path = _write_manifest(
        tmp_path / "uncertain.json",
        uncertainty={
            "level": "high",
            "authority_delta": "increased",
            "resolution_path": "Proceed anyway.",
        },
    )

    _findings, errors = validator.validate_manifest(manifest_path)

    assert any("authority may not increase under high uncertainty" in error.message for error in errors)
