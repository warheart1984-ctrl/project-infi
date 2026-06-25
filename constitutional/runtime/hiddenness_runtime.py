"""Backward-compatible re-exports — canonical implementation lives in constitutional.hiddenness."""

from constitutional.hiddenness.hiddenness_runtime import (
    HIDDENNESS_RUNTIME_NAME,
    HIDDENNESS_STATE_ID,
    HiddennessCategory,
    HiddennessItem,
    HiddennessRuntime,
    HiddennessState,
    load_hiddenness_state,
)

__all__ = [
    "HIDDENNESS_RUNTIME_NAME",
    "HIDDENNESS_STATE_ID",
    "HiddennessCategory",
    "HiddennessItem",
    "HiddennessRuntime",
    "HiddennessState",
    "load_hiddenness_state",
]
