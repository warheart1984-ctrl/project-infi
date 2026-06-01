from __future__ import annotations

import base64
import json
import sys
from dataclasses import asdict
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from story_forge.visual_artifact_schema import ImageArtifactRecord, normalize_token, unique_strings


PLACEHOLDER_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Z0WQAAAAASUVORK5CYII="
)


class VisualArtifactStorageError(ValueError):
    pass


def default_artifact_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "artifacts" / "images"
    return Path(__file__).resolve().parents[2] / "artifacts" / "images"


class VisualMemoryStore:
    INDEX_FILENAME = "index.json"

    def __init__(self, root_dir: str | Path | None = None) -> None:
        self.root_dir = Path(root_dir) if root_dir else default_artifact_root()
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, object] | None = None

    def store_artifact(
        self,
        artifact: ImageArtifactRecord,
        *,
        source_image_path: str | Path | None = None,
    ) -> ImageArtifactRecord:
        index = self._load_index()
        if not artifact.artifact_id:
            artifact.artifact_id = self.next_artifact_id()

        cartridge_dir = self.root_dir / artifact.cartridge_id
        cartridge_dir.mkdir(parents=True, exist_ok=True)
        image_path = cartridge_dir / f"{artifact.artifact_id}.png"
        metadata_path = cartridge_dir / f"{artifact.artifact_id}.json"

        self._write_image(image_path, source_image_path)
        artifact.image_path = str(image_path)
        artifact.metadata_path = str(metadata_path)
        metadata_path.write_text(json.dumps(asdict(artifact), indent=2), encoding="utf-8")

        artifacts = dict(index.get("artifacts", {}))
        artifacts[artifact.artifact_id] = {
            "artifact_id": artifact.artifact_id,
            "metadata_path": self._relative_path(metadata_path),
            "image_path": self._relative_path(image_path),
            "timestamp": artifact.timestamp,
            "cartridge_id": artifact.cartridge_id,
            "narrative_arc": artifact.narrative_arc,
            "major": artifact.major,
        }
        index["artifacts"] = artifacts
        self._append_index_value(index, "by_cartridge", artifact.cartridge_id, artifact.artifact_id)
        self._append_index_value(index, "by_event_type", artifact.event_type, artifact.artifact_id)
        self._append_index_value(index, "by_arc", artifact.narrative_arc, artifact.artifact_id)
        self._append_index_value(index, "by_location", artifact.location, artifact.artifact_id)
        for character_id in artifact.character_ids:
            self._append_index_value(index, "by_character", character_id, artifact.artifact_id)
        for symbol in artifact.symbols:
            self._append_index_value(index, "by_symbol", symbol, artifact.artifact_id)

        current_counter = int(index.get("counters", {}).get("artifact", 0))
        parsed_counter = self._parse_artifact_counter(artifact.artifact_id)
        index["counters"] = {"artifact": max(current_counter, parsed_counter)}
        self._save_index(index)
        return artifact

    def next_artifact_id(self) -> str:
        index = self._load_index()
        counters = dict(index.get("counters", {}))
        next_value = int(counters.get("artifact", 0)) + 1
        counters["artifact"] = next_value
        index["counters"] = counters
        self._save_index(index)
        return f"img_{next_value:04d}"

    def get_artifact(self, artifact_id: str) -> ImageArtifactRecord | None:
        index = self._load_index()
        artifact_entry = dict(index.get("artifacts", {})).get(artifact_id)
        if not artifact_entry:
            return None
        metadata_path = self.root_dir / str(artifact_entry.get("metadata_path", ""))
        if not metadata_path.exists():
            self.rebuild_index()
            artifact_entry = dict(self._load_index().get("artifacts", {})).get(artifact_id)
            if not artifact_entry:
                return None
            metadata_path = self.root_dir / str(artifact_entry.get("metadata_path", ""))
            if not metadata_path.exists():
                return None
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
        return ImageArtifactRecord(**payload)

    def list_artifacts(self, cartridge_id: str | None = None) -> list[ImageArtifactRecord]:
        index = self._load_index()
        artifact_ids = list(dict(index.get("artifacts", {})).keys())
        if cartridge_id:
            artifact_ids = list(dict(index.get("by_cartridge", {})).get(cartridge_id, []))
        artifacts = [self.get_artifact(artifact_id) for artifact_id in artifact_ids]
        return self._sort_artifacts([artifact for artifact in artifacts if artifact is not None])

    def find_by_character(self, character_id: str) -> list[ImageArtifactRecord]:
        return self._artifacts_for_index("by_character", character_id)

    def find_by_location(self, location: str) -> list[ImageArtifactRecord]:
        return self._artifacts_for_index("by_location", location)

    def find_by_symbol(self, symbol: str) -> list[ImageArtifactRecord]:
        return self._artifacts_for_index("by_symbol", symbol)

    def find_by_event_type(self, event_type: str) -> list[ImageArtifactRecord]:
        return self._artifacts_for_index("by_event_type", event_type)

    def find_by_arc(self, narrative_arc: str) -> list[ImageArtifactRecord]:
        return self._artifacts_for_index("by_arc", narrative_arc)

    def rebuild_index(self) -> dict[str, object]:
        index = self._empty_index()
        highest_counter = 0
        for metadata_path in sorted(self.root_dir.rglob("*.json")):
            if metadata_path.name == self.INDEX_FILENAME:
                continue
            try:
                payload = json.loads(metadata_path.read_text(encoding="utf-8"))
                artifact = ImageArtifactRecord(**payload)
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
            image_path = metadata_path.with_suffix(".png")
            artifacts = dict(index.get("artifacts", {}))
            artifacts[artifact.artifact_id] = {
                "artifact_id": artifact.artifact_id,
                "metadata_path": self._relative_path(metadata_path),
                "image_path": self._relative_path(image_path),
                "timestamp": artifact.timestamp,
                "cartridge_id": artifact.cartridge_id,
                "narrative_arc": artifact.narrative_arc,
                "major": artifact.major,
            }
            index["artifacts"] = artifacts
            self._append_index_value(index, "by_cartridge", artifact.cartridge_id, artifact.artifact_id)
            self._append_index_value(index, "by_event_type", artifact.event_type, artifact.artifact_id)
            self._append_index_value(index, "by_arc", artifact.narrative_arc, artifact.artifact_id)
            self._append_index_value(index, "by_location", artifact.location, artifact.artifact_id)
            for character_id in artifact.character_ids:
                self._append_index_value(index, "by_character", character_id, artifact.artifact_id)
            for symbol in artifact.symbols:
                self._append_index_value(index, "by_symbol", symbol, artifact.artifact_id)
            highest_counter = max(highest_counter, self._parse_artifact_counter(artifact.artifact_id))
        index["counters"] = {"artifact": highest_counter}
        self._save_index(index)
        return index

    def _artifacts_for_index(self, index_name: str, key: str) -> list[ImageArtifactRecord]:
        normalized_key = normalize_token(key)
        if not normalized_key:
            return []
        index = self._load_index()
        artifact_ids = list(dict(index.get(index_name, {})).get(normalized_key, []))
        artifacts = [self.get_artifact(artifact_id) for artifact_id in artifact_ids]
        return self._sort_artifacts([artifact for artifact in artifacts if artifact is not None])

    def _sort_artifacts(self, artifacts: list[ImageArtifactRecord]) -> list[ImageArtifactRecord]:
        return sorted(
            artifacts,
            key=lambda artifact: (artifact.timestamp, artifact.artifact_id),
            reverse=True,
        )

    def _write_image(self, destination: Path, source_image_path: str | Path | None) -> None:
        if source_image_path:
            source = Path(source_image_path)
            if not source.exists():
                raise VisualArtifactStorageError(
                    f"Source image was not found for artifact storage: {source}"
                )
            if not source.is_file():
                raise VisualArtifactStorageError(
                    f"Source image path was not a file for artifact storage: {source}"
                )
            normalized_bytes = self._normalize_source_image_to_png(source)
            destination.write_bytes(normalized_bytes)
            return
        destination.write_bytes(PLACEHOLDER_PNG_BYTES)

    def _normalize_source_image_to_png(self, source: Path) -> bytes:
        raw_bytes = source.read_bytes()
        if not raw_bytes:
            raise VisualArtifactStorageError(
                f"Source image was empty for artifact storage: {source}"
            )

        try:
            with Image.open(BytesIO(raw_bytes)) as image:
                image.load()
                working = image.copy()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise VisualArtifactStorageError(
                f"Source image was not renderable for artifact storage: {source}"
            ) from exc

        if working.mode not in {"1", "L", "LA", "P", "RGB", "RGBA"}:
            working = working.convert("RGBA")

        buffer = BytesIO()
        working.save(buffer, format="PNG")
        normalized_bytes = buffer.getvalue()
        if not normalized_bytes:
            raise VisualArtifactStorageError(
                f"Source image normalized to an empty PNG for artifact storage: {source}"
            )
        return normalized_bytes

    def _load_index(self) -> dict[str, object]:
        if self._index is not None:
            return self._index
        index_path = self.root_dir / self.INDEX_FILENAME
        if not index_path.exists():
            if self._has_metadata_sidecars():
                return self.rebuild_index()
            self._index = self._empty_index()
            self._save_index(self._index)
            return self._index
        try:
            self._index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            if self._has_metadata_sidecars():
                return self.rebuild_index()
            self._index = self._empty_index()
            self._save_index(self._index)
            return self._index
        if self._index_needs_rebuild(self._index):
            return self.rebuild_index()
        return self._index

    def _save_index(self, index: dict[str, object]) -> None:
        index_path = self.root_dir / self.INDEX_FILENAME
        index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
        self._index = index

    def _empty_index(self) -> dict[str, object]:
        return {
            "artifacts": {},
            "by_cartridge": {},
            "by_character": {},
            "by_location": {},
            "by_symbol": {},
            "by_event_type": {},
            "by_arc": {},
            "counters": {"artifact": 0},
        }

    def _append_index_value(
        self,
        index: dict[str, object],
        key: str,
        lookup_value: str,
        artifact_id: str,
    ) -> None:
        normalized = normalize_token(lookup_value)
        if not normalized:
            return
        bucket = dict(index.get(key, {}))
        existing = unique_strings(bucket.get(normalized, []))
        if artifact_id not in existing:
            existing.append(artifact_id)
        bucket[normalized] = existing
        index[key] = bucket

    def _relative_path(self, path: Path) -> str:
        return path.resolve().relative_to(self.root_dir.resolve()).as_posix()

    def _parse_artifact_counter(self, artifact_id: str) -> int:
        tail = str(artifact_id).split("_")[-1]
        return int(tail) if tail.isdigit() else 0

    def _has_metadata_sidecars(self) -> bool:
        return any(True for _ in self._iter_metadata_sidecars())

    def _iter_metadata_sidecars(self):
        for metadata_path in self.root_dir.rglob("*.json"):
            if metadata_path.name == self.INDEX_FILENAME:
                continue
            yield metadata_path

    def _index_needs_rebuild(self, index: dict[str, object]) -> bool:
        if dict(index.get("artifacts", {})):
            return False
        return self._has_metadata_sidecars()
