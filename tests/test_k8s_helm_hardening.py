"""Offline tests for Platform Helm K8s hardening templates."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELM = ROOT / "deploy" / "platform" / "helm"


def test_helm_hardening_templates_present():
    required = [
        "templates/deployment.yaml",
        "templates/networkpolicy.yaml",
        "templates/secret.yaml",
        "templates/serviceaccount.yaml",
    ]
    for rel in required:
        assert (HELM / rel).is_file(), rel


def test_networkpolicy_declares_policy_types():
    text = (HELM / "templates/networkpolicy.yaml").read_text(encoding="utf-8")
    assert "NetworkPolicy" in text
    assert "policyTypes" in text


def test_secret_does_not_use_values_plaintext_key():
    values = (HELM / "values.yaml").read_text(encoding="utf-8")
    assert "masterApiKey: \"\"" in values or 'masterApiKey: ""' in values


def test_deployment_wires_secret_and_resources():
    text = (HELM / "templates/deployment.yaml").read_text(encoding="utf-8")
    assert "secretKeyRef" in text
    assert "resources:" in text
    assert "serviceAccountName" in text
