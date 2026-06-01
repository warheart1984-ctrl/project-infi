from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import argparse
import re
import subprocess
import sys
from typing import Iterable

from story_forge.packaged_admission import (
    clear_packaged_admission,
    write_packaged_admission,
    write_packaged_smoke_token,
)


EXPECTED_MOVIE_DEPS = {
    "numpy",
    "opencv-python-headless",
    "pillow",
}
EXPECTED_SPEC_IMPORTS = {
    "story_forge.movie_renderer",
    "cv2",
    "numpy",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "PIL.ImageFont",
}


@dataclass(slots=True)
class AuditCheck:
    name: str
    passed: bool
    details: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AuditReport:
    scope: str
    mode: str
    generated_at: str
    checks: list[AuditCheck] = field(default_factory=list)
    proof_commands: list[tuple[str, str]] = field(default_factory=list)
    exceptions: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks) and not self.exceptions


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_mark(passed: bool) -> str:
    return "x" if passed else " "


def _normalize_dependency_name(entry: str) -> str:
    token = str(entry).strip().strip("\"'")
    token = re.split(r"[<>=!~;\[\]\s]", token, maxsplit=1)[0]
    return token.lower()


def parse_declared_dependencies(pyproject_text: str) -> set[str]:
    try:
        import tomllib  # type: ignore[attr-defined]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

    if tomllib is not None:
        parsed = tomllib.loads(pyproject_text)
        dependencies = parsed.get("project", {}).get("dependencies", [])
        return {
            _normalize_dependency_name(entry)
            for entry in dependencies
            if str(entry).strip()
        }

    match = re.search(r"(?ms)^dependencies\s*=\s*\[(.*?)\]", pyproject_text)
    if not match:
        return set()
    return {
        _normalize_dependency_name(entry)
        for entry in re.findall(r'"([^"]+)"', match.group(1))
        if str(entry).strip()
    }


def readme_has_human_intro(readme_text: str) -> bool:
    lines = [line.rstrip() for line in readme_text.splitlines()]
    try:
        title_index = next(index for index, line in enumerate(lines) if line.startswith("# "))
    except StopIteration:
        return False

    prose: list[str] = []
    for line in lines[title_index + 1 :]:
        stripped = line.strip()
        if not stripped:
            if prose:
                break
            continue
        if stripped.startswith("## "):
            break
        if stripped.startswith("- ") or stripped.startswith("```"):
            if prose:
                break
            continue
        prose.append(stripped)
    return len(" ".join(prose)) >= 60


def project_laws_is_pointer(project_laws_text: str) -> bool:
    lowered = project_laws_text.lower()
    return "repo_lawbook.md" in lowered and "compatibility pointer" in lowered


