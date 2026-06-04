#!/usr/bin/env python3
from __future__ import annotations
import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "blueprint": re.compile(r"^\s*##+\s+.*blueprint", re.IGNORECASE | re.MULTILINE),
    "operational docs": re.compile(r"^\s*##+\s+.*operational", re.IGNORECASE | re.MULTILINE),
    "fail-safes": re.compile(r"^\s*##+\s+.*fail[- ]?safe", re.IGNORECASE | re.MULTILINE),
    "debt tracker": re.compile(r"^\s*##+\s+.*debt.*tracker", re.IGNORECASE | re.MULTILINE),
    "sign-off": re.compile(r"^\s*##+\s+.*sign[- ]?off", re.IGNORECASE | re.MULTILINE),
}
REQUIRED_DEBT_COLUMNS = {"owner", "severity", "due_date", "status"}
REQUIRED_PRECEDENCE_LINE = "Law > Blueprint > Contract > Implementation > Pipeline > Tool"
REQUIRED_NO_BYPASS_PHRASE = "No CI bypass for required governance gates."
REQUIRED_MA12_LAW_ID = "MA-12"
REQUIRED_MA12_TITLE = "Operational Primer Mandate"
OPERATIONS_SECTION_PATTERN = re.compile(
    r"^\s*#{1,6}\s+.*how to start operations",
    re.IGNORECASE | re.MULTILINE,
)
MA12_SUBSECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "Prerequisites": re.compile(r"^\s*#{1,6}\s+.*prerequisites", re.IGNORECASE | re.MULTILINE),
    "Initialization Steps": re.compile(
        r"^\s*#{1,6}\s+.*initialization steps",
        re.IGNORECASE | re.MULTILINE,
    ),
    "Operational Entry Point": re.compile(
        r"^\s*#{1,6}\s+.*operational entry point",
        re.IGNORECASE | re.MULTILINE,
    ),
    "Verification Step": re.compile(
        r"^\s*#{1,6}\s+.*verification step",
        re.IGNORECASE | re.MULTILINE,
    ),
    "Failsafe Notes": re.compile(
        r"^\s*#{1,6}\s+.*failsafe notes",
        re.IGNORECASE | re.MULTILINE,
    ),
}
FENCED_CODE_BLOCK_PATTERN = re.compile(r"^\s*```", re.MULTILINE)
HEADING_LINE_PATTERN = re.compile(r"^\s*(#{1,6})\s+")
DEBT_SECTION_PATTERN = re.compile(r"^\s*##+\s+.*debt.*tracker", re.IGNORECASE)
HEADING_PATTERN = re.compile(r"^\s*##+\s+")


@dataclass(frozen=True)
class Finding:
    level: str
    message: str

    def render(self) -> str:
        return f"[{self.level.upper()}] {self.message}"


def _normalize_column_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return normalized.strip("_")


