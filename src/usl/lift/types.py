"""ULLiftedModel types — machine-code semantic lift (distinct from AAIS-UL)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

Confidence = Literal["proven", "heuristic", "unknown"]
SegmentKind = Literal["code", "data", "rodata", "bss", "unknown"]
Terminator = Literal["fallthrough", "branch", "call", "return", "syscall", "unknown"]
EdgeKind = Literal["fallthrough", "jump", "call", "return"]
InvariantKind = Literal["safety", "liveness", "protocol", "hazard"]
Severity = Literal["info", "warn", "block"]
EffectBucket = Literal["fs", "net", "timer", "proc", "mem", "device_io", "unknown"]
CapClass = Literal["fs", "net", "proc", "mem", "ui", "ipc", "time", "crypto"]
AuthorityLevel = Literal["none", "read", "write", "execute", "admin"]
ProcessModel = Literal["oneshot", "persistent", "unknown"]
Admission = Literal["single", "multi", "unknown"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class ULProvenance:
    artifact_hash: str
    build_id: str | None = None
    source_path: str | None = None
    lifted_at: str = field(default_factory=_utc_now_iso)


@dataclass
class ULSegment:
    name: str
    virtual_address: int
    virtual_size: int
    kind: SegmentKind
    raw_size: int = 0
    flags: str = ""


@dataclass
class ULProgramMeta:
    program_id: str
    format: str
    os_family: str
    architecture: str
    entry_point: int
    provenance: ULProvenance
    image_base: int = 0
    segments: list[ULSegment] = field(default_factory=list)


@dataclass
class ULBasicBlock:
    block_id: str
    start_vaddr: int
    size: int
    terminator: Terminator = "unknown"


@dataclass
class ULControlEdge:
    from_block: str
    to_block: str
    kind: EdgeKind


@dataclass
class ULFunction:
    function_id: str
    entry_vaddr: int
    blocks: list[str] = field(default_factory=list)


@dataclass
class ULControlShape:
    blocks: list[ULBasicBlock] = field(default_factory=list)
    edges: list[ULControlEdge] = field(default_factory=list)
    functions: list[ULFunction] = field(default_factory=list)


@dataclass
class ULDataRegion:
    region_id: str
    kind: Literal["global", "stack", "heap", "unknown"]
    virtual_address: int
    size: int
    segment_name: str | None = None


@dataclass
class ULDataShape:
    regions: list[ULDataRegion] = field(default_factory=list)


@dataclass
class SyscallEffect:
    effect_id: str
    bucket: EffectBucket
    confidence: Confidence
    syscall_number: int | None = None
    syscall_name: str | None = None
    site_vaddr: int = 0
    block_id: str | None = None


@dataclass
class ImportEffect:
    module: str
    symbol: str
    slot_id: str = ""


@dataclass
class AAISEffectSurface:
    syscalls: list[SyscallEffect] = field(default_factory=list)
    imports: list[ImportEffect] = field(default_factory=list)


@dataclass
class AAISInvariantRule:
    invariant_id: str
    kind: InvariantKind
    severity: Severity
    description: str = ""


@dataclass
class AAISInvariantSet:
    rules: list[AAISInvariantRule] = field(default_factory=list)


@dataclass
class ResourceCapability:
    usl_capability_id: str
    class_: CapClass
    scope: str = "guest"


@dataclass
class AuthorityGrant:
    authority_id: str
    level: AuthorityLevel


@dataclass
class AAISCapabilitySet:
    resources: list[ResourceCapability] = field(default_factory=list)
    authorities: list[AuthorityGrant] = field(default_factory=list)
    ceiling_id: str | None = None


@dataclass
class AAISHealthProfile:
    probe: str = "lift-default"
    interval_seconds: int = 30


@dataclass
class AAISRuntimeProfile:
    process_model: ProcessModel = "oneshot"
    admission: Admission = "single"
    health: AAISHealthProfile = field(default_factory=AAISHealthProfile)


@dataclass
class ULLiftedModel:
    meta: ULProgramMeta
    control: ULControlShape
    data: ULDataShape
    effects: AAISEffectSurface
    invariants: AAISInvariantSet
    capabilities: AAISCapabilitySet
    runtime_shape: AAISRuntimeProfile
    version: str = "v1"

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(asdict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ULLiftedModel:
        meta_raw = data.get("meta") or {}
        p = meta_raw.get("provenance") or {}
        segments = [
            ULSegment(
                name=str(s.get("name") or ""),
                virtual_address=int(s.get("virtual_address") or 0),
                virtual_size=int(s.get("virtual_size") or 0),
                kind=s.get("kind") or "unknown",
                raw_size=int(s.get("raw_size") or 0),
                flags=str(s.get("flags") or ""),
            )
            for s in (meta_raw.get("segments") or [])
        ]
        meta = ULProgramMeta(
            program_id=str(meta_raw.get("program_id") or ""),
            format=str(meta_raw.get("format") or ""),
            os_family=str(meta_raw.get("os_family") or ""),
            architecture=str(meta_raw.get("architecture") or ""),
            entry_point=int(meta_raw.get("entry_point") or 0),
            provenance=ULProvenance(
                artifact_hash=str(p.get("artifact_hash") or ""),
                build_id=p.get("build_id"),
                source_path=p.get("source_path"),
                lifted_at=str(p.get("lifted_at") or _utc_now_iso()),
            ),
            image_base=int(meta_raw.get("image_base") or 0),
            segments=segments,
        )

        control_raw = data.get("control") or {}
        control = ULControlShape(
            blocks=[
                ULBasicBlock(
                    block_id=str(b.get("block_id") or ""),
                    start_vaddr=int(b.get("start_vaddr") or 0),
                    size=int(b.get("size") or 0),
                    terminator=b.get("terminator") or "unknown",
                )
                for b in (control_raw.get("blocks") or [])
            ],
            edges=[
                ULControlEdge(
                    from_block=str(e.get("from_block") or ""),
                    to_block=str(e.get("to_block") or ""),
                    kind=e.get("kind") or "fallthrough",
                )
                for e in (control_raw.get("edges") or [])
            ],
            functions=[
                ULFunction(
                    function_id=str(f.get("function_id") or ""),
                    entry_vaddr=int(f.get("entry_vaddr") or 0),
                    blocks=[str(x) for x in (f.get("blocks") or [])],
                )
                for f in (control_raw.get("functions") or [])
            ],
        )

        data_raw = data.get("data") or {}
        data_shape = ULDataShape(
            regions=[
                ULDataRegion(
                    region_id=str(r.get("region_id") or ""),
                    kind=r.get("kind") or "unknown",
                    virtual_address=int(r.get("virtual_address") or 0),
                    size=int(r.get("size") or 0),
                    segment_name=r.get("segment_name"),
                )
                for r in (data_raw.get("regions") or [])
            ]
        )

        effects_raw = data.get("effects") or {}
        effects = AAISEffectSurface(
            syscalls=[
                SyscallEffect(
                    effect_id=str(s.get("effect_id") or ""),
                    bucket=s.get("bucket") or "unknown",
                    confidence=s.get("confidence") or "unknown",
                    syscall_number=s.get("syscall_number"),
                    syscall_name=s.get("syscall_name"),
                    site_vaddr=int(s.get("site_vaddr") or 0),
                    block_id=s.get("block_id"),
                )
                for s in (effects_raw.get("syscalls") or [])
            ],
            imports=[
                ImportEffect(
                    module=str(i.get("module") or ""),
                    symbol=str(i.get("symbol") or ""),
                    slot_id=str(i.get("slot_id") or ""),
                )
                for i in (effects_raw.get("imports") or [])
            ],
        )

        inv_raw = data.get("invariants") or {}
        invariants = AAISInvariantSet(
            rules=[
                AAISInvariantRule(
                    invariant_id=str(r.get("invariant_id") or ""),
                    kind=r.get("kind") or "safety",
                    severity=r.get("severity") or "info",
                    description=str(r.get("description") or ""),
                )
                for r in (inv_raw.get("rules") or [])
            ]
        )

        caps_raw = data.get("capabilities") or {}
        capabilities = AAISCapabilitySet(
            resources=[
                ResourceCapability(
                    usl_capability_id=str(r.get("usl_capability_id") or ""),
                    class_=r.get("class") or r.get("class_") or "fs",
                    scope=str(r.get("scope") or "guest"),
                )
                for r in (caps_raw.get("resources") or [])
            ],
            authorities=[
                AuthorityGrant(
                    authority_id=str(a.get("authority_id") or ""),
                    level=a.get("level") or "none",
                )
                for a in (caps_raw.get("authorities") or [])
            ],
            ceiling_id=caps_raw.get("ceiling_id"),
        )

        runtime_raw = data.get("runtime_shape") or {}
        health_raw = runtime_raw.get("health") or {}
        runtime_shape = AAISRuntimeProfile(
            process_model=runtime_raw.get("process_model") or "oneshot",
            admission=runtime_raw.get("admission") or "single",
            health=AAISHealthProfile(
                probe=str(health_raw.get("probe") or "lift-default"),
                interval_seconds=int(health_raw.get("interval_seconds") or 30),
            ),
        )

        return cls(
            meta=meta,
            control=control,
            data=data_shape,
            effects=effects,
            invariants=invariants,
            capabilities=capabilities,
            runtime_shape=runtime_shape,
            version=str(data.get("version") or "v1"),
        )


def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            key = "class" if k == "class_" else k
            out[key] = _to_jsonable(v)
        return out
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    return obj