def run_command(
    command: list[str],
    *,
    cwd: Path,
    timeout_seconds: float = 600.0,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def check_law_alignment(root: Path) -> AuditCheck:
    lawbook_path = root / "document/law/REPO_LAWBOOK.md"
    project_laws_path = root / "PROJECT_LAWS.md"
    details: list[str] = []
    passed = True

    if not lawbook_path.exists():
        return AuditCheck(
            name="Law alignment",
            passed=False,
            details=["document/law/REPO_LAWBOOK.md is missing."],
        )

    lawbook_text = _read_text(lawbook_path)
    if "## Completion Audit Law" not in lawbook_text:
        passed = False
        details.append("document/law/REPO_LAWBOOK.md does not contain the Completion Audit Law.")
    if "fail closed" not in lawbook_text.lower():
        passed = False
        details.append("document/law/REPO_LAWBOOK.md does not describe fail-closed enforcement.")

    if not project_laws_path.exists():
        passed = False
        details.append("PROJECT_LAWS.md is missing.")
    else:
        project_laws_text = _read_text(project_laws_path)
        if not project_laws_is_pointer(project_laws_text):
            passed = False
            details.append("PROJECT_LAWS.md is not a compatibility pointer to the canonical lawbook.")
        if "## Completion Audit Law" in project_laws_text:
            passed = False
            details.append("PROJECT_LAWS.md duplicates the Completion Audit Law.")

    if passed:
        details.append("Canonical repo lawbook is present and duplicate completion-law text is avoided.")
    return AuditCheck(name="Law alignment", passed=passed, details=details)


def check_readme(root: Path) -> AuditCheck:
    readme_path = root / "README.md"
    if not readme_path.exists():
        return AuditCheck(
            name="Documentation",
            passed=False,
            details=["README.md is missing."],
        )

    readme_text = _read_text(readme_path)
    details: list[str] = []
    passed = True

    if not readme_has_human_intro(readme_text):
        passed = False
        details.append("README.md is missing a human-first introductory paragraph near the top.")
    if "## Key Principle" not in readme_text:
        passed = False
        details.append("README.md is missing the Key Principle section.")
    if "python -m story_forge.launcher" not in readme_text:
        passed = False
        details.append("README.md does not include the source run command.")

    if passed:
        details.append("README.md includes a human-first intro, key principle, and runnable launch instructions.")
    return AuditCheck(name="Documentation", passed=passed, details=details)


def check_dependencies_and_packaging(root: Path) -> AuditCheck:
    pyproject_path = root / "pyproject.toml"
    spec_path = root / "StoryForge.spec"
    details: list[str] = []
    passed = True

    if not pyproject_path.exists():
        return AuditCheck(
            name="Dependencies and packaging",
            passed=False,
            details=["pyproject.toml is missing."],
        )

    dependencies = parse_declared_dependencies(_read_text(pyproject_path))
    missing_deps = sorted(EXPECTED_MOVIE_DEPS - dependencies)
    if missing_deps:
        passed = False
        details.append(
            "pyproject.toml is missing declared movie runtime dependencies: "
            + ", ".join(missing_deps)
            + "."
        )

    if not spec_path.exists():
        passed = False
        details.append("StoryForge.spec is missing.")
    else:
        spec_text = _read_text(spec_path)
        missing_imports = sorted(
            expected for expected in EXPECTED_SPEC_IMPORTS if expected not in spec_text
        )
        if missing_imports:
            passed = False
            details.append(
                "StoryForge.spec is missing expected movie-related hidden imports: "
                + ", ".join(missing_imports)
                + "."
            )

    if passed:
        details.append("Runtime dependencies and packaged imports align with the movie path.")
    return AuditCheck(name="Dependencies and packaging", passed=passed, details=details)


def check_enforcement_hooks(root: Path) -> AuditCheck:
    build_script_path = root / "build_story_forge_exe.bat"
    workflow_path = root / ".github" / "workflows" / "completion-audit.yml"
    launcher_path = root / "src" / "story_forge" / "launcher.py"
    details: list[str] = []
    passed = True

    if not build_script_path.exists():
        passed = False
        details.append("build_story_forge_exe.bat is missing.")
    else:
        build_script_text = _read_text(build_script_path).lower()
        if "python -m story_forge.completion_audit" not in build_script_text:
            passed = False
            details.append("build_story_forge_exe.bat does not invoke the automated completion audit.")

    if not workflow_path.exists():
        passed = False
        details.append(".github/workflows/completion-audit.yml is missing.")
    else:
        workflow_text = _read_text(workflow_path).lower()
        if "story_forge.completion_audit" not in workflow_text:
            passed = False
            details.append("The CI workflow does not run the completion audit gate.")

    if not launcher_path.exists():
        passed = False
        details.append("src/story_forge/launcher.py is missing.")
    else:
        launcher_text = _read_text(launcher_path)
        if "verify_packaged_admission" not in launcher_text:
            passed = False
            details.append("launcher.py does not verify packaged admission before boot.")
        if "--completion-audit-smoke" not in launcher_text:
            passed = False
            details.append("launcher.py does not expose the packaged smoke admission path.")

    if passed:
        details.append("Build, CI, and packaged startup all fail closed through the audit gate.")
    return AuditCheck(name="Automated enforcement", passed=passed, details=details)


def run_test_suite(root: Path) -> tuple[AuditCheck, tuple[str, str]]:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]
    completed = run_command(command, cwd=root, timeout_seconds=1200.0)
    details = [f"command: {' '.join(command)}"]
    if completed.returncode == 0:
        summary_line = next(
            (line.strip() for line in completed.stdout.splitlines() if line.strip().startswith("Ran ")),
            "Test suite passed.",
        )
        details.append(summary_line)
        details.append("Test suite completed successfully.")
    else:
        details.append("Test suite failed.")
        if completed.stdout.strip():
            details.append(completed.stdout.strip().splitlines()[-1])
        if completed.stderr.strip():
            details.append(completed.stderr.strip().splitlines()[-1])
    return (
        AuditCheck(name="Core behavior and proof", passed=completed.returncode == 0, details=details),
        (" ".join(command), completed.stdout + completed.stderr),
    )


