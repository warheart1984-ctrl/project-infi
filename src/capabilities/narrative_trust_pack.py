"""Narrative Trust Pack — governed export for Story Forge → Beatbox → Speakers."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mechanic.common import derive_claim_status, sha256_file

PACK_VERSION = "narrative_trust_pack.v1"
DEFAULT_NARRATIVE_ROOT = Path(".runtime/narrative")
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "narrative_trust_pack.v1.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def pack_dir(pack_id: str, *, root: Path | None = None) -> Path:
    base = (root or DEFAULT_NARRATIVE_ROOT).expanduser().resolve()
    return base / pack_id


def pack_path(pack_id: str, *, root: Path | None = None) -> Path:
    return pack_dir(pack_id, root=root) / "narrative_trust_pack.v1.json"


def build_stage_envelope(
    *,
    stage_name: str,
    artifact_path: str | Path,
    author: str,
    ul_substrate: dict[str, Any] | None = None,
    claim_label: str = "asserted",
) -> dict[str, Any]:
    path = Path(artifact_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"stage artifact not found: {path}")
    envelope = {
        "stage_id": f"stage-{uuid.uuid4().hex[:12]}",
        "stage_name": stage_name,
        "artifact_hash": sha256_file(path),
        "artifact_path": str(path),
        "claim_label": claim_label,
        "author": author,
        "created_at_utc": _utc_now_iso(),
    }
    if ul_substrate:
        envelope["ul_substrate"] = ul_substrate
    return envelope


def build_pack_from_capability_output(
    output: dict[str, Any],
    *,
    pack_id: str,
    author: str,
    story_forge_artifact_path: str | Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build NTP from story_forge_audio capability result dict."""
    stages: list[dict[str, Any]] = []
    ul_substrate = output.get("ul_substrate") if isinstance(output.get("ul_substrate"), dict) else None

    sf_path = story_forge_artifact_path
    if sf_path is None:
        for candidate_key in ("metadata_path", "artifact_path"):
            if output.get(candidate_key):
                sf_path = output[candidate_key]
                break
    if sf_path:
        stages.append(
            build_stage_envelope(
                stage_name="story_forge",
                artifact_path=sf_path,
                author=author,
                ul_substrate=ul_substrate,
            )
        )

    music_path = output.get("music_stem_path") or output.get("beatbox_path")
    if music_path:
        stages.append(
            build_stage_envelope(
                stage_name="beatbox",
                artifact_path=music_path,
                author=author,
            )
        )

    final_audio = output.get("final_audio_path")
    if final_audio:
        stages.append(
            build_stage_envelope(
                stage_name="speakers",
                artifact_path=final_audio,
                author=author,
            )
        )

    if not stages:
        raise ValueError("capability output missing stage artifact paths")

    now = _utc_now_iso()
    pack = {
        "pack_version": PACK_VERSION,
        "pack_id": pack_id,
        "session_id": output.get("session_id") or "",
        "stages": stages,
        "claim_label": derive_claim_status([stage["claim_label"] for stage in stages]),
        "export_ready": False,
        "created_at_utc": now,
        "updated_at_utc": now,
    }
    persist_pack(pack, root=root)
    return pack


def persist_pack(pack: dict[str, Any], *, root: Path | None = None) -> Path:
    pack_id = str(pack["pack_id"])
    out_dir = pack_dir(pack_id, root=root)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stage in pack.get("stages") or []:
        stage_dir = out_dir / "stages" / str(stage.get("stage_name") or "unknown")
        stage_dir.mkdir(parents=True, exist_ok=True)
    path = pack_path(pack_id, root=root)
    pack["updated_at_utc"] = _utc_now_iso()
    path.write_text(json.dumps(pack, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_pack(pack_id: str, *, root: Path | None = None) -> dict[str, Any]:
    path = pack_path(pack_id, root=root)
    if not path.is_file():
        raise FileNotFoundError(f"pack not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_pack_integrity(pack: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    for stage in pack.get("stages") or []:
        path = Path(str(stage.get("artifact_path") or ""))
        expected = str(stage.get("artifact_hash") or "")
        if not path.is_file():
            failures.append(f"missing artifact: {path}")
            continue
        actual = sha256_file(path)
        if expected and actual != expected:
            failures.append(f"hash mismatch: {stage.get('stage_name')} ({path.name})")

    if failures:
        return {"ok": False, "claim_label": "rejected", "failures": failures}
    return {"ok": True, "claim_label": "asserted", "failures": []}


def apply_signoff(
    pack: dict[str, Any],
    *,
    signoff_by: str,
    notes: str = "",
    override_command: str = "none",
) -> dict[str, Any]:
    verify = verify_pack_integrity(pack)
    if not verify.get("ok"):
        pack["claim_label"] = "rejected"
        pack["export_ready"] = False
        pack["signoff_error"] = verify.get("failures")
        return pack

    pack["signoff"] = {
        "signoff_by": signoff_by,
        "signoff_at_utc": _utc_now_iso(),
        "override_command": override_command,
        "notes": notes[:500],
    }
    pack["claim_label"] = "proven"
    pack["export_ready"] = True
    pack.pop("signoff_error", None)
    return pack
