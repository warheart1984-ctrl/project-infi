"""Law-scoped L0–L2 caches for Cloud Forge (Phase 3)."""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import re
import threading
from pathlib import Path
from typing import Any

from src.cloud_forge.types import CACHE_MODES, CACHE_ORDER, LawEnvelope, TaskSignature, cap_cache_mode


CACHE_STORE_ID = "aais.cloud_forge.cache"
CACHE_STORE_VERSION = "0.1"

_TENANT_RE = re.compile(r"^[a-zA-Z0-9._-]{1,64}$")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _default_cache_root() -> Path:
    configured = os.getenv("CLOUD_FORGE_CACHE_ROOT")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[2] / ".runtime" / "cloud_forge" / "cache"


def _runtime_flags_dir() -> Path:
    return Path(__file__).resolve().parents[2] / ".runtime" / "cloud_forge"


def _validate_tenant_id(tenant_id: str) -> str:
    tid = str(tenant_id or "default").strip() or "default"
    if not _TENANT_RE.match(tid):
        raise ValueError(f"invalid tenant_id for cache key: {tid}")
    return tid


def _law_scope(law: LawEnvelope | dict[str, Any]) -> tuple[str, str]:
    if isinstance(law, LawEnvelope):
        return law.law_id, law.law_version
    data = dict(law or {})
    return str(data.get("law_id") or "unknown"), str(data.get("law_version") or "unknown")


def build_l1_key(
    tenant_id: str,
    law_id: str,
    law_version: str,
    normalized_question: str,
) -> str:
    """Contract: hash(tenant, law_id, normalized_question) + law_version in record."""
    tenant_id = _validate_tenant_id(tenant_id)
    question = " ".join(str(normalized_question or "").split()).strip().lower()
    material = _stable_json(
        {
            "tenant_id": tenant_id,
            "law_id": law_id,
            "normalized_question": question,
        }
    )
    return _digest(material)


def build_l2_key(
    tenant_id: str,
    law_id: str,
    law_version: str,
    pattern_class: str,
    domain: str | None,
    normalized_prompt_hash: str | None,
) -> str:
    tenant_id = _validate_tenant_id(tenant_id)
    material = _stable_json(
        {
            "tenant_id": tenant_id,
            "law_id": law_id,
            "law_version": law_version,
            "pattern_class": pattern_class,
            "domain": domain or "",
            "normalized_prompt_hash": normalized_prompt_hash or "",
        }
    )
    return _digest(material)


def build_l0_key(
    tenant_id: str,
    law_id: str,
    law_version: str,
    tool_name: str,
    tool_input: str,
) -> str:
    tenant_id = _validate_tenant_id(tenant_id)
    material = f"{tenant_id}::{law_id}::{law_version}::{tool_name}::{tool_input}"
    return _digest(material)


