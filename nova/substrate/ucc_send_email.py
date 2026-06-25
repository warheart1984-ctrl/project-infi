from __future__ import annotations

from typing import Any

from nova.law_kernel.models import Intent
from nova.substrate.ucc_capabilities import UCCCapabilityContract, UCCConstraints, UCCSubstrateRegistry

_SENT_EMAILS: list[dict[str, Any]] = []


def send_email_handler(intent: Intent) -> dict[str, Any]:
    args = intent.payload.get("tool_args", {})
    record = {"status": "sent", "to": args.get("to"), "body": args.get("body")}
    _SENT_EMAILS.append(record)
    return record


def get_sent_emails() -> list[dict[str, Any]]:
    return list(_SENT_EMAILS)


def clear_sent_emails() -> None:
    _SENT_EMAILS.clear()


send_email_contract = UCCCapabilityContract(
    name="send_email",
    handler=send_email_handler,
    invariants={
        "has_body": lambda intent: bool(intent.payload.get("tool_args", {}).get("body")),
        "has_to": lambda intent: bool(intent.payload.get("tool_args", {}).get("to")),
    },
    ucc=UCCConstraints(
        max_tokens=800,
        requires_pacing_consent=True,
        overload_safe=True,
        cognitive_style_safe=True,
    ),
)


def make_ucc_send_email_registry() -> UCCSubstrateRegistry:
    registry = UCCSubstrateRegistry()
    registry.register(send_email_contract)
    return registry
