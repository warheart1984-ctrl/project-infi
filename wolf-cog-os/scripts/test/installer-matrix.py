#!/usr/bin/env python3
import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
SCENARIOS = os.environ.get("INSTALLER_TEST_SCENARIOS", "1,2,3,4,5,6,7")
WORK_ROOT = Path(os.environ.get("COGOS_MATRIX_WORK", os.environ.get("MATRIX_OUT_DIR", "/tmp/cogos-installer-matrix")))
BASE_ROOTFS = Path(
    os.environ.get(
        "COGOS_ROOTFS_SRC",
        str(ROOT_DIR / "wolf-cog-os" / "build" / f"rootfs-{os.environ.get('COGOS_TAG', '12-22-0-wolf-os')}"),
    )
)
BASE_ISO = os.environ.get(
    "ISO",
    str(ROOT_DIR / "wolf-cog-os" / "output" / f"wolf-cog-os-{os.environ.get('COGOS_TAG', '12.22.0-wolf-os')}.iso"),
)
DEBIAN_BASE_ISO = os.environ.get("COGOS_MATRIX_BASE_ISO", "")
MATRIX_SUMMARY_PATH = Path(os.environ.get("COGOS_MATRIX_SUMMARY_PATH", str(WORK_ROOT / "matrix-summary.json")))
DEBUG_LOG_PATH = ROOT_DIR / "debug-26beb4.log"


# region agent log
def debug_log(run_id: str, hypothesis_id: str, location: str, message: str, data: dict) -> None:
    payload = {
        "sessionId": "26beb4",
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with DEBUG_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, separators=(",", ":")) + "\n")


# endregion


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run installer matrix scenarios.")
    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="Scenario id(s) to run. Repeat flag or use comma-separated list.",
    )
    parser.add_argument("--iso", help="ISO path override for scenario 6/5.")
    parser.add_argument("--work-root", help="Matrix work root override.")
    parser.add_argument("--summary-path", help="Matrix summary output path override.")
    return parser.parse_args()


def resolve_scenarios(arg_values) -> str:
    if not arg_values:
        return SCENARIOS
    collected = []
    for raw in arg_values:
        for token in raw.split(","):
            tok = token.strip()
            if tok:
                collected.append(tok)
    return ",".join(collected) if collected else SCENARIOS


def log(msg: str) -> None:
    print(f"[installer-matrix] {msg}")


def run(cmd, env=None, check=True):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    print("+", " ".join(shlex.quote(str(c)) for c in cmd))
    return subprocess.run(cmd, env=merged_env, check=check)


def run_loop_apply(name: str, extra_env=None):
    scenario_dir = WORK_ROOT / name
    env = {
        "INSTALLER_STATE_DIR": str(scenario_dir / "state"),
        "COGOS_LOOP_TEST_WORK": str(scenario_dir),
        "COGOS_LOOP_TEST_IMG": str(scenario_dir / "disk.img"),
        "TARGET_MOUNT_ROOT": str(scenario_dir / "target-root"),
    }
    if extra_env:
        env.update(extra_env)
    run(["bash", str(ROOT_DIR / "wolf-cog-os/scripts/test/installer-loop-apply.sh")], env=env)


def scenario1():
    log("Scenario 1: clean disk install (core)")
    run_loop_apply("scenario1-core", {"COGOS_ROOTFS_SRC": str(BASE_ROOTFS)})


def scenario2():
    log("Scenario 2: clean disk install (daily-driver)")
    dd_rootfs = WORK_ROOT / "daily-driver-rootfs"
    run(
        [
            "sudo",
            "bash",
            str(ROOT_DIR / "wolf-cog-os/scripts/build-rootfs.sh"),
        ],
        env={"COGOS_ROOTFS_OUT": str(dd_rootfs), "COGOS_DAILY_DRIVER_PACKAGES": "1"},
    )
    run_loop_apply("scenario2-daily", {"COGOS_ROOTFS_SRC": str(dd_rootfs)})


