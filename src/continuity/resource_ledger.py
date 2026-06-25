"""Resource Ledger — constitutional ResourceObject store (CRK-1)."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

RESOURCE_LEDGER_SPEC_ID = "RESOURCE-LEDGER"
RESOURCE_LEDGER_SQL = Path(__file__).resolve().parents[2] / "fixtures" / "continuity" / "resource_ledger.sql"


class ResourceType(str, Enum):
    TIME = "time"
    MONEY = "money"
    PEOPLE = "people"
    INFRA = "infra"
    ATTENTION = "attention"
    OTHER = "other"


class ResourceStatus(str, Enum):
    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    FROZEN = "frozen"
    RETIRED = "retired"


@dataclass
class ResourceAllocation:
    decision_id: str
    amount: float
    unit: str
    epoch: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "amount": self.amount,
            "unit": self.unit,
            "epoch": self.epoch,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ResourceAllocation:
        return cls(
            decision_id=str(payload["decision_id"]),
            amount=float(payload["amount"]),
            unit=str(payload["unit"]),
            epoch=int(payload["epoch"]),
        )


@dataclass
class ResourceObject:
    id: str
    type: str
    label: str
    quantity_total: float
    quantity_allocated: float
    quantity_unit: str
    constraints: list[dict[str, Any]] = field(default_factory=list)
    allocations: list[ResourceAllocation] = field(default_factory=list)
    status: ResourceStatus = ResourceStatus.ACTIVE
    epoch: int = 0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "quantity": {
                "total": self.quantity_total,
                "allocated": self.quantity_allocated,
                "unit": self.quantity_unit,
            },
            "constraints": list(self.constraints),
            "allocations": [item.to_dict() for item in self.allocations],
            "status": self.status.value,
            "epoch": self.epoch,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ResourceObject:
        quantity = dict(payload.get("quantity") or {})
        return cls(
            id=str(payload["id"]),
            type=str(payload["type"]),
            label=str(payload.get("label") or ""),
            quantity_total=float(
                quantity.get("total", payload.get("quantity_total", 0))
            ),
            quantity_allocated=float(
                quantity.get("allocated", payload.get("quantity_allocated", 0))
            ),
            quantity_unit=str(
                quantity.get("unit", payload.get("quantity_unit", ""))
            ),
            constraints=[dict(item) for item in payload.get("constraints") or []],
            allocations=[
                ResourceAllocation.from_dict(item)
                for item in payload.get("allocations") or []
            ],
            status=ResourceStatus(str(payload.get("status") or ResourceStatus.ACTIVE.value)),
            epoch=int(payload.get("epoch") or 0),
            created_at=str(payload.get("created_at") or ""),
            updated_at=str(payload.get("updated_at") or ""),
        )


def default_resource_ledger_path() -> Path:
    override = os.environ.get("RESOURCE_LEDGER_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    online = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
    if online:
        return Path(online).expanduser().resolve() / "resource-ledger.sqlite3"
    root = Path(__file__).resolve().parents[2]
    return root / ".runtime" / "online" / "resource-ledger.sqlite3"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def recompute_resource_status(resource: ResourceObject) -> ResourceStatus:
    if resource.status == ResourceStatus.FROZEN:
        return ResourceStatus.FROZEN
    if resource.status == ResourceStatus.RETIRED:
        return ResourceStatus.RETIRED
    if resource.quantity_allocated >= resource.quantity_total:
        return ResourceStatus.EXHAUSTED
    return ResourceStatus.ACTIVE


class ResourceLedgerStore:
    """SQLite-backed ResourceObject ledger."""

    def __init__(self, path: Path | str | None = None) -> None:
        if path == ":memory:":
            self.path = Path(":memory:")
        else:
            self.path = Path(path) if path else default_resource_ledger_path()
        if self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @classmethod
    def in_memory(cls) -> ResourceLedgerStore:
        return cls(path=":memory:")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        sql = RESOURCE_LEDGER_SQL.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(sql)
            conn.commit()

    def add(self, record: ResourceObject) -> ResourceObject:
        now = _now_iso()
        if not record.created_at:
            record = ResourceObject.from_dict({**record.to_dict(), "created_at": now, "updated_at": now})
        record.status = recompute_resource_status(record)
        return self.upsert(record)

    def upsert(self, record: ResourceObject) -> ResourceObject:
        now = _now_iso()
        if not record.updated_at:
            record = ResourceObject.from_dict({**record.to_dict(), "updated_at": now})
        record.status = recompute_resource_status(record)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO resources (
                    id, type, label, quantity_total, quantity_allocated, quantity_unit,
                    constraints_json, allocations_json, status, epoch, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    type = excluded.type,
                    label = excluded.label,
                    quantity_total = excluded.quantity_total,
                    quantity_allocated = excluded.quantity_allocated,
                    quantity_unit = excluded.quantity_unit,
                    constraints_json = excluded.constraints_json,
                    allocations_json = excluded.allocations_json,
                    status = excluded.status,
                    epoch = excluded.epoch,
                    updated_at = excluded.updated_at
                """,
                (
                    record.id,
                    record.type,
                    record.label,
                    record.quantity_total,
                    record.quantity_allocated,
                    record.quantity_unit,
                    json.dumps(record.constraints, sort_keys=True),
                    json.dumps([item.to_dict() for item in record.allocations], sort_keys=True),
                    record.status.value,
                    record.epoch,
                    record.created_at or now,
                    record.updated_at,
                ),
            )
            conn.commit()
        return record

    def get(self, resource_id: str) -> ResourceObject | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list_resources(self, *, status: str | None = None) -> list[ResourceObject]:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM resources WHERE status = ? ORDER BY id",
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM resources ORDER BY id").fetchall()
        return [self._row_to_record(row) for row in rows]

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> ResourceObject:
        return ResourceObject(
            id=str(row["id"]),
            type=str(row["type"]),
            label=str(row["label"] or ""),
            quantity_total=float(row["quantity_total"]),
            quantity_allocated=float(row["quantity_allocated"]),
            quantity_unit=str(row["quantity_unit"]),
            constraints=json.loads(row["constraints_json"] or "[]"),
            allocations=[
                ResourceAllocation.from_dict(item)
                for item in json.loads(row["allocations_json"] or "[]")
            ],
            status=ResourceStatus(str(row["status"])),
            epoch=int(row["epoch"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )


def bootstrap_resource_ledger(
    store: ResourceLedgerStore | None = None,
    *,
    epoch: int = 17,
) -> dict[str, Any]:
    ledger = store or ResourceLedgerStore()
    if ledger.get("RES-2026-0001") is not None:
        return {"seed_resource_id": "RES-2026-0001"}

    now = _now_iso()
    seed = ResourceObject(
        id="RES-2026-0001",
        type=ResourceType.TIME.value,
        label="Operator focus (hours)",
        quantity_total=40.0,
        quantity_allocated=12.0,
        quantity_unit="hours",
        constraints=[
            {
                "id": "RES-C-ATTN-MAX-DAILY",
                "description": "Max 6h/day of deep work",
                "type": "hard",
            }
        ],
        allocations=[
            ResourceAllocation(decision_id="DEC-2026-0001", amount=8.0, unit="hours", epoch=epoch),
            ResourceAllocation(decision_id="DEC-2026-0002", amount=4.0, unit="hours", epoch=epoch),
        ],
        status=ResourceStatus.ACTIVE,
        epoch=epoch,
        created_at=now,
        updated_at=now,
    )
    ledger.add(seed)

    ops = ResourceObject(
        id="RES-TIME-OPS-01",
        type=ResourceType.TIME.value,
        label="Operator time pool",
        quantity_total=40.0,
        quantity_allocated=40.0,
        quantity_unit="hours",
        constraints=[],
        allocations=[
            ResourceAllocation(decision_id="DEC-2026-0001", amount=40.0, unit="hours", epoch=epoch),
        ],
        status=ResourceStatus.EXHAUSTED,
        epoch=epoch,
        created_at=now,
        updated_at=now,
    )
    ledger.add(ops)
    return {"seed_resource_id": seed.id, "ops_resource_id": ops.id}
