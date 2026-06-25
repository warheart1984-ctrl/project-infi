from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nova.law_kernel.bootstrap import make_law_kernel_stack
from nova.law_kernel.models import Intent
from nova.law_kernel.router import LawfulIntentRouter


@dataclass
class Specimen:
    id: str
    router: LawfulIntentRouter
    metadata: dict[str, Any] = field(default_factory=dict)


class SpecimenManager:
    def __init__(self) -> None:
        self._specimens: dict[str, Specimen] = {}

    def create(self, specimen_id: str, metadata: dict[str, Any] | None = None) -> Specimen:
        router = make_law_kernel_stack()
        specimen = Specimen(id=specimen_id, router=router, metadata=metadata or {})
        self._specimens[specimen_id] = specimen
        return specimen

    def route(self, specimen_id: str, intent: Intent, **ctx: Any) -> dict[str, Any]:
        specimen = self._specimens[specimen_id]
        return specimen.router.route(intent, **ctx)

    def get(self, specimen_id: str) -> Specimen:
        return self._specimens[specimen_id]