def scenario3():
    log("Scenario 3: injected failure + resume")
    scenario = "scenario3-resume"
    scenario_dir = WORK_ROOT / scenario
    state_dir = scenario_dir / "state"
    target_root = scenario_dir / "target-root"
    img = scenario_dir / "disk.img"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    target_root.mkdir(parents=True, exist_ok=True)
    run(["qemu-img", "create", "-f", "raw", str(img), "20G"])
    loop_dev = subprocess.check_output(["sudo", "losetup", "--find", "--show", str(img)], text=True).strip()
    try:
        first = run(
            [
                "sudo",
                "env",
                f"INSTALLER_STATE_DIR={state_dir}",
                f"TARGET_MOUNT_ROOT={target_root}",
                "COGOS_INSTALLER_FAIL_STEP=bootloader",
                "bash",
                str(ROOT_DIR / "wolf-cog-os/scripts/cogos-installer.sh"),
                "--target-disk",
                loop_dev,
                "--rootfs",
                str(BASE_ROOTFS),
                "--state-dir",
                str(state_dir),
                "--hostname",
                "cogos-resume-test",
                "--user",
                "operator",
                "--no-rollback",
                "--apply",
                "--yes",
                "--non-interactive",
            ],
            check=False,
        )
        if first.returncode == 0:
            raise RuntimeError("Expected injected failure did not occur")

        run(
            [
                "sudo",
                "env",
                f"INSTALLER_STATE_DIR={state_dir}",
                f"TARGET_MOUNT_ROOT={target_root}",
                "bash",
                str(ROOT_DIR / "wolf-cog-os/scripts/cogos-installer.sh"),
                "--target-disk",
                loop_dev,
                "--rootfs",
                str(BASE_ROOTFS),
                "--state-dir",
                str(state_dir),
                "--hostname",
                "cogos-resume-test",
                "--user",
                "operator",
                "--apply",
                "--yes",
                "--non-interactive",
                "--resume",
            ],
        )
        run(
            [
                "python3",
                str(ROOT_DIR / "wolf-cog-os/scripts/test/validate-installer-state.py"),
                "--state",
                str(state_dir / "state.json"),
                "--require-proof",
                "--target-root",
                str(target_root),
            ]
        )
    finally:
        subprocess.run(["sudo", "losetup", "-d", loop_dev], check=False)


def scenario4():
    log("Scenario 4: rollback on failure path")
    scenario = "scenario4-rollback"
    scenario_dir = WORK_ROOT / scenario
    state_dir = scenario_dir / "state"
    target_root = scenario_dir / "target-root"
    img = scenario_dir / "disk.img"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    target_root.mkdir(parents=True, exist_ok=True)
    run(["qemu-img", "create", "-f", "raw", str(img), "20G"])
    loop_dev = subprocess.check_output(["sudo", "losetup", "--find", "--show", str(img)], text=True).strip()
    try:
        first = run(
            [
                "sudo",
                "bash",
                str(ROOT_DIR / "wolf-cog-os/scripts/cogos-installer.sh"),
                "--target-disk",
                loop_dev,
                "--rootfs",
                str(BASE_ROOTFS),
                "--hostname",
                "cogos-rollback-test",
                "--user",
                "operator",
                "--apply",
                "--yes",
                "--non-interactive",
            ],
            env={
                "INSTALLER_STATE_DIR": str(state_dir),
                "TARGET_MOUNT_ROOT": str(target_root),
                "COGOS_INSTALLER_FAIL_STEP": "copy",
            },
            check=False,
        )
        if first.returncode == 0:
            raise RuntimeError("Expected rollback-triggering failure did not occur")
        if "rollback" not in (state_dir / "events.log").read_text(encoding="utf-8", errors="ignore"):
            raise RuntimeError("Rollback events not detected")
    finally:
        subprocess.run(["sudo", "losetup", "-d", loop_dev], check=False)


