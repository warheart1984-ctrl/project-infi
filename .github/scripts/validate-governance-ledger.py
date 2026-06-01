#!/usr/bin/env python3
import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


POLICIES = {"warn", "fail"}
DEPRECATION_STATUSES = {"active", "deprecated", "removed"}
MAKE_TARGET_RE = re.compile(r"^([A-Za-z0-9_.-]+)\s*:(?:\s|$)")


@dataclass(frozen=True)
class Finding:
    level: str
    command_id: str
    message: str

    def render(self) -> str:
        return f"[{self.level.upper()}] {self.command_id}: {self.message}"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Ledger root must be an object: {path}")
    return data


def _read_text_cached(path: Path, cache: dict[Path, str]) -> str:
    if path not in cache:
        cache[path] = path.read_text(encoding="utf-8")
    return cache[path]


def _collect_make_targets(makefile_path: Path) -> set[str]:
    targets: set[str] = set()
    for raw_line in makefile_path.read_text(encoding="utf-8").splitlines():
        if not raw_line or raw_line[0].isspace():
            continue
        match = MAKE_TARGET_RE.match(raw_line)
        if not match:
            continue
        target = match.group(1).strip()
        if target and not target.startswith("."):
            targets.add(target)
    return targets


def _var_referenced(content: str, var_name: str) -> bool:
    patterns = (
        rf"\b{re.escape(var_name)}\s*:",
        rf"\b{re.escape(var_name)}\s*=",
        rf"\${{{re.escape(var_name)}}}",
        rf"\${re.escape(var_name)}\b",
        rf"\bsecrets\.{re.escape(var_name)}\b",
    )
    return any(re.search(pattern, content) for pattern in patterns)


def _validate_command_shape(cmd: dict[str, Any], idx: int) -> tuple[str, list[str]]:
    missing: list[str] = []
    cmd_id = str(cmd.get("id", "")).strip() or f"commands[{idx}]"
    for key in (
        "id",
        "owner",
        "component",
        "invocation",
        "required_env",
        "optional_env",
        "deprecation",
        "verification_policy",
        "consumers",
    ):
        if key not in cmd:
            missing.append(key)
    return cmd_id, missing


def _effective_policy(default_policy: str, command_policy: str, mode: str) -> str:
    if mode in POLICIES:
        return mode
    if command_policy in POLICIES:
        return command_policy
    return default_policy if default_policy in POLICIES else "warn"


