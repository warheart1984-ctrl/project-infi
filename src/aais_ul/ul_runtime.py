"""UL command substrate (ForgeGate).

Minimal Actor Verb Multiplier grammar with default-deny posture for destructive verbs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_COMMAND_RE = re.compile(
    r"^\s*(?P<actor>[a-zA-Z_][\w.-]*)\s+"
    r"(?P<verb>[a-zA-Z_][\w.-]*)\s+"
    r"(?P<multiplier>x\d+)\s*$",
    re.IGNORECASE,
)

_DENIED_VERBS = frozenset(
    {
        "delete_repo",
        "destroy",
        "wipe",
        "purge",
        "format",
        "rm",
        "unlink",
    }
)


@dataclass
class GateViolation:
    rule: str
    message: str


@dataclass
class GateResult:
    allowed: bool
    violations: list[GateViolation] = field(default_factory=list)


@dataclass
class ExecuteResult:
    allowed: bool
    gate: GateResult
    audit: list[str] = field(default_factory=list)
    outputs: list[Any] = field(default_factory=list)
    error: str | None = None


class ForgeGate:
    """Default-deny gate for governed substrate commands."""

    def evaluate(
        self,
        *,
        actor: str,
        verb: str,
        multiplier: str,
        operator_present: bool = False,
        context: dict[str, Any] | None = None,
    ) -> GateResult:
        _ = (actor, multiplier, context)
        violations: list[GateViolation] = []
        verb_key = verb.lower()
        if verb_key in _DENIED_VERBS:
            violations.append(
                GateViolation(
                    rule="default_deny.destructive_verb",
                    message=(
                        f"verb '{verb}' is denied"
                        if operator_present
                        else f"verb '{verb}' requires operator presence"
                    ),
                )
            )
        return GateResult(allowed=not violations, violations=violations)


class SubstrateRuntime:
    """Parse and execute governed command strings through ForgeGate."""

    def __init__(self) -> None:
        self.gate = ForgeGate()

    def execute(
        self,
        source: str,
        *,
        context: dict[str, Any] | None = None,
        operator_present: bool = False,
    ) -> ExecuteResult:
        audit: list[str] = []
        match = _COMMAND_RE.match(source or "")
        if not match:
            gate = GateResult(
                allowed=False,
                violations=[
                    GateViolation(
                        rule="parse",
                        message="command does not match actor verb multiplier grammar",
                    )
                ],
            )
            return ExecuteResult(
                allowed=False,
                gate=gate,
                audit=audit,
                error="parse_error",
            )

        actor = match.group("actor")
        verb = match.group("verb")
        multiplier = match.group("multiplier")
        audit.append(f"parsed:{actor}/{verb}/{multiplier}")

        gate = self.gate.evaluate(
            actor=actor,
            verb=verb,
            multiplier=multiplier,
            operator_present=operator_present,
            context=context,
        )
        if not gate.allowed:
            return ExecuteResult(allowed=False, gate=gate, audit=audit)

        count = int(multiplier[1:]) if multiplier.lower().startswith("x") else 1
        outputs = [{"actor": actor, "verb": verb, "count": count, "status": "simulated"}]
        audit.append("executed:simulated")
        return ExecuteResult(allowed=True, gate=gate, audit=audit, outputs=outputs)
