from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass, replace
from typing import Any


@dataclass
class Constitution:
    invariants: list[Any]
    capabilities: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.invariants = list(self.invariants)
        self.capabilities = list(self.capabilities)
        self.history = list(self.history)

    def validate(self, snapshot: dict[str, Any]) -> bool:
        for invariant in self.invariants:
            check_fn = getattr(invariant, "check_fn", None)
            if not callable(check_fn):
                return False
            if not check_fn(snapshot):
                return False
        return True

    def list_ids(self) -> list[str]:
        return [
            str(getattr(invariant, "invariant_id", getattr(invariant, "id", "")))
            for invariant in self.invariants
            if getattr(invariant, "invariant_id", getattr(invariant, "id", ""))
        ]

    def get_invariant(self, invariant_id: str) -> Any | None:
        for invariant in self.invariants:
            current_id = str(getattr(invariant, "invariant_id", getattr(invariant, "id", "")))
            if current_id == invariant_id:
                return invariant
        return None

    def apply_promotion(self, change: dict[str, Any]) -> bool:
        kind = str(change.get("kind", ""))
        applied = False
        normalized_change = dict(change)

        if kind == "AddInvariant":
            invariant = self._extract_invariant(normalized_change)
            if invariant is not None:
                invariant_id = str(getattr(invariant, "invariant_id", getattr(invariant, "id", "")))
                if invariant_id and self.get_invariant(invariant_id) is None:
                    self.invariants.append(invariant)
                    applied = True
        elif kind == "UpdateInvariant":
            target_id = str(
                normalized_change.get("invariant_id")
                or normalized_change.get("payload", {}).get("invariant_id", "")
            )
            if target_id:
                invariant = self.get_invariant(target_id)
                if invariant is not None:
                    replacement = self._merge_invariant(invariant, normalized_change)
                    index = self.invariants.index(invariant)
                    self.invariants[index] = replacement
                    applied = True
        elif kind == "RemoveInvariant":
            target_id = str(
                normalized_change.get("invariant_id")
                or normalized_change.get("payload", {}).get("invariant_id", "")
            )
            if target_id:
                before = len(self.invariants)
                self.invariants = [
                    invariant
                    for invariant in self.invariants
                    if str(getattr(invariant, "invariant_id", getattr(invariant, "id", ""))) != target_id
                ]
                applied = len(self.invariants) != before
        else:
            capability_id = str(
                normalized_change.get("capability_id")
                or normalized_change.get("payload", {}).get("capability_id", "")
            )
            if capability_id:
                self.capabilities.append(
                    {
                        "capability_id": capability_id,
                        "kind": kind or "CapabilityPromotion",
                        "payload": dict(normalized_change),
                    }
                )
                applied = True

        self.history.append({"applied": applied, "change": normalized_change})
        return applied

    def _extract_invariant(self, change: dict[str, Any]) -> Any | None:
        invariant = change.get("invariant")
        if invariant is not None:
            return invariant
        payload = change.get("payload", {})
        if isinstance(payload, dict):
            return payload.get("invariant")
        return None

    def _merge_invariant(self, invariant: Any, change: dict[str, Any]) -> Any:
        payload = dict(change.get("payload", {}))
        replacement = change.get("invariant")
        if replacement is not None:
            return replacement
        if isinstance(payload, dict):
            if is_dataclass(invariant):
                valid_fields = {field.name for field in fields(invariant)}
                updates: dict[str, Any] = {}
                for key, value in payload.items():
                    if key in valid_fields:
                        updates[key] = value
                if updates:
                    return replace(invariant, **updates)
            for key, value in payload.items():
                if hasattr(invariant, key):
                    try:
                        setattr(invariant, key, value)
                    except Exception:
                        continue
        return invariant
