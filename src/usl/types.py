"""USL core datatypes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ActorInfo:
    binary_id: str
    profile_id: str
    principal_id: str
    sigil_id: str

    def blob(self) -> bytes:
        parts = (self.binary_id, self.profile_id, self.principal_id, self.sigil_id)
        return "|".join(parts).encode("utf-8")


@dataclass
class ContextInfo:
    os_family: str
    process_id: str
    thread_id: str
    session_id: str
    usl_node_id: str


@dataclass
class ResourceInfo:
    kind: str
    locator: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityInfo:
    capability_id: str
    ceiling_id: str
    resource: ResourceInfo


@dataclass
class DeltaSummary:
    bytes_written: int = 0
    bytes_read: int = 0
    objects_created: int = 0
    objects_deleted: int = 0
    capabilities_granted: int = 0
    capabilities_revoked: int = 0


@dataclass
class StateInfo:
    pre_state_hash: str
    post_state_hash: str
    delta_hash: str
    delta_summary: DeltaSummary


@dataclass
class LawInfo:
    policy_id: str
    lawbook_id: str
    decision: str
    decision_reason: str
    decision_detail: str = ""


@dataclass
class VossInfo:
    lambda_coupling_id: str
    debt_id: str
    scar_id: str
    cycle_id: int | str
    lane_id: str


@dataclass
class SignatureInfo:
    signer_id: str
    algo: str
    sig: str


@dataclass
class CryptoInfo:
    event_hash: str
    prev_ledger_root: str
    ledger_root: str
    signature: SignatureInfo | None = None


@dataclass
class VossTransition:
    version: str
    transition_id: str
    timestamp: str
    actor: ActorInfo
    context: ContextInfo
    capability: CapabilityInfo
    state: StateInfo
    law: LawInfo
    voss: VossInfo
    crypto: CryptoInfo

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "version": self.version,
            "transition_id": self.transition_id,
            "timestamp": self.timestamp,
            "actor": {
                "binary_id": self.actor.binary_id,
                "profile_id": self.actor.profile_id,
                "principal_id": self.actor.principal_id,
                "sigil_id": self.actor.sigil_id,
            },
            "context": {
                "os_family": self.context.os_family,
                "process_id": self.context.process_id,
                "thread_id": self.context.thread_id,
                "session_id": self.context.session_id,
                "usl_node_id": self.context.usl_node_id,
            },
            "capability": {
                "capability_id": self.capability.capability_id,
                "ceiling_id": self.capability.ceiling_id,
                "resource": {
                    "kind": self.capability.resource.kind,
                    "locator": self.capability.resource.locator,
                    "extra": dict(self.capability.resource.extra),
                },
            },
            "state": {
                "pre_state_hash": self.state.pre_state_hash,
                "post_state_hash": self.state.post_state_hash,
                "delta_hash": self.state.delta_hash,
                "delta_summary": {
                    "bytes_written": self.state.delta_summary.bytes_written,
                    "bytes_read": self.state.delta_summary.bytes_read,
                    "objects_created": self.state.delta_summary.objects_created,
                    "objects_deleted": self.state.delta_summary.objects_deleted,
                    "capabilities_granted": self.state.delta_summary.capabilities_granted,
                    "capabilities_revoked": self.state.delta_summary.capabilities_revoked,
                },
            },
            "law": {
                "policy_id": self.law.policy_id,
                "lawbook_id": self.law.lawbook_id,
                "decision": self.law.decision,
                "decision_reason": self.law.decision_reason,
                "decision_detail": self.law.decision_detail,
            },
            "voss": {
                "lambda_coupling_id": self.voss.lambda_coupling_id,
                "debt_id": self.voss.debt_id,
                "scar_id": self.voss.scar_id,
                "cycle_id": self.voss.cycle_id,
                "lane_id": self.voss.lane_id,
            },
            "crypto": {
                "event_hash": self.crypto.event_hash,
                "prev_ledger_root": self.crypto.prev_ledger_root,
                "ledger_root": self.crypto.ledger_root,
            },
        }
        if self.crypto.signature:
            d["crypto"]["signature"] = {
                "signer_id": self.crypto.signature.signer_id,
                "algo": self.crypto.signature.algo,
                "sig": self.crypto.signature.sig,
            }
        return d


@dataclass
class SegmentInfo:
    name: str
    virtual_address: int
    virtual_size: int
    raw_size: int
    flags: str = ""
    data: bytes = field(default_factory=bytes, repr=False)


@dataclass
class ImportSlot:
    module: str
    symbol: str
    slot_id: str
    ordinal: int | None = None


@dataclass
class UBO:
    version: str
    binary_id: str
    os_family: str
    format: str
    entry_point: int
    segments: list[SegmentInfo]
    imports: list[ImportSlot]
    architecture: str = "x86_64"
    image_base: int = 0
    signature_status: str = "unverified"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "binary_id": self.binary_id,
            "os_family": self.os_family,
            "format": self.format,
            "architecture": self.architecture,
            "entry_point": self.entry_point,
            "image_base": self.image_base,
            "signature_status": self.signature_status,
            "segments": [
                {
                    "name": s.name,
                    "virtual_address": s.virtual_address,
                    "virtual_size": s.virtual_size,
                    "raw_size": s.raw_size,
                    "flags": s.flags,
                }
                for s in self.segments
            ],
            "imports": [
                {
                    "module": i.module,
                    "symbol": i.symbol,
                    "slot_id": i.slot_id,
                    "ordinal": i.ordinal,
                }
                for i in self.imports
            ],
            "metadata": dict(self.metadata),
        }


@dataclass
class GuestAddressSpace:
    """Page-range guest memory model (Phase 1 interpreted dispatch)."""

    pages: dict[int, bytes] = field(default_factory=dict)

    def map_segment(self, segment: SegmentInfo) -> None:
        if not segment.data:
            return
        base = segment.virtual_address
        for offset in range(0, len(segment.data), 4096):
            page_addr = base + offset
            chunk = segment.data[offset : offset + 4096]
            self.pages[page_addr] = chunk


@dataclass
class GuestContext:
    ubo: UBO
    address_space: GuestAddressSpace
    process_id: str
    thread_id: str = "1"
    session_id: str = "default"
    usl_node_id: str = "usl-node-1"
    profile_id: str = "daily-driver"
    principal_id: str = "user:jon"
    sigil_id: str = "sigil:lambda-root"
    cycle_id: int = 1
    lane_id: str = "lane:substrate"


@dataclass
class CapabilityRequest:
    capability_id: str
    ceiling_id: str
    resource: ResourceInfo
    guest: GuestContext
    pre_state_hash: str
    post_state_hash: str
    delta_hash: str
    delta_summary: DeltaSummary
    transition_id: str | None = None
    timestamp: str | None = None
