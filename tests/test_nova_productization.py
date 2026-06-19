from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = (
    REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    if sys.platform == "win32"
    else REPO_ROOT / ".venv" / "bin" / "python"
)


def test_windows_verify_discovers_repo_virtualenv_python() -> None:
    with tempfile.TemporaryDirectory(prefix="nova-verify-home-") as home:
        env = os.environ.copy()
        env["USERPROFILE"] = home
        env["LAWFUL_NOVA_REPO_ROOT"] = str(REPO_ROOT)
        env["PATH"] = os.pathsep.join(
            part for part in env.get("PATH", "").split(os.pathsep) if "Python" not in part
        )

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(REPO_ROOT / "lawful-nova-shell" / "setup" / "verify.ps1"),
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] Python .venv" in result.stdout


def test_unix_verify_discovers_repo_virtualenv_python() -> None:
    if sys.platform == "win32":
        return
    bash = shutil.which("bash")
    if bash is None:
        return

    with tempfile.TemporaryDirectory(prefix="nova-verify-home-") as home:
        env = os.environ.copy()
        env["HOME"] = home
        env["LAWFUL_NOVA_REPO_ROOT"] = str(REPO_ROOT)

        result = subprocess.run(
            [bash, str(REPO_ROOT / "lawful-nova-shell" / "setup" / "verify.sh")],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] Python .venv" in result.stdout


def test_unix_verify_treats_docker_as_native_optional() -> None:
    if sys.platform == "win32":
        return
    bash = shutil.which("bash")
    if bash is None:
        return

    env = os.environ.copy()
    env["LAWFUL_NOVA_REPO_ROOT"] = str(REPO_ROOT)
    env["PATH"] = os.pathsep.join(
        part for part in env.get("PATH", "").split(os.pathsep) if "docker" not in part.lower()
    )

    result = subprocess.run(
        [bash, str(REPO_ROOT / "lawful-nova-shell" / "setup" / "verify.sh")],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[INFO] Docker not found - optional for native unix agent" in result.stdout
    assert "[WARN] Docker not found" not in result.stdout


def test_windows_verify_treats_docker_as_native_optional() -> None:
    with tempfile.TemporaryDirectory(prefix="nova-verify-home-") as home:
        env = os.environ.copy()
        env["USERPROFILE"] = home
        env["LAWFUL_NOVA_REPO_ROOT"] = str(REPO_ROOT)
        env["PATH"] = os.pathsep.join(
            part
            for part in env.get("PATH", "").split(os.pathsep)
            if "Docker" not in part and "docker" not in part
        )

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(REPO_ROOT / "lawful-nova-shell" / "setup" / "verify.ps1"),
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[INFO] Docker not found - optional for native Windows agent" in result.stdout
    assert "[WARN] Docker not found" not in result.stdout


def test_lawful_nova_shell_cli_health_outputs_json() -> None:
    if sys.platform == "win32":
        cli = REPO_ROOT / "lawful-nova-shell" / "bin" / "nova.ps1"
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(cli),
            "health",
            "--json",
        ]
    else:
        cli = REPO_ROOT / "lawful-nova-shell" / "bin" / "nova"
        cmd = [str(cli), "health", "--json"]

    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    json_line = next(
        (line for line in reversed(result.stdout.splitlines()) if line.strip().startswith("{")),
        result.stdout.strip(),
    )
    payload = json.loads(json_line)
    assert payload["service"] == "nova_local_cli"
    assert payload["direct_lawful_llm"]["status"] == "ok"


def test_local_nova_cli_health_outputs_json() -> None:
    if not PYTHON.exists():
        return
    result = subprocess.run(
        [str(PYTHON), "-m", "nova.cli", "health", "--json"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["service"] == "nova_local_cli"
    assert payload["direct_lawful_llm"]["status"] == "ok"


def test_nova_productization_gate_reports_local_slice_ready() -> None:
    if not PYTHON.exists():
        return
    out = REPO_ROOT / ".runtime" / "nova_productization_test_report.json"
    result = subprocess.run(
        [str(PYTHON), "scripts/nova_productization_gate.py", "--json-out", str(out)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["local_lawful_slice_ready"] is True
    assert payload["checks"]["direct_lawful_llm"]["status"] == "ok"
    assert payload["checks"]["chain_contract"]["status"] == "ok"
    assert payload["checks"]["python_runtime"]["status"] == "ok"
    assert all("Point NOVA_CLI" not in item for item in payload["remaining_external_closure"])
    assert all("Start /health-compatible API" not in item for item in payload["remaining_external_closure"])


def test_nova_cli_is_packaged_as_console_script() -> None:
    payload = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = payload["project"]["scripts"]
    includes = payload["tool"]["setuptools"]["packages"]["find"]["include"]

    assert scripts["nova"] == "nova.cli:main"
    assert "nova*" in includes


def test_local_nova_api_health_and_chat_contract() -> None:
    from fastapi.testclient import TestClient
    from nova.api import app

    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["service"] == "nova_local_api"

    chat = client.post(
        "/v1/chat",
        json={"prompt": "observe lawful nova", "tenant_id": "local", "capability": "observe"},
    )
    assert chat.status_code == 200
    payload = chat.json()
    assert payload["decision"] == "EXECUTED"
    assert payload["receipt_verified"] is True
    chain = payload["chain"]
    assert chain["identity"]["instance_id"]
    assert chain["trace"]["trace_id"]
    assert chain["authority_boundary"]["operator_authority"] == "external"
    assert chain["authority_boundary"]["runtime_authority"] == "execute_after_rsl"
    assert chain["reproducibility"]["prompt_sha256"]
    assert chain["reproducibility"]["output_sha256"]
