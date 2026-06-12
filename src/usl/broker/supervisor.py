"""Guest broker supervisor — validates policy, routes syscalls to USLGate."""

from __future__ import annotations

import base64
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from src.usl.adapters.windows_fs import build_fs_write_request
from src.usl.broker.ipc import BrokerMessage, BrokerResponse
from src.usl.law.default_policy import ALLOW
from src.usl.types import CapabilityRequest, DeltaSummary, GuestContext, ResourceInfo

from src.usl.forge.runtime_policy import (
    ForgeRuntimePolicy,
    _bundle_for_capability,
    resolve_syscall_capability,
)

if TYPE_CHECKING:
    from src.usl.gate import USLGate


@dataclass
class GuestBrokerConfig:
    policy_path: Path | None = None
    require_signed_policy: bool = False
    sigil_id: str = "sigil:lambda-root"


class GuestBroker:
    """Supervised guest syscall broker (Phase 2+)."""

    def __init__(
        self,
        gate: USLGate,
        guest: GuestContext,
        *,
        config: GuestBrokerConfig | None = None,
        forge_policy: ForgeRuntimePolicy | None = None,
    ) -> None:
        self.gate = gate
        self.guest = guest
        self.config = config or GuestBrokerConfig()
        self.forge_policy = forge_policy
        self._policy_verified = False

    def verify_policy_at_load(self) -> tuple[bool, str]:
        """Verify signed lawbook before guest execution (Phase 3)."""
        if not self.config.require_signed_policy:
            self._policy_verified = True
            return True, "policy_optional"

        path = self.config.policy_path
        if path is None or not path.is_file():
            return False, "policy_missing"

        from src.usl.policy_signing import verify_signed_policy

        ok, detail = verify_signed_policy(path, expected_sigil=self.config.sigil_id)
        self._policy_verified = ok
        return ok, detail

    def handle(self, message: BrokerMessage) -> BrokerResponse:
        if self.config.require_signed_policy and not self._policy_verified:
            return BrokerResponse(
                ok=False,
                decision="deny",
                error="unsigned_policy",
            )

        try:
            request = self._message_to_request(message)
            transition, substrate = self.gate.dispatch(request)
            return BrokerResponse(
                ok=transition.law.decision == ALLOW,
                decision=transition.law.decision,
                transition_id=transition.transition_id,
                substrate=substrate,
            )
        except Exception as exc:
            return BrokerResponse(ok=False, decision="error", error=str(exc)[:500])

    def handle_json(self, raw: str | bytes) -> str:
        msg = BrokerMessage.from_json(raw)
        return self.handle(msg).to_json()

    def _message_to_request(self, message: BrokerMessage) -> CapabilityRequest:
        guest = replace(
            self.guest,
            process_id=message.guest_process_id or self.guest.process_id,
            profile_id=message.profile_id or self.guest.profile_id,
        )

        if message.capability_id == "fs.write":
            data = b""
            if message.payload_b64:
                data = base64.b64decode(message.payload_b64)
            req = build_fs_write_request(guest, message.path, data)
            req.guest = guest
            return req

        capability_id = message.capability_id
        ceiling_id = message.ceiling_id

        if self.forge_policy is not None:
            syscall_raw = message.extra.get("syscall_number")
            if syscall_raw is not None:
                try:
                    syscall_num = int(syscall_raw)
                except (TypeError, ValueError):
                    syscall_num = -1
                resolved = resolve_syscall_capability(self.forge_policy, syscall_num)
                if resolved:
                    capability_id = resolved
                    bundle = _bundle_for_capability(resolved)
                    if bundle:
                        ceiling_id = bundle

        resource = ResourceInfo(
            kind=message.extra.get("kind", "generic"),
            locator=message.path or message.extra.get("locator", ""),
            extra=dict(message.extra),
        )
        return CapabilityRequest(
            capability_id=capability_id,
            ceiling_id=ceiling_id,
            resource=resource,
            guest=guest,
            pre_state_hash=message.extra.get("pre_state_hash", "genesis"),
            post_state_hash=message.extra.get("post_state_hash", "post"),
            delta_hash=message.extra.get("delta_hash", "delta"),
            delta_summary=DeltaSummary(),
        )
