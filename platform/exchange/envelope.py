"""IMXP signed envelopes."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from typing import Any

from platform.common import new_id

ENVELOPE_VERSION = "platform.membrane_envelope.v1"


def exchange_secret() -> str:
    return os.environ.get("PLATFORM_EXCHANGE_SECRET", "platform-exchange-dev-secret")


def sign_envelope(envelope: dict[str, Any]) -> str:
    body = json.dumps({k: v for k, v in envelope.items() if k != "signature"}, sort_keys=True)
    return hmac.new(exchange_secret().encode(), body.encode(), hashlib.sha256).hexdigest()


def verify_envelope(envelope: dict[str, Any]) -> bool:
    sig = str(envelope.get("signature") or "")
    expected = sign_envelope(envelope)
    return hmac.compare_digest(sig, expected)


def build_envelope(
    *,
    tenant_id: str,
    source_org_id: str,
    target_org_id: str,
    kind: str,
    body: dict[str, Any],
    consent_by: str,
    dual_consent: bool = False,
) -> dict[str, Any]:
    env = {
        "envelope_version": ENVELOPE_VERSION,
        "tenant_id": tenant_id,
        "source_org_id": source_org_id,
        "target_org_id": target_org_id,
        "kind": kind,
        "body": body,
        "consent_id": new_id("consent"),
        "consent_by": consent_by,
        "dual_consent": dual_consent,
    }
    env["signature"] = sign_envelope(env)
    return env
