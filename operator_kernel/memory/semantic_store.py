"""Offline-first semantic memory (JSONL + hash embeddings + cosine search)."""

from __future__ import annotations

import hashlib
import json
import math
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from operator_kernel.memory.paths import memory_paths


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_embedding(text: str, dims: int = 256) -> list[float]:
    vec = [0.0] * dims
    tokens = text.lower().split()
    if not tokens:
        return vec
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for i in range(dims):
            vec[i] += (digest[i % len(digest)] / 255.0) - 0.5
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class SemanticStore:
    def __init__(self, store_path: Path | None = None) -> None:
        paths = memory_paths()
        self.path = store_path or paths.semantic
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        project_id: str,
        content: str,
        *,
        task_id: str | None = None,
        item_type: str = "note",
    ) -> dict[str, Any]:
        text = content.strip()
        if not text:
            return {}
        item = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "task_id": task_id,
            "type": item_type,
            "content": text[:4000],
            "embedding": _hash_embedding(text),
            "timestamp": _utc_now(),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        return item

    def _load_items(self, project_id: str) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        items: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("project_id") == project_id:
                    items.append(row)
        return items

    def search(self, project_id: str, query: str, *, top_k: int = 5) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []
        q_embed = _hash_embedding(query)
        scored: list[tuple[float, dict[str, Any]]] = []
        for item in self._load_items(project_id):
            emb = item.get("embedding")
            if not isinstance(emb, list):
                emb = _hash_embedding(str(item.get("content") or ""))
            score = _cosine(q_embed, [float(x) for x in emb])
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for score, item in scored[:top_k] if score > 0.05]

    def summarize_for_prompt(self, project_id: str, query: str, *, top_k: int = 5) -> str:
        hits = self.search(project_id, query, top_k=top_k)
        if not hits:
            return ""
        lines = ["Relevant past work:"]
        for hit in hits:
            snippet = str(hit.get("content") or "").replace("\n", " ").strip()
            if snippet:
                lines.append(f"- {snippet[:240]}")
        return "\n".join(lines) if len(lines) > 1 else ""