def scenario5():
    log("Scenario 5: surprise mode build + smoke boot")
    if not DEBIAN_BASE_ISO:
        log("Skipping scenario 5 (COGOS_MATRIX_BASE_ISO not provided).")
        return "skipped"
    out_iso = WORK_ROOT / "surprise" / "Wolf-CoG-OS-daily-driver-surprise.iso"
    out_iso.parent.mkdir(parents=True, exist_ok=True)
    run(
        ["bash", str(ROOT_DIR / "wolf-cog-os/scripts/build-surprise-installer.sh"), DEBIAN_BASE_ISO],
        env={
            "COGOS_OUT": str(out_iso),
            "COGOS_BUILD_FROM_TREE": "1",
            "COGOS_BUILD_ROOTFS_FIRST": "1",
        },
    )
    run(
        ["bash", str(ROOT_DIR / "wolf-cog-os/scripts/test/installer-qemu-smoke.sh")],
        env={"ISO": str(out_iso), "COGOS_QEMU_WORK": str(WORK_ROOT / "surprise" / "qemu"), "COGOS_QEMU_WAIT": "60"},
    )


def scenario6():
    log("Scenario 6: normal ISO QEMU boot smoke")
    run(
        ["bash", str(ROOT_DIR / "wolf-cog-os/scripts/test/installer-qemu-smoke.sh")],
        env={"ISO": BASE_ISO, "COGOS_QEMU_WORK": str(WORK_ROOT / "scenario6-qemu"), "COGOS_QEMU_WAIT": "60"},
    )


def scenario7():
    log("Scenario 7: upgrade/reinstall smoke")
    scenario_dir = WORK_ROOT / "scenario7-upgrade"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    shared_img = scenario_dir / "disk.img"
    run_loop_apply("scenario7-upgrade-pass1", {"COGOS_ROOTFS_SRC": str(BASE_ROOTFS), "COGOS_LOOP_TEST_IMG": str(shared_img)})
    dd_rootfs = scenario_dir / "daily-driver-rootfs"
    run(
        ["sudo", "bash", str(ROOT_DIR / "wolf-cog-os/scripts/build-rootfs.sh")],
        env={"COGOS_ROOTFS_OUT": str(dd_rootfs), "COGOS_DAILY_DRIVER_PACKAGES": "1"},
    )
    run_loop_apply(
        "scenario7-upgrade-pass2",
        {"COGOS_ROOTFS_SRC": str(dd_rootfs), "COGOS_LOOP_TEST_IMG": str(shared_img), "COGOS_LOOP_REUSE_IMG": "1"},
    )


SCENARIO_MAP = {
    "1": {"name": "CleanDiskInstall_Core", "fn": scenario1, "tags": ["installer", "core"]},
    "2": {"name": "CleanDiskInstall_DailyDriver", "fn": scenario2, "tags": ["installer", "daily_driver"]},
    "3": {"name": "ResumeAfterInjectedFailure", "fn": scenario3, "tags": ["installer", "resume"]},
    "4": {"name": "RollbackPathFailure", "fn": scenario4, "tags": ["installer", "rollback"]},
    "5": {"name": "SurpriseModeInstallPath", "fn": scenario5, "tags": ["iso_build", "qemu_boot", "surprise"]},
    "6": {"name": "QemuIsoBootSmoke", "fn": scenario6, "tags": ["qemu_boot"]},
    "7": {"name": "UpgradePath_Smoke", "fn": scenario7, "tags": ["installer", "upgrade"]},
}


def get_run_id() -> str:
    if os.environ.get("GITHUB_RUN_ID"):
        return os.environ["GITHUB_RUN_ID"]
    return f"local-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}"