def run_packaged_smoke(root: Path, exe_path: Path) -> tuple[AuditCheck, tuple[str, str]]:
    smoke_token_path = write_packaged_smoke_token(
        exe_path,
        scope="Packaged completion audit smoke",
    )
    command = [str(exe_path), "--completion-audit-smoke", str(smoke_token_path)]
    smoke_input = "/3d A flooded chapel glows behind the archive glass.\n/movie\nquit\n"
    try:
        completed = run_command(
            command,
            cwd=root,
            timeout_seconds=180.0,
            input_text=smoke_input,
        )
        output = completed.stdout + completed.stderr
        passed = (
            completed.returncode == 0
            and "Movie export ready." in output
            and "Type '/3d <scene prompt>'" in output
        )
        details = [f"command: {exe_path}"]
        if passed:
            details.append("Packaged executable launched and completed a /3d -> /movie smoke path.")
        else:
            details.append("Packaged executable smoke path failed.")
            if output.strip():
                details.append(output.strip().splitlines()[-1])
        return (
            AuditCheck(name="Packaged smoke", passed=passed, details=details),
            (f"{exe_path} < piped smoke input>", output),
        )
    finally:
        smoke_token_path.unlink(missing_ok=True)


def render_audit_markdown(report: AuditReport) -> str:
    lines = [
        "# Completion Audit",
        "",
        f"Audit date: {report.generated_at[:10]}",
        f"Scope: {report.scope}",
        "Primary law source: `document/law/REPO_LAWBOOK.md`",
        f"Audit mode: `{report.mode}`",
        "",
        "## Summary",
        "",
        (
            "Story Forge passed the automated completion audit."
            if report.passed
            else "Story Forge failed the automated completion audit."
        ),
        "",
        "## Checklist",
        "",
    ]
    for check in report.checks:
        lines.append(f"- [{_status_mark(check.passed)}] {check.name}")
        for detail in check.details:
            lines.append(f"  {detail}")
        lines.append("")

    lines.extend(
        [
            "## Proof",
            "",
        ]
    )
    for command, output in report.proof_commands:
        lines.append(f"Command: `{command}`")
        snippet = output.strip()
        if not snippet:
            lines.append("Result: no output captured.")
            lines.append("")
            continue
        lines.append("")
        lines.append("```text")
        lines.extend(snippet.splitlines()[-20:])
        lines.append("```")
        lines.append("")

    lines.extend(
        [
            "## Exceptions",
            "",
        ]
    )
    if report.exceptions:
        for exception in report.exceptions:
            lines.append(f"- {exception}")
    else:
        lines.append("No open exceptions were carried for this audit.")
    lines.append("")
    return "\n".join(lines)


def write_audit_artifact(root: Path, report: AuditReport) -> Path:
    target = root / "AUDIT.md"
    target.write_text(render_audit_markdown(report), encoding="utf-8")
    return target


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Story Forge completion audit gate.")
    parser.add_argument(
        "--mode",
        choices=("ci", "packaged"),
        default="ci",
        help="Audit mode. 'packaged' also requires a packaged smoke path.",
    )
    parser.add_argument(
        "--packaged-exe",
        type=Path,
        default=None,
        help="Path to the packaged executable for packaged smoke verification.",
    )
    parser.add_argument(
        "--scope",
        default="Automated completion audit",
        help="Human-readable audit scope stored in AUDIT.md.",
    )
    parser.add_argument(
        "--write-audit",
        action="store_true",
        help="Write the resulting audit summary to AUDIT.md.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    root = repo_root()
    report = AuditReport(
        scope=args.scope,
        mode=args.mode,
        generated_at=_now_iso(),
    )

    report.checks.append(check_law_alignment(root))
    report.checks.append(check_readme(root))
    report.checks.append(check_dependencies_and_packaging(root))
    report.checks.append(check_enforcement_hooks(root))

    tests_check, tests_proof = run_test_suite(root)
    report.checks.append(tests_check)
    report.proof_commands.append(tests_proof)

    if args.mode == "packaged":
        if args.packaged_exe is None:
            report.checks.append(
                AuditCheck(
                    name="Packaged smoke",
                    passed=False,
                    details=["--packaged-exe is required in packaged audit mode."],
                )
            )
        else:
            packaged_check, packaged_proof = run_packaged_smoke(root, args.packaged_exe)
            report.checks.append(packaged_check)
            report.proof_commands.append(packaged_proof)

    audit_artifact_path = None
    if args.write_audit:
        audit_artifact_path = write_audit_artifact(root, report)

    if args.packaged_exe is not None:
        if report.passed and args.mode == "packaged":
            write_packaged_admission(
                args.packaged_exe,
                scope=args.scope,
                audit_mode=args.mode,
                audit_artifact_path=audit_artifact_path,
            )
        else:
            clear_packaged_admission(args.packaged_exe)

    if report.passed:
        print("Completion audit passed.")
        for check in report.checks:
            print(f"[PASS] {check.name}")
        return 0

    print("Completion audit failed.")
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"[{status}] {check.name}")
        if not check.passed:
            for detail in check.details:
                print(f"  - {detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
