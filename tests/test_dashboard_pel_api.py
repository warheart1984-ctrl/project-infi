"""Tests for PEL Explorer dashboard API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.cori.pel.store import build_pel_record, ensure_db, insert_pel_record
from src.cori.pel.normalize import normalize_text
from src.dashboard.app import app


@pytest.fixture()
def pel_client(tmp_path, monkeypatch):
    db_path = tmp_path / "pel.sqlite3"
    monkeypatch.setenv("PEL_STORE_PATH", str(db_path))
    conn = ensure_db(db_path)

    claim_norm = normalize_text("claim body", {"title": "T1 Claim"})
    claim = build_pel_record(type_="claim", author="jon", norm=claim_norm, pel_id="PEL-claim-test")
    insert_pel_record(conn, claim)

    evidence_norm = normalize_text("evidence body", {"title": "Primary doc"})
    evidence = build_pel_record(
        type_="artifact",
        author="jon",
        norm=evidence_norm,
        pel_id="PEL-evidence-test",
        links=[{"relation": "supports", "target_id": claim["id"]}],
        evidence_strength="primary",
    )
    insert_pel_record(conn, evidence)

    orphan_norm = normalize_text("orphan claim", {"title": "Orphan"})
    orphan = build_pel_record(type_="claim", author="jon", norm=orphan_norm, pel_id="PEL-orphan-claim")
    insert_pel_record(conn, orphan)

    conn.commit()
    conn.close()

    with TestClient(app) as client:
        yield client


def test_list_pel_records(pel_client: TestClient) -> None:
    response = pel_client.get("/pel/records?type=claim")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert all(row["type"] == "claim" for row in body)


def test_get_pel_record(pel_client: TestClient) -> None:
    response = pel_client.get("/pel/record/PEL-claim-test")
    assert response.status_code == 200
    assert response.json()["title"] == "T1 Claim"


def test_claim_evidence_trace(pel_client: TestClient) -> None:
    response = pel_client.get("/pel/claim/PEL-claim-test/evidence")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "PEL-evidence-test"


def test_evidence_to_claims_trace(pel_client: TestClient) -> None:
    response = pel_client.get("/pel/evidence/PEL-evidence-test/claims")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "PEL-claim-test"


def test_gaps_lists_orphan_claim(pel_client: TestClient) -> None:
    response = pel_client.get("/pel/gaps/claims")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["claim_id"] == "PEL-orphan-claim"
    assert body[0]["missing_primary_evidence"] is True
