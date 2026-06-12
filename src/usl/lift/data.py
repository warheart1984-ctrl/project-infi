"""Lift static data regions from UBO segments."""

from __future__ import annotations

from src.usl.lift.types import ULDataRegion, ULDataShape, ULProgramMeta


def lift_data_from_meta(meta: ULProgramMeta) -> ULDataShape:
    """Map loadable segments to global data regions (stack/heap deferred)."""
    regions: list[ULDataRegion] = []
    for idx, seg in enumerate(meta.segments):
        if seg.kind in ("code",):
            continue
        kind = "global"
        if seg.kind == "bss":
            kind = "global"
        regions.append(
            ULDataRegion(
                region_id=f"region-{idx}",
                kind=kind,  # type: ignore[arg-type]
                virtual_address=seg.virtual_address,
                size=seg.virtual_size,
                segment_name=seg.name,
            )
        )
    return ULDataShape(regions=regions)
