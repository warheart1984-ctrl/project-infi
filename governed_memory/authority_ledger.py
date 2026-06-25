"""AuthorityLedger — capability tokens bound to intent versions."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict

from governed_memory.types import AuthorityScope, AuthorityToken


class AuthorityLedger:
    def __init__(self) -> None:
        self._tokens: dict[str, AuthorityToken] = {}

    def issue(
        self,
        *,
        issued_by: str,
        issued_to: str,
        capabilities: list[str],
        scope: AuthorityScope,
        delegation_chain: list[str] | None = None,
    ) -> AuthorityToken:
        if scope.intent_version < 1:
            raise ValueError("authority scope must bind intent_version >= 1")
        token_id = str(uuid.uuid4())
        payload = json.dumps(
            {
                "token_id": token_id,
                "issued_by": issued_by,
                "issued_to": issued_to,
                "capabilities": capabilities,
                "scope": asdict(scope),
                "delegation_chain": delegation_chain or [],
            },
            sort_keys=True,
        )
        signature = hashlib.sha256(f"auth:{payload}".encode()).hexdigest()
        token = AuthorityToken(
            token_id=token_id,
            issued_by=issued_by,
            issued_to=issued_to,
            capabilities=list(capabilities),
            scope=scope,
            delegation_chain=list(delegation_chain or []),
            signature=signature,
            revoked=False,
        )
        self._tokens[token_id] = token
        return token

    def get(self, token_id: str) -> AuthorityToken | None:
        return self._tokens.get(token_id)

    def revoke(self, token_id: str) -> bool:
        token = self._tokens.get(token_id)
        if not token or token.revoked:
            return False
        self._tokens[token_id] = AuthorityToken(
            token_id=token.token_id,
            issued_by=token.issued_by,
            issued_to=token.issued_to,
            capabilities=token.capabilities,
            scope=token.scope,
            delegation_chain=token.delegation_chain,
            signature=token.signature,
            revoked=True,
        )
        return True

    def validate(self, token_id: str, capability: str, now: float | None = None) -> tuple[bool, str | None]:
        now = now if now is not None else time.time() * 1000
        token = self.get(token_id)
        if not token:
            return False, "missing_token"
        if token.revoked:
            return False, "revoked"
        if capability not in token.capabilities:
            return False, "capability_denied"
        expiry = token.scope.time_limit_ms
        if expiry > 0 and now > expiry:
            return False, "expired"
        return True, None
