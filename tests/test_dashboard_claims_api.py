"""Tests for claim registry dashboard API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.cori.claims.store import ensure_db, insert_claim, insert_claim_evidence_link
from src.cori.pel.store import build_pel_record, ensure_db as ensure_pel_db, insert_pel_record
from src.cori.pel.normalize import normalize_text
from src.dashboard.app import app


@pytest.fixture()
def claims_client(tmp_path, monkeypatch):
    registry_path = tmp_path / "claim_registry.sqlite3"
    pel_path = tmp_path / "pel.sqlite3"
    monkeypatch.setenv("CLAIM_REGISTRY_PATH", str(registry_path))
    monkeypatch.setenv("PEL_STORE_PATH", str(pel_path))

    conn = ensure_db(registry_path)
    pel_conn = ensure_pel_db(pel_path)

    norm = normalize_text("evidence", {"title": "Doc"})
    pel = build_pel_record(type_="artifact", author="jon", norm=norm, pel_id="PEL-test-1")
    insert_pel_record(pel_conn, pel)
    pel_conn.commit()
    pel_conn.close()

    supported = insert_claim(
        conn,
        claim_id="CLAIM-supported",
        kind="stewardship",
        summary="Supported claim",
        created_by="jon",
        status="active",
    )
    insert_claim_evidence_link(
        conn,
        claim_id=supported["id"],
        pel_id=pel["id"],
        relation="supports",
        strength="primary",
        created_by="jon",
    )
    insert_claim(
        conn,
        claim_id="CLAIM-gap",
        kind="ownership",
        summary="Gap claim",
        created_by="jon",
        status="active",
    )
    conn.commit()
    conn.close()

    with TestClient(app) as client:
        yield client


def test_list_claims(claims_client: TestClient) -> None:
    response = claims_client.get("/claims?status=active")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_claim(claims_client: TestClient) -> None:
    response = claims_client.get("/claims/CLAIM-supported")
    assert response.status_code == 200
    assert response.json()["summary"] == "Supported claim"


def test_claim_evidence_links(claims_client: TestClient) -> None:
    response = claims_client.get("/claims/CLAIM-supported/evidence")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["pel_id"] == "PEL-test-1"


def test_gaps_endpoint(claims_client: TestClient) -> None:
    response = claims_client.get("/claims/gaps/claims")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["claim_id"] == "CLAIM-gap"
    assert body[0]["missing_primary_evidence"] is True
