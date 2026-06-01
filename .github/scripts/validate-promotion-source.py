#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate release promotion source identity and optional Forge profile expectations."
    )
    parser.add_argument("--artifacts-dir", required=True, help="Directory containing downloaded promotable artifacts.")
    parser.add_argument("--source-run-id", required=True, help="Expected source workflow run id.")
    parser.add_argument(
        "--expected-profile-id",
        default="",
        help="Optional expected Forge profile id (for example forge-selfhosted).",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional JSON output path for validation report.",
    )
    parser.add_argument(
        "--required-scenarios",
        default="",
        help="Optional comma-separated installer scenario ids that must be present and passed in matrix-summary.json.",
    )
    parser.add_argument(
        "--promotion-channel",
        default="",
        help="Optional promotion channel (rc or stable) for lineage policy.",
    )
    parser.add_argument(
        "--expected-lineage-id",
        default="",
        help="Optional expected forge-lineage.json lineage_id (stable promotions).",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return data


def _resolve_profile_id(attestation: dict) -> str:
    resolution = attestation.get("resolution", {})
    profile = attestation.get("profile", {})
    resolution_id = str(resolution.get("profile_id", "")).strip()
    profile_id = str(profile.get("id", "")).strip()
    return resolution_id or profile_id


def _parse_required_scenarios(raw: str) -> list[str]:
    return [token.strip() for token in raw.split(",") if token.strip()]


def main() -> int:
    args = parse_args()
    artifacts_dir = Path(args.artifacts_dir)
    source_run_id = str(args.source_run_id).strip()
    expected_profile_id = str(args.expected_profile_id).strip()
    promotion_channel = str(args.promotion_channel).strip().lower()
    expected_lineage_id = str(args.expected_lineage_id).strip()
    required_scenarios = _parse_required_scenarios(args.required_scenarios)
    findings: list[dict[str, str]] = []
    status = "pass"

    if not artifacts_dir.exists():
        findings.append({"level": "error", "message": f"Artifacts directory not found: {artifacts_dir}"})
        status = "fail"
    if not source_run_id:
        findings.append({"level": "error", "message": "source_run_id is required"})
        status = "fail"

    build_metadata_path = artifacts_dir / "build-metadata.json"
    if not build_metadata_path.exists():
        findings.append({"level": "error", "message": "build-metadata.json is required for source identity validation"})
        status = "fail"
        build_metadata = {}
    else:
        try:
            build_metadata = _load_json(build_metadata_path)
        except Exception as exc:
            findings.append({"level": "error", "message": f"Invalid build-metadata.json: {exc}"})
            status = "fail"
            build_metadata = {}

    run = build_metadata.get("run", {}) if isinstance(build_metadata, dict) else {}
    observed_run_id = str(run.get("run_id", "")).strip()
    if source_run_id and observed_run_id and observed_run_id != source_run_id:
        findings.append(
            {
                "level": "error",
                "message": f"source_run_id mismatch: expected={source_run_id} observed={observed_run_id}",
            }
        )
        status = "fail"
    elif source_run_id and not observed_run_id:
        findings.append({"level": "error", "message": "build-metadata.json is missing run.run_id"})
        status = "fail"

    rc_index_path = artifacts_dir / "rc-index.json"
    if rc_index_path.exists():
        try:
            rc_index = _load_json(rc_index_path)
            rc_run_id = str(rc_index.get("run", {}).get("run_id", "")).strip()
            if source_run_id and rc_run_id and rc_run_id != source_run_id:
                findings.append(
                    {
                        "level": "error",
                        "message": f"rc-index source mismatch: expected={source_run_id} observed={rc_run_id}",
                    }
                )
                status = "fail"
        except Exception as exc:
            findings.append({"level": "error", "message": f"Invalid rc-index.json: {exc}"})
            status = "fail"

    observed_profile_id = ""
    attestation_path = artifacts_dir / "profile-attestation.json"
    if expected_profile_id:
        if not attestation_path.exists():
            findings.append(
                {
                    "level": "error",
                    "message": "expected_profile_id was provided, but profile-attestation.json is missing",
                }
            )
            status = "fail"
        else:
            try:
                attestation = _load_json(attestation_path)
                observed_profile_id = _resolve_profile_id(attestation)
                if observed_profile_id != expected_profile_id:
                    findings.append(
                        {
                            "level": "error",
                            "message": (
                                f"profile mismatch: expected={expected_profile_id} "
                                f"observed={observed_profile_id or 'unknown'}"
                            ),
                        }
                    )
                    status = "fail"
            except Exception as exc:
                findings.append({"level": "error", "message": f"Invalid profile-attestation.json: {exc}"})
                status = "fail"

        validation_path = artifacts_dir / "profile-validation.json"
        if not validation_path.exists():
            findings.append({"level": "error", "message": "expected_profile_id was provided, but profile-validation.json is missing"})
            status = "fail"
        else:
            try:
                validation = _load_json(validation_path)
                validation_status = str(validation.get("status", "")).strip().lower()
                if validation_status == "fail":
                    findings.append({"level": "error", "message": "profile-validation.json reports status=fail"})
                    status = "fail"
            except Exception as exc:
                findings.append({"level": "error", "message": f"Invalid profile-validation.json: {exc}"})
                status = "fail"

        forge_state_path = artifacts_dir / "forge-build-state.json"
        forge_state: dict = {}
        if not forge_state_path.exists():
            findings.append(
                {
                    "level": "error",
                    "message": "expected_profile_id was provided, but forge-build-state.json is missing",
                }
            )
            status = "fail"
        else:
            try:
                forge_state = _load_json(forge_state_path)
                forge_profile_id = str(forge_state.get("profile_id", "")).strip()
                if forge_profile_id != expected_profile_id:
                    findings.append(
                        {
                            "level": "error",
                            "message": (
                                f"forge-build-state profile mismatch: expected={expected_profile_id} "
                                f"observed={forge_profile_id or 'unknown'}"
                            ),
                        }
                    )
                    status = "fail"
                if forge_state.get("forge_layout_ok") is not True:
                    findings.append(
                        {
                            "level": "error",
                            "message": "forge-build-state.json reports forge_layout_ok!=true",
                        }
                    )
                    status = "fail"
            except Exception as exc:
                findings.append({"level": "error", "message": f"Invalid forge-build-state.json: {exc}"})
                status = "fail"

        lineage_path = artifacts_dir / "forge-lineage.json"
        if not lineage_path.is_file():
            findings.append(
                {
                    "level": "error",
                    "message": "expected_profile_id was provided, but forge-lineage.json is missing",
                }
            )
            status = "fail"
        else:
            try:
                lineage_payload = _load_json(lineage_path)
                observed_lineage_id = str(lineage_payload.get("lineage_id", "")).strip()
                if not observed_lineage_id:
                    findings.append({"level": "error", "message": "forge-lineage.json missing lineage_id"})
                    status = "fail"
                elif expected_lineage_id and observed_lineage_id != expected_lineage_id:
                    findings.append(
                        {
                            "level": "error",
                            "message": (
                                f"lineage_id mismatch: expected={expected_lineage_id} "
                                f"observed={observed_lineage_id}"
                            ),
                        }
                    )
                    status = "fail"
                elif promotion_channel == "stable" and not expected_lineage_id:
                    findings.append(
                        {
                            "level": "error",
                            "message": "stable promotion requires --expected-lineage-id",
                        }
                    )
                    status = "fail"
                elif promotion_channel == "stable" and not observed_lineage_id:
                    findings.append({"level": "error", "message": "stable promotion requires lineage_id"})
                    status = "fail"
                build_lineage_id = str(forge_state.get("lineage_id", "")).strip() if isinstance(forge_state, dict) else ""
                if build_lineage_id and observed_lineage_id and build_lineage_id != observed_lineage_id:
                    findings.append(
                        {
                            "level": "error",
                            "message": (
                                "forge-build-state lineage_id does not match forge-lineage.json: "
                                f"state={build_lineage_id} lineage={observed_lineage_id}"
                            ),
                        }
                    )
                    status = "fail"
            except Exception as exc:
                findings.append({"level": "error", "message": f"Invalid forge-lineage.json: {exc}"})
                status = "fail"

    matrix_path = artifacts_dir / "matrix-summary.json"
    observed_required_status: dict[str, str] = {}
    missing_required_scenarios: list[str] = []
    failed_required_scenarios: list[str] = []
    if required_scenarios:
        if not matrix_path.exists():
            findings.append(
                {
                    "level": "error",
                    "message": "required_scenarios were provided, but matrix-summary.json is missing",
                }
            )
            status = "fail"
        else:
            try:
                matrix_summary = _load_json(matrix_path)
                scenarios = matrix_summary.get("scenarios", [])
                if not isinstance(scenarios, list):
                    raise ValueError("matrix-summary.json has non-list scenarios")
                status_by_id: dict[str, str] = {}
                for row in scenarios:
                    if isinstance(row, dict):
                        sid = str(row.get("scenario_id", "")).strip()
                        if sid:
                            status_by_id[sid] = str(row.get("status", "unknown")).strip()
                for sid in required_scenarios:
                    if sid not in status_by_id:
                        missing_required_scenarios.append(sid)
                        continue
                    observed_required_status[sid] = status_by_id[sid]
                    if status_by_id[sid] != "passed":
                        failed_required_scenarios.append(sid)
                if missing_required_scenarios:
                    findings.append(
                        {
                            "level": "error",
                            "message": (
                                "required scenarios missing from matrix summary: "
                                + ",".join(missing_required_scenarios)
                            ),
                        }
                    )
                    status = "fail"
                if failed_required_scenarios:
                    findings.append(
                        {
                            "level": "error",
                            "message": (
                                "required scenarios not passed: "
                                + ",".join(
                                    f"{sid}={observed_required_status.get(sid, 'unknown')}"
                                    for sid in failed_required_scenarios
                                )
                            ),
                        }
                    )
                    status = "fail"
            except Exception as exc:
                findings.append({"level": "error", "message": f"Invalid matrix-summary.json: {exc}"})
                status = "fail"

    result = {
        "validator": "promotion-source-identity.v1",
        "status": status,
        "source_run_id": source_run_id,
        "observed_source_run_id": observed_run_id,
        "expected_profile_id": expected_profile_id,
        "observed_profile_id": observed_profile_id,
        "promotion_channel": promotion_channel,
        "expected_lineage_id": expected_lineage_id,
        "required_scenarios": required_scenarios,
        "observed_required_scenario_status": observed_required_status,
        "missing_required_scenarios": missing_required_scenarios,
        "failed_required_scenarios": failed_required_scenarios,
        "findings": findings,
    }

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(
        "Promotion source validation:"
        f" status={status}, source_run_id={source_run_id}, observed_run_id={observed_run_id or 'unknown'},"
        f" expected_profile={expected_profile_id or 'none'}, observed_profile={observed_profile_id or 'none'},"
        f" findings={len(findings)}"
    )
    if status == "fail":
        for finding in findings:
            print(f"[{finding['level'].upper()}] {finding['message']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