def _add_contract_finding(
    findings: list[Finding],
    command_id: str,
    policy: str,
    message: str,
) -> None:
    level = "error" if policy == "fail" else "warning"
    findings.append(Finding(level=level, command_id=command_id, message=message))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate command governance ledger contracts.")
    parser.add_argument(
        "--ledger",
        default=".github/governance/command-ledger.json",
        help="Path to governance ledger JSON.",
    )
    parser.add_argument(
        "--mode",
        choices=["ledger", "warn", "fail"],
        default="ledger",
        help="Override verification policy (default: use per-command ledger policy).",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only print summary line unless errors exist.",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    ledger_path = (repo_root / args.ledger).resolve()
    try:
        ledger = _load_json(ledger_path)
    except Exception as exc:
        print(f"[ERROR] ledger: {exc}", file=sys.stderr)
        return 2

    default_policy = str(ledger.get("default_verification_policy", "warn")).strip().lower()
    if default_policy not in POLICIES:
        print(
            f"[ERROR] ledger: invalid default_verification_policy '{default_policy}', expected one of {sorted(POLICIES)}",
            file=sys.stderr,
        )
        return 2

    commands = ledger.get("commands", [])
    if not isinstance(commands, list):
        print("[ERROR] ledger: 'commands' must be an array.", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    content_cache: dict[Path, str] = {}
    make_cache: dict[Path, set[str]] = {}
    seen_ids: set[str] = set()

    for idx, raw_cmd in enumerate(commands):
        if not isinstance(raw_cmd, dict):
            findings.append(Finding(level="error", command_id=f"commands[{idx}]", message="Command entry must be an object."))
            continue

        command_id, missing = _validate_command_shape(raw_cmd, idx)
        if missing:
            findings.append(Finding(level="error", command_id=command_id, message=f"Missing required keys: {', '.join(missing)}"))
            continue
        if command_id in seen_ids:
            findings.append(Finding(level="error", command_id=command_id, message="Duplicate command id."))
            continue
        seen_ids.add(command_id)

        command_policy = str(raw_cmd.get("verification_policy", "")).strip().lower()
        policy = _effective_policy(default_policy, command_policy, args.mode)

        owner = repo_root / str(raw_cmd.get("owner", "")).strip()
        if not owner.exists():
            _add_contract_finding(findings, command_id, policy, f"Owner path does not exist: {owner.relative_to(repo_root)}")

        invocation = raw_cmd.get("invocation", {})
        if not isinstance(invocation, dict):
            findings.append(Finding(level="error", command_id=command_id, message="'invocation' must be an object."))
            continue
        invocation_type = str(invocation.get("type", "")).strip()

        if invocation_type == "make_target":
            makefile_rel = str(invocation.get("makefile", "")).strip()
            target = str(invocation.get("target", "")).strip()
            if not makefile_rel or not target:
                findings.append(Finding(level="error", command_id=command_id, message="make_target invocation requires makefile and target."))
            else:
                makefile_path = repo_root / makefile_rel
                if not makefile_path.exists():
                    _add_contract_finding(
                        findings,
                        command_id,
                        policy,
                        f"Makefile does not exist: {makefile_rel}",
                    )
                else:
                    targets = make_cache.setdefault(makefile_path, _collect_make_targets(makefile_path))
                    if target not in targets:
                        _add_contract_finding(
                            findings,
                            command_id,
                            policy,
                            f"Target '{target}' not found in {makefile_rel}.",
                        )
        elif invocation_type == "script_path":
            script_rel = str(invocation.get("path", "")).strip()
            if not script_rel:
                findings.append(Finding(level="error", command_id=command_id, message="script_path invocation requires path."))
            else:
                script_path = repo_root / script_rel
                if not script_path.exists():
                    _add_contract_finding(
                        findings,
                        command_id,
                        policy,
                        f"Script path does not exist: {script_rel}",
                    )
        else:
            findings.append(
                Finding(
                    level="error",
                    command_id=command_id,
                    message=f"Unsupported invocation.type '{invocation_type}'.",
                )
            )

        required_env = raw_cmd.get("required_env", [])
        optional_env = raw_cmd.get("optional_env", [])
        consumers = raw_cmd.get("consumers", [])
        deprecation = raw_cmd.get("deprecation", {})
        dep_status = str((deprecation or {}).get("status", "active")).strip().lower()
        replacement = str((deprecation or {}).get("replacement", "")).strip()

        if not isinstance(required_env, list) or not isinstance(optional_env, list):
            findings.append(Finding(level="error", command_id=command_id, message="'required_env' and 'optional_env' must be arrays."))
            continue
        if not isinstance(consumers, list):
            findings.append(Finding(level="error", command_id=command_id, message="'consumers' must be an array."))
            continue
        if dep_status not in DEPRECATION_STATUSES:
            findings.append(Finding(level="error", command_id=command_id, message=f"Invalid deprecation.status '{dep_status}'."))
            continue

        matched_consumer_count = 0
        for consumer_idx, consumer in enumerate(consumers):
            if not isinstance(consumer, dict):
                findings.append(
                    Finding(
                        level="error",
                        command_id=command_id,
                        message=f"consumers[{consumer_idx}] must be an object.",
                    )
                )
                continue
            consumer_path_rel = str(consumer.get("path", "")).strip()
            contains = str(consumer.get("contains", "")).strip()
            if not consumer_path_rel or not contains:
                findings.append(
                    Finding(
                        level="error",
                        command_id=command_id,
                        message=f"consumers[{consumer_idx}] requires path and contains.",
                    )
                )
                continue
            consumer_path = repo_root / consumer_path_rel
            if not consumer_path.exists():
                _add_contract_finding(
                    findings,
                    command_id,
                    policy,
                    f"Consumer file does not exist: {consumer_path_rel}",
                )
                continue

            consumer_content = _read_text_cached(consumer_path, content_cache)
            if contains not in consumer_content:
                _add_contract_finding(
                    findings,
                    command_id,
                    policy,
                    f"Consumer '{consumer_path_rel}' no longer contains '{contains}'.",
                )
                continue

            matched_consumer_count += 1
            for env_name in required_env:
                env_key = str(env_name).strip()
                if env_key and not _var_referenced(consumer_content, env_key):
                    _add_contract_finding(
                        findings,
                        command_id,
                        policy,
                        f"Required env '{env_key}' is not referenced in consumer '{consumer_path_rel}'.",
                    )

        if dep_status == "deprecated" and matched_consumer_count > 0:
            replacement_hint = f" Replacement: {replacement}." if replacement else ""
            _add_contract_finding(
                findings,
                command_id,
                policy,
                f"Deprecated command still has active consumers.{replacement_hint}",
            )

    errors = [finding for finding in findings if finding.level == "error"]
    warnings = [finding for finding in findings if finding.level == "warning"]

    if not args.summary_only or errors:
        for finding in findings:
            print(finding.render())
    print(
        f"Governance ledger check: commands={len(commands)}, warnings={len(warnings)}, errors={len(errors)}, mode={args.mode}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
