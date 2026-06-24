"""CRK-1 Interpretive Lineage Tree — ancestry queries over interpretation frames."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.crk1.errors import ConstitutionalError

if TYPE_CHECKING:
    from src.crk1.runtime_facade import CRK1Runtime


class InterpretiveLineageTree:
    """
    Records and queries interpretive frame ancestry (K7, K9, K10, K11).
    Stored as replayable lineage fields on InterpretationObjects in the Semantic Ledger.
    """

    def __init__(self, runtime: CRK1Runtime) -> None:
        self.runtime = runtime

    def _load(self, frame_id: str):
        return self.runtime.load_interpretation(frame_id)

    def get_ancestors(self, frame_id: str) -> list[str]:
        """All upstream frames in lineage order (roots first)."""
        frame = self._load(frame_id)
        ancestors: list[str] = []
        for parent_id in frame.lineage:
            if parent_id not in ancestors:
                ancestors.append(parent_id)
            for upstream in self.get_ancestors(parent_id):
                if upstream not in ancestors:
                    ancestors.append(upstream)
        return ancestors

    def get_descendants(self, frame_id: str) -> list[str]:
        """All downstream frames that list frame_id in their lineage."""
        descendants: list[str] = []
        for item in self.runtime.get_all_interpretations():
            if frame_id not in item.lineage:
                continue
            if item.id not in descendants:
                descendants.append(item.id)
            for child in self.get_descendants(item.id):
                if child not in descendants:
                    descendants.append(child)
        return descendants

    def get_siblings(self, frame_id: str) -> list[str]:
        """Frames sharing at least one parent in lineage."""
        frame = self._load(frame_id)
        if not frame.lineage:
            return [
                item.id
                for item in self.runtime.get_all_interpretations()
                if not item.lineage and item.id != frame_id
            ]
        frame_parents = set(frame.lineage)
        return [
            item.id
            for item in self.runtime.get_all_interpretations()
            if item.id != frame_id and frame_parents & set(item.lineage)
        ]

    def assert_lineage_integrity(self) -> None:
        """Reject frames whose lineage references unknown ancestors."""
        known = {item.id for item in self.runtime.get_all_interpretations()}
        for frame in self.runtime.get_all_interpretations():
            for parent_id in frame.lineage:
                if parent_id not in known:
                    raise ConstitutionalError(
                        f"Unknown lineage parent {parent_id} for frame {frame.id}",
                    )
