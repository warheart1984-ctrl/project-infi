"""Release 29 partial→live integration helpers and universal posture checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

INTEGRATION_UNIVERSAL_PROOF = (
    "docs/proof/platform/INTEGRATION_UNIVERSAL_BUNDLE_V1_PROOF.md"
)

STORY_FORGE_EXECUTION_PROOFS = (
    "docs/proof/storyforge/STORY_FORGE_LAUNCHER_ORGAN_EXECUTION_V1_PROOF.md",
    "docs/proof/storyforge/MOVIE_RENDERER_LANE_ORGAN_EXECUTION_V1_PROOF.md",
    "docs/proof/storyforge/TEXT_GAME_TO_VIDEO_ORGAN_EXECUTION_V1_PROOF.md",
    "docs/proof/storyforge/GAME_FRONT_DOOR_ORGAN_EXECUTION_V1_PROOF.md",
    "docs/proof/storyforge/TEXT_TO_3D_WORLD_LANE_ORGAN_EXECUTION_V1_PROOF.md",
    "docs/proof/storyforge/WORLD_PACK_LANE_ORGAN_EXECUTION_V1_PROOF.md",
)


def _normalize_bridge_key(capability_id: str, action: str) -> tuple[str, str]:
    cap = str(capability_id or "").replace("-", "_").strip().lower()
    act = str(action or "").strip().lower()
    return cap, act


def is_bridge_action_registered(
    capability_id: str,
    action: str,
    *,
    selection_routes: dict[tuple[str, str], Any] | None = None,
) -> bool:
    key = _normalize_bridge_key(capability_id, action)
    if selection_routes is not None:
        return key in selection_routes
    return key in _expected_bridge_actions_from_source()


def _expected_bridge_actions_from_source() -> set[tuple[str, str]]:
    root = Path(__file__).resolve().parents[1]
    text = (root / "src/capability_service_bridge.py").read_text(encoding="utf-8")
    pairs: set[tuple[str, str]] = set()
    cap_id: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('"capability_id":'):
            cap_id = stripped.split(":", 1)[1].strip().strip('",')
        elif stripped.startswith('"action":') and cap_id:
            act = stripped.split(":", 1)[1].strip().strip('",')
            pairs.add(_normalize_bridge_key(cap_id, act))
    return pairs


def assert_bridge_action_registered(
    capability_id: str,
    action: str,
    *,
    selection_routes: dict[tuple[str, str], Any] | None = None,
) -> None:
    if not is_bridge_action_registered(
        capability_id, action, selection_routes=selection_routes
    ):
        raise ValueError(
            f"Unregistered capability bridge action: {capability_id}/{action}"
        )


def memory_governance_universal_ready(*, root: Path | None = None) -> bool:
    root = root or Path(__file__).resolve().parents[1]
    api_path = root / "src/api.py"
    enforcer_path = root / "src/memory_board_enforcer.py"
    board_path = root / "src/jarvis_memory_board.py"
    if not all(p.is_file() for p in (api_path, enforcer_path, board_path)):
        return False
    api_text = api_path.read_text(encoding="utf-8")
    return (
        "memory_enforcer.add_memory" in api_text
        and "MemoryBoardEnforcer" in api_text
        and "get_memory_board_snapshot" in api_text
    )


def capability_bridge_universal_ready(*, root: Path | None = None) -> bool:
    root = root or Path(__file__).resolve().parents[1]
    bridge_path = root / "src/capability_service_bridge.py"
    if not bridge_path.is_file():
        return False
    text = bridge_path.read_text(encoding="utf-8")
    return (
        "unregistered bridge action" in text
        and "story_forge_launcher" in text
    )


def pipeline_transport_ready(*, root: Path | None = None) -> bool:
    root = root or Path(__file__).resolve().parents[1]
    api_path = root / "src/api.py"
    pipeline_path = root / "src/governed_direct_pipeline.py"
    if not api_path.is_file() or not pipeline_path.is_file():
        return False
    api_text = api_path.read_text(encoding="utf-8")
    pipeline_text = pipeline_path.read_text(encoding="utf-8")
    return (
        "consult_pipeline_transport_substrate" in api_text
        and "apply_transport_lane_from_packets" in pipeline_text
        and "pipeline_as_transport_enabled" in pipeline_text
    )


def perception_router_ready(*, root: Path | None = None) -> bool:
    root = root or Path(__file__).resolve().parents[1]
    gateway_path = root / "src/perception_gateway_organ.py"
    if not gateway_path.is_file():
        return False
    return "route_perception_entry" in gateway_path.read_text(encoding="utf-8")


def build_integration_universal_posture(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    proof_present = (root / INTEGRATION_UNIVERSAL_PROOF).is_file()
    return {
        "integration_universal_proof_present": proof_present,
        "memory_governance_universal_ready": memory_governance_universal_ready(root=root),
        "capability_bridge_universal_ready": capability_bridge_universal_ready(root=root),
        "pipeline_transport_ready": pipeline_transport_ready(root=root),
        "perception_router_ready": perception_router_ready(root=root),
        "claim_label": "asserted",
        "read_only": True,
    }


def integration_universal_aligned(*, root: Path | None = None) -> bool:
    posture = build_integration_universal_posture(root=root)
    return all(
        posture.get(key)
        for key in (
            "integration_universal_proof_present",
            "memory_governance_universal_ready",
            "capability_bridge_universal_ready",
            "pipeline_transport_ready",
            "perception_router_ready",
        )
    )
