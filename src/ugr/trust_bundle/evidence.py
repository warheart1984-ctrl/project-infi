"""Evidence capture for UGR trust bundle organ."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
from hashlib import sha256
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any


ORGAN_VERSION = "1.0"
BUNDLE_ID = "ugr-trust-bundle-organ-v1"


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class ScenarioEvidence:
    scenario_id: str
    machine_id: str
    status: str
    summary: str
    command: str = ""
    exit_code: int = 0
    stdout_sha256: str = ""
    payload_sha256: str = ""
    artifacts: dict[str, str] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MachineProfile:
    machine_id: str
    label: str
    platform: str
    python_version: str
    runtime_root: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_command(command: list[str], *, cwd: Path | None = None) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output


def machine_profile(machine_id: str, runtime_root: Path) -> MachineProfile:
    return MachineProfile(
        machine_id=machine_id,
        label=f"{machine_id}-profile",
        platform=platform.platform(),
        python_version=sys.version.split()[0],
        runtime_root=str(runtime_root),
    )


def write_proof_bundle(output_dir: Path, bundle: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "proof_bundle.json"
    serialized = stable_json(bundle)
    path.write_text(serialized + "\n", encoding="utf-8")
    sidecar = output_dir / "proof_bundle.sha256"
    sidecar.write_text(sha256_text(serialized) + "\n", encoding="utf-8")
    return path
