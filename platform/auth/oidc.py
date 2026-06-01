"""OIDC session auth (v2 scaffold)."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from typing import Any
from urllib.parse import urlencode

from platform.common import new_id


def org_oidc_config(org: dict[str, Any]) -> dict[str, Any]:
    return dict(org.get("oidc") or {})


def build_login_redirect(*, org_id: str, org: dict[str, Any], redirect_uri: str, state: str) -> str:
    cfg = org_oidc_config(org)
    issuer = str(cfg.get("issuer") or "").rstrip("/")
    if not issuer:
        return f"/platform/getting-started?org_id={org_id}&oidc=disabled"
    params = {
        "client_id": cfg.get("client_id", ""),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
    }
    return f"{issuer}/authorize?{urlencode(params)}"


def issue_session_token(*, org_id: str, principal_id: str, secret: str, ttl_seconds: int = 3600) -> str:
    payload = {
        "org_id": org_id,
        "principal_id": principal_id,
        "exp": int(time.time()) + ttl_seconds,
        "nonce": secrets.token_hex(8),
    }
    body = json.dumps(payload, sort_keys=True)
    sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_session_token(token: str, *, secret: str) -> dict[str, Any] | None:
    if "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    payload = json.loads(body)
    if int(payload.get("exp") or 0) < int(time.time()):
        return None
    return payload


def mock_callback_principal(*, org_id: str, sub: str) -> str:
    return f"oidc-{org_id}-{sub}"


def create_refresh_session(*, store: Any, org_id: str, principal_id: str) -> dict[str, Any]:
    session_id = new_id("sess")
    record = {"session_id": session_id, "org_id": org_id, "principal_id": principal_id}
    with store._connect() as conn:
        conn.execute(
            "INSERT INTO sessions (session_id, org_id, payload) VALUES (?, ?, ?)",
            (session_id, org_id, store._dump(record)),
        )
        conn.commit()
    return record
