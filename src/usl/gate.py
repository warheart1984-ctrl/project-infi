"""USL gate: capability → law → Voss → ledger → substrate."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.usl.canonical_serialize import event_hash
from src.usl.law.default_policy import ALLOW, LawDecision, evaluate_capability
from src.usl.forge.runtime_policy import (
    ForgeRuntimePolicy,
    evaluate_capability as forge_evaluate_capability,
)
from src.usl.substrate_fs import GovernedFS
from src.usl.types import (
    ActorInfo,
    CapabilityInfo,
    CapabilityRequest,
    ContextInfo,
    CryptoInfo,
    LawInfo,
    ResourceInfo,
    StateInfo,
    VossTransition,
)
from src.usl.voss_ledger import Ledger
from src.usl.voss_scar import bind_voss


class USLGate:
    """Modeled on ForgeGate: single entry for governed substrate operations."""

    def __init__(
        self,
        ledger: Ledger | None = None,
        fs: GovernedFS | None = None,
        *,
        sign: bool = True,
        forge_policy: ForgeRuntimePolicy | None = None,
    ) -> None:
        self.ledger = ledger or Ledger(usl_node_id="usl-node-1")
        self.fs = fs or GovernedFS()
        self.sign = sign
        self.forge_policy = forge_policy

    def dispatch(self, request: CapabilityRequest) -> tuple[VossTransition, dict | None]:
        """Full gate pipeline. Returns (transition, substrate_result)."""
        if self.forge_policy is not None:
            law = forge_evaluate_capability(request, self.forge_policy)
        else:
            law = evaluate_capability(request)
        transition = self._build_transition(request, law)

        result: dict | None = None
        if law.decision == ALLOW:
            result = self._dispatch_substrate(request)
            if result and request.capability_id == "fs.write" and "post_state_hash" in result:
                transition.state.post_state_hash = result["post_state_hash"]

        self.ledger.append(transition, sign=self.sign)
        return transition, result

    def _dispatch_substrate(self, request: CapabilityRequest) -> dict | None:
        cap = request.capability_id
        if cap == "fs.write":
            mode = request.resource.extra.get("mode", "create_or_truncate")
            return self.fs.write(
                request.resource.locator,
                request.resource.extra.get("_payload", b""),
                mode=mode,
            )
        if cap == "fs.read":
            return {
                "status": "ok",
                "substrate": "fs",
                "mode": "read",
                "path": request.resource.locator,
            }
        if cap.startswith("net."):
            return {
                "status": "ok",
                "substrate": "mesh_net",
                "capability": cap,
                "locator": request.resource.locator,
            }
        if cap.startswith("ui."):
            return {
                "status": "ok",
                "substrate": "compositor",
                "capability": cap,
                "surface": request.resource.locator,
            }
        return {"status": "noop", "capability": cap}

    def _build_transition(
        self, request: CapabilityRequest, law: LawDecision
    ) -> VossTransition:
        guest = request.guest
        actor = ActorInfo(
            binary_id=guest.ubo.binary_id,
            profile_id=guest.profile_id,
            principal_id=guest.principal_id,
            sigil_id=guest.sigil_id,
        )
        voss = bind_voss(
            pre_state_hash=request.pre_state_hash,
            post_state_hash=request.post_state_hash,
            capability_id=request.capability_id,
            actor=actor,
            decision=law.decision,
            cycle_id=guest.cycle_id,
            lane_id=guest.lane_id,
        )
        ts = request.timestamp or datetime.now(timezone.utc).isoformat()
        tid = request.transition_id or str(uuid4())

        transition = VossTransition(
            version="v1",
            transition_id=tid,
            timestamp=ts,
            actor=actor,
            context=ContextInfo(
                os_family=guest.ubo.os_family,
                process_id=guest.process_id,
                thread_id=guest.thread_id,
                session_id=guest.session_id,
                usl_node_id=guest.usl_node_id,
            ),
            capability=CapabilityInfo(
                capability_id=request.capability_id,
                ceiling_id=request.ceiling_id,
                resource=request.resource,
            ),
            state=StateInfo(
                pre_state_hash=request.pre_state_hash,
                post_state_hash=request.post_state_hash,
                delta_hash=request.delta_hash,
                delta_summary=request.delta_summary,
            ),
            law=LawInfo(
                policy_id=law.policy_id,
                lawbook_id=law.lawbook_id,
                decision=law.decision,
                decision_reason=law.decision_reason,
                decision_detail=law.decision_detail,
            ),
            voss=voss,
            crypto=CryptoInfo(
                event_hash="",
                prev_ledger_root="",
                ledger_root="",
            ),
        )
        return transition
