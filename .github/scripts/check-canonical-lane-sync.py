#!/usr/bin/env python3
"""Verify src/cog_runtime is the sole editable source; bundle copy must match."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


FORBIDDEN_TRACKED_PREFIXES = (
    "AAIS-main/",
    "Aris--main/",
    "Project-Infinity-main/",
    "aris/",
    "opt/cogos/",
)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    path: str
    message: str

    def render(self) -> str:
        return f"[ERROR] {self.rule_id}: {self.message} | path={self.path}"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_ls_files(repo_root: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _check_forbidden_tracked(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel in _git_ls_files(repo_root):
        norm = rel.replace("\\", "/")
        for prefix in FORBIDDEN_TRACKED_PREFIXES:
            if norm == prefix.rstrip("/") or norm.startswith(prefix):
                findings.append(
                    Finding(
                        rule_id="canonical.forbidden_tracked",
                        path=norm,
                        message=f"git tracks file under non-canonical prefix '{prefix}'",
                    )
                )
                break
    return findings


def _check_bundle_sync(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    canonical = repo_root / "src" / "cog_runtime"
    if not canonical.is_dir():
        findings.append(
            Finding(
                rule_id="canonical.missing_source",
                path=str(canonical),
                message="canonical src/cog_runtime directory missing",
            )
        )
        return findings

    build_py = repo_root / "scripts" / "cogos" / "build_synthetic_mind_bundle.py"
    if not build_py.is_file():
        findings.append(
            Finding(
                rule_id="canonical.missing_builder",
                path=str(build_py),
                message="bundle builder script missing",
            )
        )
        return findings

    with tempfile.TemporaryDirectory(prefix="canonical-lane-sync-") as tmp:
        bundle_dir = Path(tmp) / "bundle"
        proc = subprocess.run(
            [sys.executable, str(build_py), str(bundle_dir)],
            cwd=str(repo_root),
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            findings.append(
                Finding(
                    rule_id="canonical.bundle_build_failed",
                    path=str(build_py),
                    message=proc.stderr or proc.stdout or "bundle build failed",
                )
            )
            return findings

        bundle_cog = bundle_dir / "opt" / "cogos" / "runtime" / "src" / "cog_runtime"
        for src_py in sorted(canonical.rglob("*.py")):
            rel = src_py.relative_to(canonical).as_posix()
            bundle_py = bundle_cog / rel
            if not bundle_py.is_file():
                findings.append(
                    Finding(
                        rule_id="canonical.bundle_missing_module",
                        path=rel,
                        message="canonical module absent from fresh bundle",
                    )
                )
                continue
            if _sha256(src_py) != _sha256(bundle_py):
                findings.append(
                    Finding(
                        rule_id="canonical.bundle_hash_mismatch",
                        path=rel,
                        message="bundle cog_runtime copy does not match canonical src",
                    )
                )
    return findings


def scan(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_check_forbidden_tracked(repo_root))
    findings.extend(_check_bundle_sync(repo_root))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check canonical runtime lane sync.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=["warn", "fail"], default="warn")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    findings = scan(repo_root)

    for finding in findings:
        level = "WARN" if args.mode == "warn" else "ERROR"
        print(f"[{level}] {finding.rule_id}: {finding.message} | path={finding.path}")

    print(f"Canonical lane sync: violations={len(findings)}, mode={args.mode}")
    if findings and args.mode == "fail":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
