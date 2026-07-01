from __future__ import annotations

from nova.node.substrate_events import (
    SCHEMA_VERSION,
    IntentRef,
    SubstrateEvent,
    append_substrate_event,
    make_substrate_event,
    read_substrate_events,
    substrate_event_log_path,
)


def make_event(**kwargs):
    if "type" in kwargs:
        kwargs["type_"] = kwargs.pop("type")
    if "stream_id" not in kwargs and "streamId" in kwargs:
        kwargs["stream_id"] = kwargs.pop("streamId")
    return make_substrate_event(**kwargs)


__all__ = [
    "SCHEMA_VERSION",
    "IntentRef",
    "SubstrateEvent",
    "append_substrate_event",
    "make_event",
    "make_substrate_event",
    "read_substrate_events",
    "substrate_event_log_path",
]