def resolve_forge_profile_metadata() -> tuple[str, str, list[str]]:
    profile_id = ""
    profile_source = ""
    if os.environ.get("COGOS_FORGE_PROFILE"):
        profile_id = os.environ["COGOS_FORGE_PROFILE"]
        profile_source = "env.COGOS_FORGE_PROFILE"
    else:
        boot_profile = os.environ.get("COGOS_BOOT_PROFILE", "")
        if boot_profile.startswith("forge"):
            profile_id = boot_profile
            profile_source = "env.COGOS_BOOT_PROFILE"

    required_gate_set: list[str] = []
    if profile_id:
        required_raw = os.environ.get("COGOS_FORGE_REQUIRED_SCENARIOS", "1,3,6")
        required_gate_set = [sid.strip() for sid in required_raw.split(",") if sid.strip()]
    return profile_id, profile_source, required_gate_set


def build_forge_enforcement(records, selected_scenarios: list[str]) -> dict:
    profile_env_value = os.environ.get("COGOS_FORGE_PROFILE", "")
    enforcement_enabled = bool(profile_env_value.strip())
    profile_id, profile_source, required_gate_set = resolve_forge_profile_metadata()

    required_status = {}
    missing_required = []
    passed = True
    reason = "enforcement_disabled"

    if enforcement_enabled:
        selected_set = set(selected_scenarios)
        result_by_id = {str(row.get("scenario_id", "")).strip(): row for row in records}
        missing_required = [sid for sid in required_gate_set if sid not in selected_set]
        if missing_required:
            passed = False
            reason = "required_scenarios_missing_from_selection"
        else:
            for sid in required_gate_set:
                status = result_by_id.get(sid, {}).get("status", "not_run")
                required_status[sid] = status
                if status != "passed":
                    passed = False
            reason = "all_required_scenarios_passed" if passed else "required_scenarios_not_passed"

    return {
        "enabled": enforcement_enabled,
        "passed": passed if enforcement_enabled else True,
        "reason": reason,
        "profile_env_value": profile_env_value,
        "profile_id": profile_id,
        "profile_source": profile_source,
        "required_gate_set": required_gate_set,
        "selected_scenarios": selected_scenarios,
        "missing_required_scenarios": missing_required,
        "required_scenario_status": required_status,
    }


def write_summary(records, started_at_epoch: float, forge_enforcement: dict) -> None:
    MATRIX_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    finished_at = datetime.now(timezone.utc)
    profile_id, profile_source, required_gate_set = resolve_forge_profile_metadata()
    payload = {
        "schema_version": 3,
        "run_id": get_run_id(),
        "cogos_tag": os.environ.get("COGOS_TAG", "unknown"),
        "workflow_name": os.environ.get("GITHUB_WORKFLOW", "local"),
        "event_name": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "profile_id": profile_id,
        "profile_source": profile_source,
        "required_gate_set": required_gate_set,
        "forge_enforcement": forge_enforcement,
        "started_at": datetime.fromtimestamp(started_at_epoch, tz=timezone.utc).isoformat(),
        "finished_at": finished_at.isoformat(),
        "scenarios": records,
        "total_duration_sec": round(time.time() - started_at_epoch, 3),
        "timestamp": finished_at.isoformat(),
    }
    MATRIX_SUMMARY_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    log(f"Matrix summary written: {MATRIX_SUMMARY_PATH}")


