"""Lift UBO metadata into ULProgramMeta."""

from __future__ import annotations

from src.usl.lift.types import ULProgramMeta, ULProvenance, ULSegment
from src.usl.types import SegmentInfo, UBO


def _segment_kind(seg: SegmentInfo) -> str:
    name = (seg.name or "").lower()
    flags = (seg.flags or "").lower()
    if ".text" in name or "exec" in flags or "x" in flags:
        return "code"
    if ".rodata" in name or "read" in flags and "write" not in flags:
        return "rodata"
    if ".bss" in name:
        return "bss"
    if ".data" in name or "data" in name:
        return "data"
    return "unknown"


def lift_meta_from_ubo(
    ubo: UBO,
    *,
    artifact_hash: str | None = None,
    source_path: str | None = None,
    build_id: str | None = None,
) -> ULProgramMeta:
    """Map normalized UBO into ULProgramMeta with provenance."""
    hash_value = artifact_hash or ubo.binary_id
    if build_id is None and ubo.metadata:
        build_id = ubo.metadata.get("build_id")

    segments = [
        ULSegment(
            name=s.name,
            virtual_address=s.virtual_address,
            virtual_size=s.virtual_size,
            raw_size=s.raw_size,
            flags=s.flags,
            kind=_segment_kind(s),  # type: ignore[arg-type]
        )
        for s in ubo.segments
    ]

    return ULProgramMeta(
        program_id=ubo.binary_id,
        format=ubo.format,
        os_family=ubo.os_family,
        architecture=ubo.architecture,
        entry_point=ubo.entry_point,
        image_base=ubo.image_base,
        segments=segments,
        provenance=ULProvenance(
            artifact_hash=hash_value,
            build_id=build_id,
            source_path=source_path,
        ),
    )