def _parse_markdown_row(line: str) -> list[str]:
    text = line.strip()
    if not text.startswith("|") or not text.endswith("|"):
        return []
    return [cell.strip() for cell in text.strip("|").split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    if not cells:
        return False
    for raw in cells:
        cell = raw.replace(":", "").replace("-", "").strip()
        if cell:
            return False
    return True


def _find_debt_table(
    lines: list[str],
) -> tuple[list[str] | None, list[list[str]], str | None]:
    in_debt_section = False
    for idx, line in enumerate(lines):
        if DEBT_SECTION_PATTERN.match(line):
            in_debt_section = True
            continue
        if in_debt_section and HEADING_PATTERN.match(line):
            break
        if not in_debt_section:
            continue
        if not line.strip().startswith("|"):
            continue

        header_cells = _parse_markdown_row(line)
        if not header_cells:
            continue
        if idx + 1 >= len(lines):
            return None, [], "Debt tracker table header found without separator row."

        separator_cells = _parse_markdown_row(lines[idx + 1])
        if not _is_separator_row(separator_cells):
            return None, [], "Debt tracker table header found without valid separator row."

        data_rows: list[list[str]] = []
        for row_line in lines[idx + 2 :]:
            if HEADING_PATTERN.match(row_line):
                break
            if not row_line.strip():
                break
            if not row_line.strip().startswith("|"):
                continue
            row_cells = _parse_markdown_row(row_line)
            if row_cells:
                data_rows.append(row_cells)
        return header_cells, data_rows, None

    return None, [], "Documentation Debt Tracker section does not contain a markdown table."


def _validate_checklist(checklist_path: Path) -> tuple[list[Finding], list[Finding]]:
    findings: list[Finding] = []
    errors: list[Finding] = []

    if not checklist_path.exists():
        err = Finding(level="error", message=f"Checklist file not found: {checklist_path}")
        return [err], [err]

    content = checklist_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    for label, pattern in REQUIRED_SECTION_PATTERNS.items():
        if not pattern.search(content):
            errors.append(Finding(level="error", message=f"Missing required section: {label}"))

    header_cells, rows, table_error = _find_debt_table(lines)
    if table_error:
        errors.append(Finding(level="error", message=table_error))
        findings.extend(errors)
        return findings, errors

    assert header_cells is not None  # guaranteed by table_error check above
    normalized_headers = [_normalize_column_name(col) for col in header_cells]
    header_index: dict[str, int] = {name: i for i, name in enumerate(normalized_headers)}
    missing_columns = sorted(REQUIRED_DEBT_COLUMNS - set(normalized_headers))
    if missing_columns:
        errors.append(
            Finding(
                level="error",
                message=(
                    "Debt tracker table is missing required column(s): "
                    + ", ".join(missing_columns)
                ),
            )
        )
        findings.extend(errors)
        return findings, errors

    if not rows:
        findings.append(Finding(level="info", message="Debt tracker has no rows (no open debt recorded)."))

    for row_number, row in enumerate(rows, start=1):
        if not any(cell.strip() for cell in row):
            continue
        for required_col in sorted(REQUIRED_DEBT_COLUMNS):
            col_idx = header_index[required_col]
            value = row[col_idx].strip() if col_idx < len(row) else ""
            if not value:
                errors.append(
                    Finding(
                        level="error",
                        message=(
                            f"Debt tracker row {row_number} has empty '{required_col}' value."
                        ),
                    )
                )

    findings.extend(errors)
    if not errors:
        findings.append(Finding(level="info", message="Checklist baseline validation passed."))
    return findings, errors


def _extract_section_content(content: str, section_pattern: re.Pattern[str]) -> str | None:
    match = section_pattern.search(content)
    if not match:
        return None

    heading_line = content[match.start() : match.end()].strip()
    heading_match = HEADING_LINE_PATTERN.match(heading_line)
    if not heading_match:
        return None
    section_level = len(heading_match.group(1))

    section_start = match.start()
    after_heading = content[match.end() :]
    next_heading = None
    for line_match in HEADING_LINE_PATTERN.finditer(after_heading):
        if len(line_match.group(1)) <= section_level:
            next_heading = line_match
            break

    section_end = match.end() + (next_heading.start() if next_heading else len(after_heading))
    return content[section_start:section_end]


def _validate_operational_primer(readme_path: Path) -> tuple[list[Finding], list[Finding]]:
    findings: list[Finding] = []
    errors: list[Finding] = []

    if not readme_path.exists():
        err = Finding(
            level="error",
            message=f"MA-12 requires top-level README.md; file not found: {readme_path}",
        )
        return [err], [err]

    content = readme_path.read_text(encoding="utf-8")
    section_content = _extract_section_content(content, OPERATIONS_SECTION_PATTERN)
    if section_content is None:
        errors.append(
            Finding(
                level="error",
                message=(
                    "MA-12 requires a README section header matching "
                    "'/how to start operations/i'."
                ),
            )
        )
        findings.extend(errors)
        return findings, errors

    if not FENCED_CODE_BLOCK_PATTERN.search(section_content):
        errors.append(
            Finding(
                level="error",
                message=(
                    "MA-12 requires at least one fenced code block or command sequence "
                    "inside the How to Start Operations section."
                ),
            )
        )

    for label, pattern in MA12_SUBSECTION_PATTERNS.items():
        if not pattern.search(section_content):
            errors.append(
                Finding(
                    level="error",
                    message=(
                        f"MA-12 How to Start Operations section is missing required "
                        f"subsection: {label}."
                    ),
                )
            )

    findings.extend(errors)
    if not errors:
        findings.append(
            Finding(level="info", message="MA-12 operational primer validation passed.")
        )
    return findings, errors


def _validate_meta_lawbook(repo_root: Path) -> tuple[list[Finding], list[Finding]]:
    findings: list[Finding] = []
    errors: list[Finding] = []

    lawbook_path = (repo_root / "META_ARCHITECT_LAWBOOK.md").resolve()
    if not lawbook_path.exists():
        findings.append(
            Finding(
                level="info",
                message=(
                    "Meta Architect lawbook not in workspace (gitignored local-only). "
                    "Skip lawbook validation; keep META_ARCHITECT_LAWBOOK.md on your machine only."
                ),
            )
        )
        return findings, []

    content = lawbook_path.read_text(encoding="utf-8")
    if REQUIRED_PRECEDENCE_LINE not in content:
        errors.append(
            Finding(
                level="error",
                message=(
                    "Meta Architect lawbook is missing required precedence line: "
                    f"'{REQUIRED_PRECEDENCE_LINE}'."
                ),
            )
        )
    if REQUIRED_NO_BYPASS_PHRASE not in content:
        errors.append(
            Finding(
                level="error",
                message=(
                    "Meta Architect lawbook is missing required no-bypass posture phrase: "
                    f"'{REQUIRED_NO_BYPASS_PHRASE}'."
                ),
            )
        )
    if REQUIRED_MA12_LAW_ID not in content:
        errors.append(
            Finding(
                level="error",
                message=(
                    f"Meta Architect lawbook is missing required law identifier: "
                    f"'{REQUIRED_MA12_LAW_ID}'."
                ),
            )
        )
    if REQUIRED_MA12_TITLE not in content:
        errors.append(
            Finding(
                level="error",
                message=(
                    "Meta Architect lawbook is missing required MA-12 title: "
                    f"'{REQUIRED_MA12_TITLE}'."
                ),
            )
        )

    findings.extend(errors)
    if not errors:
        findings.append(Finding(level="info", message="Meta Architect lawbook validation passed."))
    return findings, errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate project documentation baseline checklist requirements."
    )
    parser.add_argument(
        "--checklist",
        default="templates/PROJECT_BASELINE_CHECKLIST.md",
        help="Path to the project baseline checklist markdown file.",
    )
    parser.add_argument(
        "--readme",
        default="README.md",
        help="Path to the project README validated for MA-12 operational primer requirements.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Optional project root used to resolve relative paths.",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    checklist_path = Path(args.checklist)
    if not checklist_path.is_absolute():
        checklist_path = (repo_root / checklist_path).resolve()
    readme_path = Path(args.readme)
    if not readme_path.is_absolute():
        readme_path = (repo_root / readme_path).resolve()

    findings, errors = _validate_checklist(checklist_path)
    lawbook_findings, lawbook_errors = _validate_meta_lawbook(repo_root)
    readme_findings, readme_errors = _validate_operational_primer(readme_path)
    findings.extend(lawbook_findings)
    errors.extend(lawbook_errors)
    findings.extend(readme_findings)
    errors.extend(readme_errors)
    for finding in findings:
        print(finding.render())
    print(
        "Documentation baseline check: "
        f"checklist={checklist_path}, readme={readme_path}, errors={len(errors)}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