def main():
    global SCENARIOS, BASE_ISO, WORK_ROOT, MATRIX_SUMMARY_PATH, DEBIAN_BASE_ISO
    args = parse_args()
    if args.scenario:
        SCENARIOS = resolve_scenarios(args.scenario)
    if args.iso:
        BASE_ISO = args.iso
        # Keep CLI override coherent for both scenario 6 (boot smoke) and scenario 5 (surprise build substrate).
        DEBIAN_BASE_ISO = args.iso
    if args.work_root:
        WORK_ROOT = Path(args.work_root)
    if args.summary_path:
        MATRIX_SUMMARY_PATH = Path(args.summary_path)
    else:
        MATRIX_SUMMARY_PATH = Path(os.environ.get("COGOS_MATRIX_SUMMARY_PATH", str(WORK_ROOT / "matrix-summary.json")))

    run_id = f"matrix-debug-{int(time.time())}-{os.getpid()}"
    # region agent log
    debug_log(
        run_id,
        "H1",
        "installer-matrix.py:main:argv",
        "process argv observed",
        {"argv": sys.argv},
    )
    debug_log(
        run_id,
        "H2",
        "installer-matrix.py:main:env-selection",
        "selection/env inputs observed",
        {
            "INSTALLER_TEST_SCENARIOS": os.environ.get("INSTALLER_TEST_SCENARIOS"),
            "SCENARIOS": SCENARIOS,
            "parsed_scenario_args": args.scenario,
            "COGOS_FORGE_PROFILE": os.environ.get("COGOS_FORGE_PROFILE"),
            "COGOS_BOOT_PROFILE": os.environ.get("COGOS_BOOT_PROFILE"),
            "COGOS_FORGE_REQUIRED_SCENARIOS": os.environ.get("COGOS_FORGE_REQUIRED_SCENARIOS"),
            "ISO_env": os.environ.get("ISO"),
            "BASE_ISO": BASE_ISO,
            "parsed_iso_arg": args.iso,
            "COGOS_MATRIX_BASE_ISO": os.environ.get("COGOS_MATRIX_BASE_ISO"),
            "DEBIAN_BASE_ISO": DEBIAN_BASE_ISO,
            "COGOS_MATRIX_WORK": os.environ.get("COGOS_MATRIX_WORK"),
            "MATRIX_OUT_DIR": os.environ.get("MATRIX_OUT_DIR"),
            "WORK_ROOT": str(WORK_ROOT),
            "parsed_work_root_arg": args.work_root,
            "MATRIX_SUMMARY_PATH": str(MATRIX_SUMMARY_PATH),
        },
    )
    # endregion
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    started_at = time.time()
    results = []
    overall_ok = True
    selected_scenarios = [s.strip() for s in SCENARIOS.split(",") if s.strip()]
    forge_enforcement = {}
    try:
        for sid in selected_scenarios:
            # region agent log
            debug_log(
                run_id,
                "H3",
                "installer-matrix.py:main:scenario-loop",
                "scenario id selected for execution",
                {"sid": sid, "SCENARIOS": SCENARIOS},
            )
            # endregion
            spec = SCENARIO_MAP.get(sid)
            if spec is None:
                raise SystemExit(f"Unknown scenario id: {sid}")

            scenario_start = time.time()
            status = "passed"
            error_summary = None
            try:
                rv = spec["fn"]()
                if rv == "skipped":
                    status = "skipped"
            except Exception as exc:
                status = "failed"
                error_summary = str(exc)
                overall_ok = False

            results.append(
                {
                    "id": int(sid),
                    "scenario_id": sid,
                    "name": spec["name"],
                    "tags": spec.get("tags", []),
                    "status": status,
                    "duration_sec": round(time.time() - scenario_start, 3),
                    "error_summary": error_summary,
                }
            )

            if status == "failed":
                log(f"Scenario {sid} failed: {error_summary}")
                break
    finally:
        forge_enforcement = build_forge_enforcement(results, selected_scenarios)
        write_summary(results, started_at, forge_enforcement)

    if forge_enforcement.get("enabled") and not forge_enforcement.get("passed", False):
        overall_ok = False
        log(
            "Forge required scenario gate failed: "
            f"{forge_enforcement.get('reason')} "
            f"(required={forge_enforcement.get('required_gate_set', [])}, "
            f"missing={forge_enforcement.get('missing_required_scenarios', [])}, "
            f"status={forge_enforcement.get('required_scenario_status', {})})"
        )

    if not overall_ok:
        raise SystemExit("Installer matrix failed. See matrix-summary.json for details.")

    log(f"Installer scenario matrix complete: {SCENARIOS}")


if __name__ == "__main__":
    main()
