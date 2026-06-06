#!/usr/bin/env python3
"""Offline validation for Platform Membrane Helm hardening templates."""

from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_TEMPLATES = (
    "templates/deployment.yaml",
    "templates/networkpolicy.yaml",
    "templates/secret.yaml",
    "templates/serviceaccount.yaml",
)

REQUIRED_SNIPPETS = {
    "templates/networkpolicy.yaml": ("NetworkPolicy", "policyTypes"),
    "templates/secret.yaml": ("kind: Secret", "PLATFORM_MASTER_API_KEY"),
    "templates/deployment.yaml": ("resources:", "serviceAccountName"),
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    helm = root / "deploy" / "platform" / "helm"
    findings: list[str] = []

    if not (helm / "Chart.yaml").is_file():
        findings.append("missing deploy/platform/helm/Chart.yaml")

    for rel in REQUIRED_TEMPLATES:
        path = helm / rel
        if not path.is_file():
            findings.append(f"missing {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in REQUIRED_SNIPPETS.get(rel, ()):
            if snippet not in text:
                findings.append(f"{rel} missing snippet: {snippet}")

    values = helm / "values.yaml"
    if values.is_file():
        vt = values.read_text(encoding="utf-8")
        if "change-me" in vt.lower() and "masterApiKey" in vt:
            findings.append("values.yaml must not embed production masterApiKey plaintext")

    if findings:
        print("[validate-k8s-helm-manifest] FAIL")
        for item in findings:
            print(f"  - {item}")
        return 1

    print("[validate-k8s-helm-manifest] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
