#!/usr/bin/env python3
"""Validate command surfaces against top-level repo safety prohibitions."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SURFACES = [
    ".github/workflows",
    ".github/scripts",
    "Makefile",
]

SCAN_EXTENSIONS = {".yml", ".yaml", ".sh", ".bash", ".zsh", ".ps1", ".mk"}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    regex: re.Pattern[str]
    message: str


@dataclass(frozen=True)
class Finding:
    path: Path
    line_no: int
    line: str
    rule: Rule

    def render(self, repo_root: Path) -> str:
        rel = self.path.relative_to(repo_root)
        return (
            f"[ERROR] {rel}:{self.line_no} {self.rule.rule_id}: {self.rule.message} | "
            f"line='{self.line.strip()}'"
        )


RULES = [
    Rule(
        rule_id="repo_safety.git_clean",
        regex=re.compile(r"\bgit\s+clean\s+-f(?:dx|d\b|x)\b"),
        message="Destructive git clean is prohibited without explicit user approval.",
    ),
    Rule(
        rule_id="repo_safety.git_reset_hard",
        regex=re.compile(r"\bgit\s+reset\s+--hard\b"),
        message="git reset --hard is prohibited without explicit user approval.",
    ),
    Rule(
        rule_id="repo_safety.rm_rf_root",
        regex=re.compile(r"\brm\s+-rf\s+([\"'])?/(?:\1|\s|$)"),
        message="rm -rf on root path is prohibited.",
    ),
    Rule(
        rule_id="repo_safety.rm_rf_wildcard",
        regex=re.compile(r"\brm\s+-rf\s+([\"'])?\*(?:\1|\s|$)"),
        message="rm -rf wildcard at current directory scope is prohibited.",
    ),
    Rule(
        rule_id="repo_safety.rm_rf_dot",
        regex=re.compile(r"\brm\s+-rf\s+([\"'])?\.(?:\1|\s|$)"),
        message="rm -rf . is prohibited.",
    ),
    Rule(
        rule_id="repo_safety.rm_rf_dotdot",
        regex=re.compile(r"\brm\s+-rf\s+([\"'])?\.\.(?:\1|\s|$)"),
        message="rm -rf .. is prohibited.",
    ),
]


def _iter_files(repo_root: Path, surfaces: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in surfaces:
        surface = (repo_root / raw).resolve()
        if not surface.exists():
            continue
        if surface.is_file():
            files.append(surface)
            continue
        for path in surface.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in SCAN_EXTENSIONS or path.name in {"Makefile"}:
                files.append(path)
    return files


def _scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    content = path.read_text(encoding="utf-8", errors="ignore")
    for idx, line in enumerate(content.splitlines(), start=1):
        if "repo-safety: allow" in line:
            continue
        for rule in RULES:
            if rule.regex.search(line):
                findings.append(Finding(path=path, line_no=idx, line=line, rule=rule))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check command surfaces for prohibited destructive operations."
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Optional path(s) to scan. Defaults to top-level command surfaces.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only print summary unless violations exist.",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    surfaces = args.path or DEFAULT_SURFACES
    files = _iter_files(repo_root, surfaces)

    findings: list[Finding] = []
    for file_path in files:
        findings.extend(_scan_file(file_path))

    if findings and (not args.summary_only or findings):
        for finding in findings:
            print(finding.render(repo_root))
    print(
        f"Repo safety check: surfaces={len(surfaces)}, files={len(files)}, violations={len(findings)}"
    )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
