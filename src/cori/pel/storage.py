"""Persistence for Alpha PELRecord, Claim, and VerificationRecord artifacts."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from src.cori.pel.models import Claim, PELRecord, VerificationRecord
from src.cori.store_paths import alpha_evidence_path

_MIGRATION = Path(__file__).resolve().parents[3] / "migrations" / "alpha_evidence.sql"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_schema() -> str:
    return _MIGRATION.read_text(encoding="utf-8")


def ensure_alpha_db(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or alpha_evidence_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_load_schema())
    conn.commit()
    return conn


class RuntimeClient(Protocol):
    def get(self, path: str, **kwargs: Any) -> Any: ...


class PelStorage:
  def __init__(self, db_path: Path | None = None) -> None:
    self._path = db_path or alpha_evidence_path()

  def _conn(self) -> sqlite3.Connection:
    return ensure_alpha_db(self._path)

  def save_pel_record(self, pel: PELRecord) -> None:
    conn = self._conn()
    try:
      conn.execute(
        """
        INSERT OR REPLACE INTO alpha_pel_records (id, audit_id, document, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
          pel.id,
          pel.audit_id,
          json.dumps(pel.model_dump(mode="json"), sort_keys=True),
          _now_iso(),
        ),
      )
      conn.commit()
    finally:
      conn.close()

  def get_by_id(self, pel_id: str) -> PELRecord:
    conn = self._conn()
    try:
      row = conn.execute("SELECT document FROM alpha_pel_records WHERE id = ?", (pel_id,)).fetchone()
      if not row:
        raise KeyError(f"PEL record not found: {pel_id}")
      return PELRecord.model_validate(json.loads(row["document"]))
    finally:
      conn.close()

  def list_all(self) -> list[PELRecord]:
    conn = self._conn()
    try:
      rows = conn.execute("SELECT document FROM alpha_pel_records ORDER BY created_at DESC").fetchall()
      return [PELRecord.model_validate(json.loads(row["document"])) for row in rows]
    finally:
      conn.close()


class ClaimStorage:
  def __init__(self, db_path: Path | None = None) -> None:
    self._path = db_path or alpha_evidence_path()

  def _conn(self) -> sqlite3.Connection:
    return ensure_alpha_db(self._path)

  def save_claim(self, claim: Claim) -> None:
    conn = self._conn()
    try:
      conn.execute(
        """
        INSERT OR REPLACE INTO alpha_claims (id, document, created_at)
        VALUES (?, ?, ?)
        """,
        (claim.id, json.dumps(claim.model_dump(mode="json"), sort_keys=True), _now_iso()),
      )
      conn.commit()
    finally:
      conn.close()

  def get_by_id(self, claim_id: str) -> Claim:
    conn = self._conn()
    try:
      row = conn.execute("SELECT document FROM alpha_claims WHERE id = ?", (claim_id,)).fetchone()
      if not row:
        raise KeyError(f"Claim not found: {claim_id}")
      return Claim.model_validate(json.loads(row["document"]))
    finally:
      conn.close()

  def list_all(self) -> list[Claim]:
    conn = self._conn()
    try:
      rows = conn.execute("SELECT document FROM alpha_claims ORDER BY created_at DESC").fetchall()
      return [Claim.model_validate(json.loads(row["document"])) for row in rows]
    finally:
      conn.close()


class VerificationStorage:
  def __init__(self, db_path: Path | None = None) -> None:
    self._path = db_path or alpha_evidence_path()

  def _conn(self) -> sqlite3.Connection:
    return ensure_alpha_db(self._path)

  def save_verification(self, verification: VerificationRecord) -> None:
    conn = self._conn()
    try:
      conn.execute(
        """
        INSERT OR REPLACE INTO alpha_verifications (
          id, claim_id, pel_record_id, document, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
          verification.id,
          verification.claim_id,
          verification.pel_record_id,
          json.dumps(verification.model_dump(mode="json"), sort_keys=True),
          _now_iso(),
        ),
      )
      conn.commit()
    finally:
      conn.close()

  def get_by_id(self, verif_id: str) -> VerificationRecord:
    conn = self._conn()
    try:
      row = conn.execute("SELECT document FROM alpha_verifications WHERE id = ?", (verif_id,)).fetchone()
      if not row:
        raise KeyError(f"Verification not found: {verif_id}")
      return VerificationRecord.model_validate(json.loads(row["document"]))
    finally:
      conn.close()

  def list_all(self) -> list[VerificationRecord]:
    conn = self._conn()
    try:
      rows = conn.execute("SELECT document FROM alpha_verifications ORDER BY created_at DESC").fetchall()
      return [VerificationRecord.model_validate(json.loads(row["document"])) for row in rows]
    finally:
      conn.close()
