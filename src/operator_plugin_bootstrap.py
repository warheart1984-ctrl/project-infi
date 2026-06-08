"""Operator plugin bootstrap — enable safe plugs, MCP manifest, platform marketplace seed."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.library_registry import list_libraries
from src.plug_adapter_runtime import PlugAdapterRuntime
from src.plug_discovery import discover_plugs
from src.workflow_family_readiness import list_families_with_readiness

AUTHORITY_RANK = {"observe": 0, "assist": 1, "execute": 2, "admin": 3}

CURSOR_SERVER_ALIASES: dict[str, str] = {
    "linear": "plugin-linear-linear",
    "plugin-linear-linear": "plugin-linear-linear",
    "datadog": "plugin-datadog-datadog",
    "plugin-datadog-datadog": "plugin-datadog-datadog",
    "firetiger": "plugin-firetiger-firetiger",
    "plugin-firetiger-firetiger": "plugin-firetiger-firetiger",
    "huggingface": "plugin-huggingface-skills-huggingface-skills",
    "huggingface-skills": "plugin-huggingface-skills-huggingface-skills",
    "plugin-huggingface-skills-huggingface-skills": "plugin-huggingface-skills-huggingface-skills",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root_from(start: Path | None = None) -> Path:
    if start is not None:
        return start.resolve().parents[0] if start.is_file() else start.resolve()
    return Path(__file__).resolve().parents[1]


def load_policy(*, repo_root: Path) -> dict[str, Any]:
    path = repo_root / "governance" / "operator_bootstrap_policy.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_platform_seed(*, repo_root: Path) -> dict[str, Any]:
    path = repo_root / "governance" / "platform_marketplace_seed.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _authority_at_most(level: str, cap: str) -> bool:
    return AUTHORITY_RANK.get(str(level or "observe"), 99) <= AUTHORITY_RANK.get(str(cap or "admin"), 99)


def plugs_to_enable(
    plugs: list[dict[str, Any]],
    *,
    policy: dict[str, Any],
    configured_mcp_server_ids: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Return (enable_ids, skipped_ids) according to bootstrap policy."""
    auto = dict(policy.get("auto_enable") or {})
    never = dict(policy.get("never_auto_enable") or {})
    mcp_cfg = dict(policy.get("mcp") or {})

    auto_classes = set(auto.get("plug_classes") or [])
    exclude_prefixes = [str(p) for p in (auto.get("exclude_plug_id_prefixes") or [])]
    never_classes = set(never.get("plug_classes") or [])
    never_authorities = set(never.get("authority_levels") or [])

    enable_mcp = bool(mcp_cfg.get("enable_when_manifest_configured", False))
    mcp_cap = str(mcp_cfg.get("max_authority_level") or "assist")
    configured = configured_mcp_server_ids or set()

    enable_ids: list[str] = []
    skipped: list[str] = []

    for plug in plugs:
        plug_id = str(plug.get("plug_id") or "")
        plug_class = str(plug.get("plug_class") or "")
        authority = str(plug.get("authority_level") or "observe")

        if any(plug_id.startswith(prefix) for prefix in exclude_prefixes):
            skipped.append(plug_id)
            continue
        if plug_class in never_classes or authority in never_authorities:
            skipped.append(plug_id)
            continue
        if plug_class in auto_classes:
            enable_ids.append(plug_id)
            continue
        if plug_class == "mcp" and enable_mcp:
            library_id = str(plug.get("library_id") or "")
            server_id = _mcp_server_id_for_library(library_id)
            if server_id and server_id in configured and _authority_at_most(authority, mcp_cap):
                enable_ids.append(plug_id)
                continue
        skipped.append(plug_id)

    return enable_ids, skipped


def _mcp_server_id_for_library(library_id: str) -> str | None:
    for library in list_libraries():
        identity = dict(library.get("identity") or {})
        if str(identity.get("library_id") or "") != library_id:
            continue
        manifest_ref = str((library.get("mount") or {}).get("manifest_ref") or "")
        if "#" in manifest_ref:
            return manifest_ref.rsplit("#", 1)[-1]
        genome = str((library.get("mount") or {}).get("genome_gene") or "")
        if genome:
            return genome.replace("_", "-")
    return None


