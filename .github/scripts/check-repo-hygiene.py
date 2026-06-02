#!/usr/bin/env python3
"""Validate repository workspace hygiene against REPO_HYGIENE_MANIFEST.json."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


MANIFEST_REL = "docs/audit/REPO_HYGIENE_MANIFEST.json"


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    path: str
    message: str

    def render(self) -> str:
        level = "WARN" if self.severity == "warn" else "ERROR"
        return f"[{level}] {self.rule_id}: {self.message} | path={self.path}"


def _load_manifest(repo_root: Path) -> dict:
    path = repo_root / MANIFEST_REL
    if not path.is_file():
        raise FileNotFoundError(f"missing hygiene manifest: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("hygiene manifest root must be an object")
    return data


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


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _path_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def _root_children(repo_root: Path) -> list[Path]:
    children: list[Path] = []
    try:
        iterator = repo_root.iterdir()
    except OSError:
        return children
    for child in iterator:
        try:
            child.stat()
        except OSError:
            continue
        children.append(child)
    return children


def _check_forbidden_root_names(repo_root: Path, manifest: dict) -> list[Finding]:
    findings: list[Finding] = []
    forbidden = set(manifest.get("forbidden_root_names") or [])
    for child in _root_children(repo_root):
        if child.name in forbidden:
            findings.append(
                Finding(
                    rule_id="hygiene.forbidden_root_name",
                    severity="error",
                    path=child.as_posix(),
                    message=f"forbidden root entry '{child.name}' — remove or relocate per ROOT_STRUCTURE_AUDIT",
                )
            )
    return findings


def _check_forbidden_root_globs(repo_root: Path, manifest: dict) -> list[Finding]:
    findings: list[Finding] = []
    patterns = list(manifest.get("forbidden_root_globs") or [])
    for child in _root_children(repo_root):
        if not child.is_file():
            continue
        for pattern in patterns:
            if fnmatch.fnmatch(child.name, pattern):
                findings.append(
                    Finding(
                        rule_id="hygiene.forbidden_root_glob",
                        severity="warn",
                        path=child.as_posix(),
                        message=f"root artifact '{child.name}' matches forbidden pattern '{pattern}'",
                    )
                )
                break
    return findings


def _check_whitespace_poison_dirs(repo_root: Path, manifest: dict) -> list[Finding]:
    findings: list[Finding] = []
    markers = set(manifest.get("poison_dir_markers") or [])
    for child in _root_children(repo_root):
        name = child.name
        if not name or name.isspace():
            findings.append(
                Finding(
                    rule_id="hygiene.poison_dir",
                    severity="error",
                    path=child.as_posix(),
                    message="root child has empty or whitespace-only name — likely accidental bundle staging",
                )
            )
            continue
        if not child.is_dir():
            continue
        for marker in markers:
            if _path_exists(child / marker) and child.parent == repo_root:
                findings.append(
                    Finding(
                        rule_id="hygiene.poison_dir",
                        severity="error",
                        path=(child / marker).as_posix(),
                        message=f"unexpected '{marker}' under repo root — bundle mirror outside allowed paths",
                    )
                )
    return findings


def _check_forbidden_tracked(repo_root: Path, manifest: dict) -> list[Finding]:
    findings: list[Finding] = []
    prefixes = list(manifest.get("forbidden_tracked_prefixes") or [])
    for rel in _git_ls_files(repo_root):
        norm = rel.replace("\\", "/")
        for prefix in prefixes:
            if norm == prefix.rstrip("/") or norm.startswith(prefix):
                findings.append(
                    Finding(
                        rule_id="hygiene.forbidden_tracked",
                        severity="error",
                        path=norm,
                        message=f"git tracks file under forbidden prefix '{prefix}'",
                    )
                )
                break
    return findings


def _check_local_work_dirs(repo_root: Path, manifest: dict) -> list[Finding]:
    findings: list[Finding] = []
    for name in manifest.get("local_work_dirs") or []:
        path = repo_root / name
        if _path_exists(path):
            findings.append(
                Finding(
                    rule_id="hygiene.local_work_dir",
                    severity="warn",
                    path=path.as_posix(),
                    message="local work directory present — safe to delete when not in active use",
                )
            )
    return findings


def _check_stale_payload_runtime(repo_root: Path, manifest: dict) -> list[Finding]:
    findings: list[Finding] = []
    rel = str(manifest.get("stale_payload_runtime") or "").strip()
    canonical_rel = str(manifest.get("canonical_cog_runtime") or "src/cog_runtime").strip()
    if not rel:
        return findings

    payload_runtime = repo_root / rel
    canonical = repo_root / canonical_rel
    if not payload_runtime.is_dir() or not canonical.is_dir():
        return findings

    try:
        build_py = repo_root / "scripts" / "cogos" / "build_synthetic_mind_bundle.py"
        if not build_py.is_file():
            return findings

        with tempfile.TemporaryDirectory(prefix="repo-hygiene-bundle-") as tmp:
            bundle_dir = Path(tmp) / "bundle"
            proc = subprocess.run(
                [sys.executable, str(build_py), str(bundle_dir)],
                cwd=str(repo_root),
                text=True,
                capture_output=True,
                check=False,
            )
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr or proc.stdout or "bundle build failed")

            bundle_cog = bundle_dir / "opt" / "cogos" / "runtime" / "src" / "cog_runtime"
            mismatches: list[str] = []
            for src_py in sorted(canonical.rglob("*.py")):
                rel_py = src_py.relative_to(canonical).as_posix()
                bundle_py = bundle_cog / rel_py
                payload_py = payload_runtime / rel_py
                if not bundle_py.is_file():
                    continue
                expected = _sha256_file(bundle_py)
                if payload_py.is_file() and _sha256_file(payload_py) != expected:
                    mismatches.append(rel_py)
                elif not payload_py.is_file():
                    mismatches.append(f"{rel_py} (missing in payload)")
            if mismatches:
                sample = ", ".join(mismatches[:5])
                suffix = "..." if len(mismatches) > 5 else ""
                findings.append(
                    Finding(
                        rule_id="hygiene.stale_payload_runtime",
                        severity="warn",
                        path=payload_runtime.as_posix(),
                        message=(
                            f"payload cog_runtime diverges from fresh bundle ({len(mismatches)} files): "
                            f"{sample}{suffix}"
                        ),
                    )
                )
    except Exception as exc:  # noqa: BLE001
        findings.append(
            Finding(
                rule_id="hygiene.stale_payload_runtime",
                severity="warn",
                path=payload_runtime.as_posix(),
                message=f"could not compare payload runtime to bundle: {exc}",
            )
        )
    return findings


def scan_repo(repo_root: Path, *, skip_bundle_compare: bool = False) -> list[Finding]:
    manifest = _load_manifest(repo_root)
    findings: list[Finding] = []
    findings.extend(_check_forbidden_root_names(repo_root, manifest))
    findings.extend(_check_forbidden_root_globs(repo_root, manifest))
    findings.extend(_check_whitespace_poison_dirs(repo_root, manifest))
    findings.extend(_check_forbidden_tracked(repo_root, manifest))
    findings.extend(_check_local_work_dirs(repo_root, manifest))
    if not skip_bundle_compare:
        findings.extend(_check_stale_payload_runtime(repo_root, manifest))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check repository workspace hygiene.")
    parser.add_argument("--repo-root", default=".", help="Repository root (default: cwd)")
    parser.add_argument("--mode", choices=["warn", "fail"], default="warn")
    parser.add_argument("--output", default="", help="Optional JSON report path")
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument(
        "--skip-bundle-compare",
        action="store_true",
        help="Skip stale payload runtime hash comparison (faster CI unit tests)",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    findings = scan_repo(repo_root, skip_bundle_compare=args.skip_bundle_compare)

    errors = [f for f in findings if f.severity == "error"]
    warns = [f for f in findings if f.severity == "warn"]

    if not args.summary_only or findings:
        for finding in findings:
            print(finding.render())

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "mode": args.mode,
        "manifest": MANIFEST_REL,
        "violations": len(errors),
        "warnings": len(warns),
        "findings": [asdict(f) for f in findings],
    }

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"Repo hygiene check: errors={len(errors)}, warnings={len(warns)}, mode={args.mode}"
    )

    if errors:
        return 0 if args.mode == "warn" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