class CloudForgeCacheStore:
    """File-backed law-scoped cache (L0 tools, L1 answers, L2 plans)."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or _default_cache_root())
        self._lock = threading.Lock()
        self.root.mkdir(parents=True, exist_ok=True)

    def _layer_path(self, layer: str, key: str) -> Path:
        return self.root / layer / f"{key}.json"

    def _read_entry(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _write_entry(self, path: Path, entry: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_stable_json(entry) + "\n", encoding="utf-8")

    def _law_match(self, entry: dict[str, Any], law_id: str, law_version: str) -> bool:
        return (
            str(entry.get("law_id") or "") == law_id
            and str(entry.get("law_version") or "") == law_version
        )

    def l0_get(
        self,
        tenant_id: str,
        law: LawEnvelope | dict[str, Any],
        tool_name: str,
        tool_input: str,
    ) -> str | None:
        law_id, law_version = _law_scope(law)
        key = build_l0_key(tenant_id, law_id, law_version, tool_name, tool_input)
        entry = self._read_entry(self._layer_path("L0", key))
        if not entry or not self._law_match(entry, law_id, law_version):
            return None
        if str(entry.get("tenant_id")) != _validate_tenant_id(tenant_id):
            return None
        return str(entry.get("result") or "")

    def l0_set(
        self,
        tenant_id: str,
        law: LawEnvelope | dict[str, Any],
        tool_name: str,
        tool_input: str,
        result: str,
    ) -> dict[str, Any]:
        law_id, law_version = _law_scope(law)
        tenant_id = _validate_tenant_id(tenant_id)
        key = build_l0_key(tenant_id, law_id, law_version, tool_name, tool_input)
        entry = {
            "cache_store_id": CACHE_STORE_ID,
            "cache_store_version": CACHE_STORE_VERSION,
            "layer": "L0",
            "cache_key": key,
            "tenant_id": tenant_id,
            "law_id": law_id,
            "law_version": law_version,
            "tool_name": tool_name,
            "stored_at": _utc_now_iso(),
            "result": result,
        }
        with self._lock:
            self._write_entry(self._layer_path("L0", key), entry)
        return entry

    def l1_get(
        self,
        tenant_id: str,
        law: LawEnvelope | dict[str, Any],
        normalized_question: str,
    ) -> dict[str, Any] | None:
        law_id, law_version = _law_scope(law)
        key = build_l1_key(tenant_id, law_id, law_version, normalized_question)
        entry = self._read_entry(self._layer_path("L1", key))
        if not entry:
            return None
        if not self._law_match(entry, law_id, law_version):
            return None
        if str(entry.get("tenant_id")) != _validate_tenant_id(tenant_id):
            return None
        return entry

    def l1_set(
        self,
        tenant_id: str,
        law: LawEnvelope | dict[str, Any],
        normalized_question: str,
        answer: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        law_id, law_version = _law_scope(law)
        tenant_id = _validate_tenant_id(tenant_id)
        key = build_l1_key(tenant_id, law_id, law_version, normalized_question)
        entry = {
            "cache_store_id": CACHE_STORE_ID,
            "cache_store_version": CACHE_STORE_VERSION,
            "layer": "L1",
            "cache_key": key,
            "tenant_id": tenant_id,
            "law_id": law_id,
            "law_version": law_version,
            "normalized_question": normalized_question,
            "answer": answer,
            "metadata": dict(metadata or {}),
            "stored_at": _utc_now_iso(),
        }
        with self._lock:
            self._write_entry(self._layer_path("L1", key), entry)
        return entry

    def l2_get(
        self,
        tenant_id: str,
        law: LawEnvelope | dict[str, Any],
        task: TaskSignature,
    ) -> dict[str, Any] | None:
        law_id, law_version = _law_scope(law)
        key = build_l2_key(
            tenant_id,
            law_id,
            law_version,
            task.pattern_class,
            task.domain,
            task.normalized_prompt_hash,
        )
        entry = self._read_entry(self._layer_path("L2", key))
        if not entry:
            return None
        if not self._law_match(entry, law_id, law_version):
            return None
        if str(entry.get("tenant_id")) != _validate_tenant_id(tenant_id):
            return None
        return entry

    def l2_set(
        self,
        tenant_id: str,
        law: LawEnvelope | dict[str, Any],
        task: TaskSignature,
        cognition_plan: dict[str, Any],
    ) -> dict[str, Any]:
        law_id, law_version = _law_scope(law)
        tenant_id = _validate_tenant_id(tenant_id)
        key = build_l2_key(
            tenant_id,
            law_id,
            law_version,
            task.pattern_class,
            task.domain,
            task.normalized_prompt_hash,
        )
        entry = {
            "cache_store_id": CACHE_STORE_ID,
            "cache_store_version": CACHE_STORE_VERSION,
            "layer": "L2",
            "cache_key": key,
            "tenant_id": tenant_id,
            "law_id": law_id,
            "law_version": law_version,
            "pattern_class": task.pattern_class,
            "domain": task.domain,
            "normalized_prompt_hash": task.normalized_prompt_hash,
            "cognition_plan": dict(cognition_plan),
            "stored_at": _utc_now_iso(),
        }
        with self._lock:
            self._write_entry(self._layer_path("L2", key), entry)
        return entry

    def flush(
        self,
        *,
        tenant_id: str | None = None,
        law_id: str | None = None,
        layers: tuple[str, ...] = ("L1", "L2"),
    ) -> int:
        """Remove cache entries; returns count deleted."""
        removed = 0
        with self._lock:
            for layer in layers:
                layer_dir = self.root / layer
                if not layer_dir.exists():
                    continue
                for path in layer_dir.glob("*.json"):
                    entry = self._read_entry(path)
                    if not entry:
                        path.unlink(missing_ok=True)
                        removed += 1
                        continue
                    if tenant_id and str(entry.get("tenant_id")) != tenant_id:
                        continue
                    if law_id and str(entry.get("law_id")) != law_id:
                        continue
                    path.unlink(missing_ok=True)
                    removed += 1
        return removed

    def check_and_apply_flush_flags(self, tenant_id: str) -> list[str]:
        """Honor failsafe flush flag files; return actions taken."""
        actions: list[str] = []
        flags_dir = _runtime_flags_dir()
        global_flag = flags_dir / "cache_flush.all"
        tenant_flag = flags_dir / f"cache_flush.{_validate_tenant_id(tenant_id)}"

        if global_flag.is_file():
            removed = self.flush(layers=("L0", "L1", "L2"))
            actions.append(f"flush.all:{removed}")
            global_flag.unlink(missing_ok=True)

        if tenant_flag.is_file():
            removed = self.flush(tenant_id=_validate_tenant_id(tenant_id), layers=("L1", "L2"))
            actions.append(f"flush.tenant:{removed}")
            tenant_flag.unlink(missing_ok=True)

        return actions


_default_store: CloudForgeCacheStore | None = None


def get_default_cache_store() -> CloudForgeCacheStore:
    global _default_store
    if _default_store is None:
        _default_store = CloudForgeCacheStore()
    return _default_store


def effective_cache_mode(plan_mode: str, law: LawEnvelope | dict[str, Any]) -> str:
    law_obj = law if isinstance(law, LawEnvelope) else LawEnvelope.from_dict(law)
    ceiling = law_obj.forbid_cache_above
    return cap_cache_mode(plan_mode, ceiling)


def resolve_cache(
    *,
    tenant_id: str,
    law: LawEnvelope | dict[str, Any],
    task: TaskSignature,
    cache_mode: str,
    store: CloudForgeCacheStore | None = None,
    normalized_question: str | None = None,
) -> dict[str, Any]:
    """
    Probe L2 then L1 per plan cache_mode.

    Returns cache_resolution dict (hit/miss, layer, payload).
    """
    store = store or get_default_cache_store()
    store.check_and_apply_flush_flags(tenant_id)

    mode = str(cache_mode or "off").strip()
    if mode not in CACHE_MODES or mode == "off":
        return _wrap_ul_payload({"status": "miss", "layer": None, "cache_mode": mode})

    question = normalized_question
    if not question and task.normalized_prompt_hash:
        question = task.normalized_prompt_hash

    if CACHE_ORDER[mode] >= CACHE_ORDER["L2"]:
        hit = store.l2_get(tenant_id, law, task)
        if hit:
            return _wrap_ul_payload({
                "status": "hit",
                "layer": "L2",
                "cache_mode": mode,
                "cache_key": hit.get("cache_key"),
                "cognition_plan": hit.get("cognition_plan"),
                "stored_at": hit.get("stored_at"),
                "claim_status": "asserted",
            })

    if CACHE_ORDER[mode] >= CACHE_ORDER["L1"] and question:
        hit = store.l1_get(tenant_id, law, question)
        if hit:
            return _wrap_ul_payload({
                "status": "hit",
                "layer": "L1",
                "cache_mode": mode,
                "cache_key": hit.get("cache_key"),
                "answer": hit.get("answer"),
                "metadata": hit.get("metadata") or {},
                "stored_at": hit.get("stored_at"),
                "claim_status": "asserted",
            })

    return _wrap_ul_payload({"status": "miss", "layer": None, "cache_mode": mode})


def persist_cache_outcomes(
    *,
    tenant_id: str,
    law: LawEnvelope | dict[str, Any],
    task: TaskSignature,
    cache_mode: str,
    cognition_plan: dict[str, Any],
    store: CloudForgeCacheStore | None = None,
    store_answer: str | None = None,
    store_plan: bool = False,
    answer_metadata: dict[str, Any] | None = None,
    normalized_question: str | None = None,
) -> dict[str, Any]:
    """Write L1/L2 entries after a successful governed response."""
    store = store or get_default_cache_store()
    mode = str(cache_mode or "off")
    persisted: dict[str, Any] = {"layers": []}

    question = normalized_question or task.normalized_prompt_hash or ""
    if CACHE_ORDER.get(mode, 0) >= CACHE_ORDER["L1"] and store_answer and question:
        entry = store.l1_set(
            tenant_id,
            law,
            question,
            store_answer,
            metadata=answer_metadata,
        )
        persisted["layers"].append({"layer": "L1", "cache_key": entry.get("cache_key")})

    if CACHE_ORDER.get(mode, 0) >= CACHE_ORDER["L2"] and store_plan:
        entry = store.l2_set(tenant_id, law, task, cognition_plan)
        persisted["layers"].append({"layer": "L2", "cache_key": entry.get("cache_key")})

    return persisted