def default_cursor_mcp_paths(*, repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    project_cfg = repo_root / ".cursor" / "mcp.json"
    if project_cfg.is_file():
        paths.append(project_cfg)
    user_cfg = Path.home() / ".cursor" / "mcp.json"
    if user_cfg.is_file() and user_cfg not in paths:
        paths.append(user_cfg)
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        legacy = Path(appdata) / "Cursor" / "User" / "globalStorage" / "cursor.mcp" / "mcp.json"
        if legacy.is_file() and legacy not in paths:
            paths.append(legacy)
    return paths


def load_cursor_mcp_config(paths: list[Path]) -> dict[str, Any]:
    merged: dict[str, Any] = {"mcpServers": {}}
    for path in paths:
        if not path.is_file():
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        servers = doc.get("mcpServers") or doc.get("servers") or {}
        if isinstance(servers, dict):
            merged["mcpServers"].update(servers)
    return merged


def _redact_server_entry(name: str, entry: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "cursor_name": name,
        "transport": "stdio",
        "configured": True,
    }
    if entry.get("url"):
        row["transport"] = "http"
        row["url"] = str(entry["url"])
    if entry.get("command"):
        row["transport"] = "stdio"
        row["command"] = str(entry["command"])
        row["args"] = list(entry.get("args") or [])
    env = entry.get("env") or {}
    auth = entry.get("auth") or {}
    env_keys = sorted({str(k) for k in list(env.keys()) + list(auth.keys())})
    if env_keys:
        row["env_keys"] = env_keys
    return row


def _normalize_server_id(cursor_name: str) -> str:
    alias = CURSOR_SERVER_ALIASES.get(cursor_name.lower())
    if alias:
        return alias
    slug = re.sub(r"[^a-z0-9]+", "-", cursor_name.lower()).strip("-")
    return f"cursor-{slug}" if slug else f"cursor-{cursor_name}"


def merge_mcp_manifest(
    *,
    cursor_config: dict[str, Any],
    existing: dict[str, Any] | None = None,
    source_paths: list[str] | None = None,
) -> dict[str, Any]:
    base = dict(existing or {})
    servers = dict(base.get("servers") or {})
    cursor_servers = dict(cursor_config.get("mcpServers") or {})

    for name, entry in cursor_servers.items():
        if not isinstance(entry, dict):
            continue
        server_id = _normalize_server_id(str(name))
        prior = dict(servers.get(server_id) or {})
        prior.update(_redact_server_entry(str(name), entry))
        prior["server_id"] = server_id
        prior["updated_at"] = _utc_now_iso()
        if source_paths:
            prior["source_paths"] = list(source_paths)
        servers[server_id] = prior

    return {
        "mcp_server_manifest_version": "mcp_server_manifest.v1",
        "generated_at": _utc_now_iso(),
        "generated_by": "bootstrap_operator_plugins",
        "servers": servers,
    }


def load_mcp_manifest(*, repo_root: Path) -> dict[str, Any]:
    path = repo_root / "governance" / "mcp_server_manifest.v1.json"
    if not path.is_file():
        return {"mcp_server_manifest_version": "mcp_server_manifest.v1", "servers": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def write_mcp_manifest(*, repo_root: Path, manifest: dict[str, Any]) -> Path:
    path = repo_root / "governance" / "mcp_server_manifest.v1.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def configured_mcp_server_ids(manifest: dict[str, Any]) -> set[str]:
    servers = dict(manifest.get("servers") or {})
    return {sid for sid, row in servers.items() if isinstance(row, dict) and row.get("configured")}


def apply_plug_enables(
    runtime: PlugAdapterRuntime,
    plug_ids: list[str],
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    enabled: list[str] = []
    missing: list[str] = []
    known = {p["plug_id"] for p in discover_plugs(repo_root=runtime._repo_root)}
    for plug_id in plug_ids:
        if plug_id not in known:
            missing.append(plug_id)
            continue
        if not dry_run:
            runtime.set_plug_enabled(plug_id, True)
        enabled.append(plug_id)
    return {"enabled": enabled, "missing": missing}


def seed_platform_marketplace(
    *,
    org_id: str,
    repo_root: Path,
    dry_run: bool = False,
    platform_settings=None,
) -> dict[str, Any]:
    from platform.marketplace.install import install_listing
    from platform.marketplace.publish import publish_listing
    from platform.service import PlatformService

    seed = load_platform_seed(repo_root=repo_root)
    svc = PlatformService(platform_settings)
    org = svc.store.get_org(org_id)
    if org is None:
        org = {
            "org_id": org_id,
            "label": org_id,
            "ugr_tenant_id": f"tenant:{org_id}",
        }
        if not dry_run:
            svc.store.upsert_org(org)
    ugr_tenant_id = str(org.get("ugr_tenant_id") or f"tenant:{org_id}")

    published: list[str] = []
    installed: list[str] = []
    for listing_seed in list(seed.get("listings") or []):
        name = str(listing_seed.get("name") or "")
        if dry_run:
            published.append(name)
            installed.append(name)
            continue
        listing = publish_listing(
            store=svc.store,
            org_id=org_id,
            ugr_tenant_id=ugr_tenant_id,
            name=name,
            steps=list(listing_seed.get("steps") or []),
            visibility=str(listing_seed.get("visibility") or "org"),
            semver=str(listing_seed.get("semver") or "1.0.0"),
            curated=bool(listing_seed.get("curated", False)),
            proof_requirements=list(listing_seed.get("proof_requirements") or []),
            workflow_id=str(listing_seed.get("workflow_id") or ""),
            is_platform_admin=True,
        )
        published.append(str(listing.get("listing_id") or name))
        wf = install_listing(
            store=svc.store,
            listing=listing,
            target_org_id=org_id,
            ugr_tenant_id=ugr_tenant_id,
            is_platform_admin=True,
        )
        installed.append(str(wf.get("workflow_id") or name))

    return {
        "org_id": org_id,
        "published_listing_ids": published,
        "installed_workflow_ids": installed,
    }


def run_governance_gates(*, repo_root: Path) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for gate in ("library-gate", "plug-adapter-gate"):
        if gate == "library-gate":
            script = repo_root / ".github" / "scripts" / "check-library-governance.py"
        else:
            script = repo_root / ".github" / "scripts" / "check-plug-adapter-governance.py"
        if not script.is_file():
            results[gate] = {"ok": False, "reason": f"missing {script.name}"}
            continue
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        results[gate] = {
            "ok": proc.returncode == 0,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    return results


def bootstrap_operator_plugins(
    *,
    repo_root: Path | None = None,
    dry_run: bool = False,
    enable_operator_plugs: bool = True,
    generate_mcp_manifest: bool = False,
    cursor_mcp_paths: list[Path] | None = None,
    platform_org: str = "",
    skip_gates: bool = False,
    runtime_dir: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or repo_root_from()
    policy = load_policy(repo_root=root)
    runtime = PlugAdapterRuntime(runtime_dir=runtime_dir, repo_root=root)

    report: dict[str, Any] = {
        "bootstrap_version": "operator_plugin_bootstrap.v1",
        "dry_run": dry_run,
        "started_at": _utc_now_iso(),
        "repo_root": str(root),
    }

    manifest = load_mcp_manifest(repo_root=root)
    mcp_paths = cursor_mcp_paths or default_cursor_mcp_paths(repo_root=root)
    if generate_mcp_manifest:
        cursor_cfg = load_cursor_mcp_config(mcp_paths)
        manifest = merge_mcp_manifest(
            cursor_config=cursor_cfg,
            existing=manifest,
            source_paths=[str(p) for p in mcp_paths if p.is_file()],
        )
        report["mcp_manifest"] = {
            "source_paths": [str(p) for p in mcp_paths if p.is_file()],
            "server_count": len(manifest.get("servers") or {}),
            "written": False,
        }
        if not dry_run:
            write_mcp_manifest(repo_root=root, manifest=manifest)
            report["mcp_manifest"]["written"] = True

    configured_servers = configured_mcp_server_ids(manifest)
    runtime.rescan()
    plugs = discover_plugs(repo_root=root)

    if enable_operator_plugs:
        enable_ids, skipped = plugs_to_enable(
            plugs,
            policy=policy,
            configured_mcp_server_ids=configured_servers,
        )
        apply_result = apply_plug_enables(runtime, enable_ids, dry_run=dry_run)
        snap = runtime.registry_snapshot()
        report["operator_plugs"] = {
            "discovered": len(plugs),
            "requested_enable": len(enable_ids),
            "enabled": apply_result["enabled"],
            "missing": apply_result["missing"],
            "skipped": skipped,
            "enabled_count": snap["enabled_count"] if not dry_run else len(apply_result["enabled"]),
        }

    if platform_org.strip():
        report["platform_marketplace"] = seed_platform_marketplace(
            org_id=platform_org.strip(),
            repo_root=root,
            dry_run=dry_run,
        )

    if not skip_gates and not dry_run:
        report["gates"] = run_governance_gates(repo_root=root)

    report["readiness"] = list_families_with_readiness(repo_root=root)
    report["finished_at"] = _utc_now_iso()
    report["ok"] = True
    if report.get("gates"):
        report["ok"] = all(row.get("ok") for row in report["gates"].values())

    return report
