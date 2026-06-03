"""URG mission-level governance — switchboard over provider organs."""

from src.ugr.mission.ingress import UrgIngressLaw
from src.ugr.mission.receipt_signing import verify_mission_receipt, verify_mission_receipt_v2

__all__ = [
    "UrgIngressLaw",
    "verify_mission_receipt",
    "verify_mission_receipt_v2",
]


def __getattr__(name: str):
    if name == "UGRMissionRuntime":
        from src.ugr.mission.mission_runtime import UGRMissionRuntime

        return UGRMissionRuntime
    if name == "build_mission_runtime":
        from src.ugr.mission.mission_runtime import build_mission_runtime

        return build_mission_runtime
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
