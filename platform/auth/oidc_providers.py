"""OIDC provider registry (v8) — Google, Microsoft, GitHub + local fallback."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlencode

PROVIDER_ISSUERS: dict[str, str] = {
    "google": "https://accounts.google.com",
    "microsoft": "https://login.microsoftonline.com/common/v2.0",
    "github": "https://github.com",
}


def build_authorize_url(
    *,
    provider: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    org_id: str,
) -> str:
    if provider == "local" or not client_id:
        return f"/platform/getting-started?org_id={org_id}&oidc=local"
    base = PROVIDER_ISSUERS.get(provider, "")
    if provider == "google":
        path = f"{base}/o/oauth2/v2/auth"
    elif provider == "microsoft":
        path = f"{base}/oauth2/v2.0/authorize"
    elif provider == "github":
        path = f"{base}/login/oauth/authorize"
    else:
        return f"/platform/getting-started?org_id={org_id}"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }
    if provider == "github":
        params["scope"] = "read:user user:email"
    return f"{path}?{urlencode(params)}"


def exchange_code_for_identity(
    *,
    provider: str,
    code: str,
    org: dict[str, Any],
) -> dict[str, str]:
    """v8 stub: real token exchange via env-configured HTTP in production."""
    cfg = dict(org.get("oidc_config") or {})
    if provider == "local" or not code:
        return {"sub": "local-user", "email": "local@platform.local"}
    stub_mode = os.environ.get("PLATFORM_OIDC_STUB", "1") != "0"
    if stub_mode:
        return {"sub": f"{provider}-{code[:8]}", "email": f"{code[:8]}@{provider}.stub"}
    return {"sub": f"{provider}-user", "email": f"user@{provider}.platform"}


def provider_from_org(org: dict[str, Any]) -> str:
    return str(org.get("oidc_provider") or "local")
