"""SQLite persistence for vault entries and sovereign seal records."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from src.cori.store_paths import vault_store_path
from src.cori.vault.models import (
    BoneKingProofPackage,
    CeremonyCompletionRecord,
    LineageProofRegistration,
    MissionCompletionRecord,
    MissionDossierRecord,
    ObserverReportRecord,
    SealApplicationRecord,
    TrustBoundaryUpdate,
    VaultEntry,
)

_MIGRATION = Path(__file__).resolve().parents[3] / "migrations" / "vault.sql"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_vault_db(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or vault_store_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_MIGRATION.read_text(encoding="utf-8"))
    conn.commit()
    return conn


class VaultStorage:
    def __init__(self, db_path: Path | None = None) -> None:
        self._path = db_path or vault_store_path()

    def _conn(self) -> sqlite3.Connection:
        return ensure_vault_db(self._path)

    def save_package(self, package: BoneKingProofPackage) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO vault_packages (id, chain_id, document, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    package.id,
                    package.chain_id,
                    json.dumps(package.model_dump(mode="json"), sort_keys=True),
                    _now_iso(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def save_vault_entry(self, entry: VaultEntry) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO vault_entries (id, chain_id, document, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    entry.id,
                    entry.chain_id,
                    json.dumps(entry.model_dump(mode="json"), sort_keys=True),
                    _now_iso(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def save_seal_record(self, record: SealApplicationRecord) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO vault_seal_records (id, chain_id, document, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.chain_id,
                    json.dumps(record.model_dump(mode="json"), sort_keys=True),
                    _now_iso(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def save_lineage_registration(self, registration: LineageProofRegistration) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO vault_lineage_proofs (id, chain_id, document, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    registration.id,
                    registration.chain_id,
                    json.dumps(registration.model_dump(mode="json"), sort_keys=True),
                    _now_iso(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def persist_ceremony(
        self,
        package: BoneKingProofPackage,
        entry: VaultEntry,
        seal: SealApplicationRecord,
        lineage: LineageProofRegistration,
    ) -> None:
        self.save_package(package)
        self.save_vault_entry(entry)
        self.save_seal_record(seal)
        self.save_lineage_registration(lineage)

    def get_vault_entry(self, entry_id: str) -> VaultEntry:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT document FROM vault_entries WHERE id = ?", (entry_id,)
            ).fetchone()
            if not row:
                raise KeyError(f"Vault entry not found: {entry_id}")
            return VaultEntry.model_validate(json.loads(row["document"]))
        finally:
            conn.close()

    def _save_document(
        self,
        table: str,
        row_id: str,
        *,
        document: dict,
        mission_id: str | None = None,
        chain_id: str | None = None,
    ) -> None:
        conn = self._conn()
        try:
            if table == "vault_mission_dossiers":
                conn.execute(
                    f"""
                    INSERT OR REPLACE INTO {table} (mission_id, document, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (row_id, json.dumps(document, sort_keys=True), _now_iso()),
                )
            elif mission_id is not None:
                conn.execute(
                    f"""
                    INSERT OR REPLACE INTO {table} (id, mission_id, document, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (row_id, mission_id, json.dumps(document, sort_keys=True), _now_iso()),
                )
            elif chain_id is not None:
                conn.execute(
                    f"""
                    INSERT OR REPLACE INTO {table} (id, chain_id, document, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (row_id, chain_id, json.dumps(document, sort_keys=True), _now_iso()),
                )
            else:
                raise ValueError(f"unsupported save for {table}")
            conn.commit()
        finally:
            conn.close()

    def save_observer_report(self, report: ObserverReportRecord) -> None:
        self._save_document(
            "vault_observer_reports",
            report.id,
            document=report.model_dump(mode="json"),
            mission_id=report.mission_id,
        )

    def save_mission_completion(self, record: MissionCompletionRecord) -> None:
        self._save_document(
            "vault_mission_completions",
            record.id,
            document=record.model_dump(mode="json"),
            mission_id=record.mission_id,
        )

    def save_ceremony_completion(self, record: CeremonyCompletionRecord) -> None:
        self._save_document(
            "vault_ceremony_completions",
            record.ceremony_id,
            document=record.model_dump(mode="json"),
            mission_id=record.mission_id,
        )

    def save_trust_boundary_update(self, record: TrustBoundaryUpdate) -> None:
        self._save_document(
            "vault_trust_boundary_updates",
            record.chain_id,
            document=record.model_dump(mode="json"),
            chain_id=record.chain_id,
        )

    def save_mission_dossier(self, dossier: MissionDossierRecord) -> None:
        self._save_document(
            "vault_mission_dossiers",
            dossier.mission_id,
            document=dossier.model_dump(mode="json"),
        )

    def persist_category_b_closure(
        self,
        package: BoneKingProofPackage,
        entry: VaultEntry,
        seal: SealApplicationRecord,
        lineage: LineageProofRegistration,
        observer_report: ObserverReportRecord,
        mission_completion: MissionCompletionRecord,
        ceremony_completion: CeremonyCompletionRecord,
        trust_update: TrustBoundaryUpdate,
        dossier: MissionDossierRecord,
    ) -> None:
        self.persist_ceremony(package, entry, seal, lineage)
        self.save_observer_report(observer_report)
        self.save_mission_completion(mission_completion)
        self.save_ceremony_completion(ceremony_completion)
        self.save_trust_boundary_update(trust_update)
        self.save_mission_dossier(dossier)
