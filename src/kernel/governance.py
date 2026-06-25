"""CRK-T2 governance facade — kernel version and amendment ratification."""

from __future__ import annotations

import logging
from typing import Any

from src.kernel.amendment_ledger import InMemoryAmendmentStore, KernelAmendmentLedger

logger = logging.getLogger(__name__)

_SHARED_STORE = InMemoryAmendmentStore()


class Governance:
    """Runtime governance hook for kernel amendment proposals."""

    _instance: Governance | None = None

    def __init__(self, *, store: InMemoryAmendmentStore | None = None) -> None:
        self._kernel_version = 1
        self._store = store or _SHARED_STORE
        self._ledger = KernelAmendmentLedger(self._store)

    @classmethod
    def current(cls) -> Governance:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
        _SHARED_STORE._rows.clear()
        _SHARED_STORE._counter = 0
        from src.kernel.identity_history_ledger import reset_identity_ledger

        reset_identity_ledger()

    def amendment_store(self) -> InMemoryAmendmentStore:
        return self._store

    def amendment_ledger(self) -> KernelAmendmentLedger:
        return self._ledger

    def current_kernel_version(self) -> int:
        return self._kernel_version

    def set_kernel_version(self, version: int) -> None:
        self._kernel_version = version

    def propose_kernel_amendment(
        self,
        *,
        reason: str,
        signals: list[float],
        insufficiency: float,
        ratify: bool = False,
    ) -> bool:
        if not ratify:
            logger.info(
                "CRK-T2 amendment proposed (pending ratification): %s insufficiency=%.4f",
                reason,
                insufficiency,
            )
            return False
        self._kernel_version += 1
        from src.continuity.identity_object import DEFAULT_IDENTITY
        from src.kernel.identity_history_ledger import shared_identity_ledger

        try:
            from src.constitutional_cockpit_routes import _ensure_ledgers

            law_store, _, _, _, _, _ = _ensure_ledgers()
            epoch = int(law_store.get_current_epoch())
        except Exception:
            epoch = 0
        shared_identity_ledger().append(
            identity=DEFAULT_IDENTITY,
            epoch=epoch,
            kernel_version=self._kernel_version,
            reason=f"kernel-amendment-ratified: {reason}",
        )
        logger.info(
            "CRK-T2 amendment ratified: %s insufficiency=%.4f kernel_version=%s",
            reason,
            insufficiency,
            self._kernel_version,
        )
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "kernel_version": self._kernel_version,
            "amendment_count": len(self._ledger.list()),
        }
