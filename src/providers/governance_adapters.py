"""Provider governance adapters — consume compiler mask/bundle outputs at runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Protocol

GOVERNANCE_ADAPTER_VERSION = "1.0"

DECISION_ALLOW = "ALLOW"
DECISION_RETRY = "RETRY"
DECISION_ROLLBACK = "ROLLBACK"
DECISION_ESCALATE = "ESCALATE"
DECISION_BLOCK = "BLOCK"

MASK_SURFACE_LOGIT = "logit_mask"
MASK_SURFACE_STRUCTURED = "structured_output"
MASK_SURFACE_SAMPLING = "sampling_config"

_STUB_PROVIDER_IDS = frozenset({"openai_compatible", "anthropic", "openrouter", "claude", "http_chat"})


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class ProviderContext:
    provider_id: str
    site_id: str = "tool_call_schema"
    decode_context: dict[str, Any] = field(default_factory=dict)
    provider_request: dict[str, Any] | None = None
    messages: list[dict[str, Any]] | None = None
    checkpoint_failures: tuple[dict[str, Any], ...] = ()
    attempt: int = 1
    decoded_output: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "site_id": self.site_id,
            "decode_context": dict(self.decode_context),
            "provider_request": dict(self.provider_request or {}),
            "messages": list(self.messages or []),
            "checkpoint_failures": [dict(item) for item in self.checkpoint_failures],
            "attempt": self.attempt,
            "decoded_output": dict(self.decoded_output or {}) if self.decoded_output else None,
        }


@dataclass(frozen=True)
class ProviderMask:
    mask_surface: str
    generation_overrides: dict[str, Any]
    schema_constraints: dict[str, Any]
    denied_token_ids: tuple[int, ...]
    instruction_fragments: tuple[str, ...]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mask_surface": self.mask_surface,
            "generation_overrides": dict(self.generation_overrides),
            "schema_constraints": dict(self.schema_constraints),
            "denied_token_ids": list(self.denied_token_ids),
            "instruction_fragments": list(self.instruction_fragments),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class DecodeGovernanceDecision:
    decision: str
    sampling_tighten: bool
    retry_hint: str | None
    rollback_action: str | None
    generation_overrides: dict[str, Any]
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "sampling_tighten": self.sampling_tighten,
            "retry_hint": self.retry_hint,
            "rollback_action": self.rollback_action,
            "generation_overrides": dict(self.generation_overrides),
            "details": dict(self.details),
        }


class GovernanceProviderAdapter(Protocol):
    provider_id: str

    def apply_authority_mask(
        self,
        provider_ctx: ProviderContext,
        authority_mask_spec: dict[str, Any],
    ) -> ProviderMask: ...

    def run_decode_governance(
        self,
        provider_ctx: ProviderContext,
        decode_governance_bundle: dict[str, Any],
    ) -> DecodeGovernanceDecision: ...


def _active_site_constraint(
    authority_mask_spec: dict[str, Any],
    site_id: str,
) -> dict[str, Any]:
    sites = dict(authority_mask_spec.get("sites") or {})
    return dict(sites.get(site_id) or sites.get("tool_call_schema") or {})


def _verb_token_id(verb: str) -> int:
    digest = sha256(verb.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100_000


def _deny_pattern_token_ids(patterns: tuple[str, ...] | list[str]) -> tuple[int, ...]:
    ids: list[int] = []
    for pattern in patterns or ():
        digest = sha256(str(pattern).encode("utf-8")).hexdigest()
        ids.append(int(digest[:8], 16) % 100_000)
    return tuple(sorted(set(ids)))


class ReferenceMockAdapter:
    """Deterministic logit-mask simulation for tests."""

    provider_id = "reference_mock"

    def apply_authority_mask(
        self,
        provider_ctx: ProviderContext,
        authority_mask_spec: dict[str, Any],
    ) -> ProviderMask:
        site_id = provider_ctx.site_id or str(authority_mask_spec.get("active_site_id") or "tool_call_schema")
        constraint = _active_site_constraint(authority_mask_spec, site_id)
        forbidden = tuple(constraint.get("forbidden_verbs") or ())
        deny_patterns = tuple(constraint.get("deny_patterns") or ())
        denied_ids = tuple(
            sorted({_verb_token_id(verb) for verb in forbidden} | set(_deny_pattern_token_ids(deny_patterns)))
        )
        return ProviderMask(
            mask_surface=MASK_SURFACE_LOGIT,
            generation_overrides={"temperature": 0.0, "temperature_max": 0.0},
            schema_constraints={
                "site_id": site_id,
                "allowed_verbs": list(constraint.get("allowed_verbs") or ()),
                "forbidden_verbs": list(forbidden),
                "denied": bool(constraint.get("denied")),
            },
            denied_token_ids=denied_ids,
            instruction_fragments=(),
            metadata={
                "implementation": "reference_mock",
                "adapter_version": GOVERNANCE_ADAPTER_VERSION,
                "mask_id": authority_mask_spec.get("mask_id"),
            },
        )

    def run_decode_governance(
        self,
        provider_ctx: ProviderContext,
        decode_governance_bundle: dict[str, Any],
    ) -> DecodeGovernanceDecision:
        rollback_policy = dict(decode_governance_bundle.get("rollback_policy") or {})
        max_rollbacks = int(rollback_policy.get("max_rollbacks") or 0)
        tighten = bool(rollback_policy.get("tighten_on_violation"))
        failures = list(provider_ctx.checkpoint_failures or ())
        if not failures:
            return DecodeGovernanceDecision(
                decision=DECISION_ALLOW,
                sampling_tighten=False,
                retry_hint=None,
                rollback_action=None,
                generation_overrides={},
                details={"reason": "no_checkpoint_failures"},
            )
        if provider_ctx.attempt <= max_rollbacks:
            action = "retry_with_tightened_sampling" if tighten else "retry"
            return DecodeGovernanceDecision(
                decision=DECISION_ROLLBACK if provider_ctx.attempt > 1 else DECISION_RETRY,
                sampling_tighten=tighten,
                retry_hint=action,
                rollback_action="checkpoint_rollback",
                generation_overrides={"temperature": 0.0, "temperature_max": 0.0},
                details={
                    "reason": "checkpoint_violation",
                    "failures": failures,
                    "attempt": provider_ctx.attempt,
                    "max_rollbacks": max_rollbacks,
                },
            )
        escalation = dict(decode_governance_bundle.get("escalation_hooks") or {})
        if escalation.get("operator_approval") or escalation.get("otem_gate"):
            return DecodeGovernanceDecision(
                decision=DECISION_ESCALATE,
                sampling_tighten=False,
                retry_hint="escalate",
                rollback_action=None,
                generation_overrides={},
                details={"reason": "rollback_budget_exhausted", "failures": failures},
            )
        return DecodeGovernanceDecision(
            decision=DECISION_BLOCK,
            sampling_tighten=False,
            retry_hint=None,
            rollback_action=None,
            generation_overrides={},
            details={"reason": "rollback_budget_exhausted", "failures": failures},
        )


class LocalGovernanceAdapter:
    """Structured-output + sampling constraints for the local provider stack."""

    provider_id = "local"

    def apply_authority_mask(
        self,
        provider_ctx: ProviderContext,
        authority_mask_spec: dict[str, Any],
    ) -> ProviderMask:
        site_id = provider_ctx.site_id or str(authority_mask_spec.get("active_site_id") or "tool_call_schema")
        constraint = _active_site_constraint(authority_mask_spec, site_id)
        allowed_verbs = list(constraint.get("allowed_verbs") or ())
        forbidden_verbs = list(constraint.get("forbidden_verbs") or ())
        deny_patterns = list(constraint.get("deny_patterns") or ())
        allowed_resources = list(constraint.get("allowed_resource_classes") or ())
        stop_sequences = [f"deny:{pattern}" for pattern in deny_patterns[:4]]
        fragments = [
            f"Governed decode site={site_id}.",
            f"Allowed verbs: {', '.join(allowed_verbs) or 'none'}.",
            f"Forbidden verbs: {', '.join(forbidden_verbs) or 'none'}.",
            f"Allowed resources: {', '.join(allowed_resources) or 'none'}.",
            "Emit only schema-compliant tool calls within authority envelope.",
        ]
        schema_constraints = {
            "site_id": site_id,
            "type": "object",
            "properties": {
                "verb": {"type": "string", "enum": allowed_verbs or ["observe"]},
                "resource_class": {"type": "string", "enum": allowed_resources or ["session"]},
                "action_class": {
                    "type": "string",
                    "enum": list(constraint.get("allowed_action_classes") or ("observe",)),
                },
            },
            "required": ["verb"],
            "additionalProperties": False,
        }
        if site_id in {"tool_call_schema", "external_mutation_command"}:
            schema_constraints["properties"]["tool_call"] = {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "enum": allowed_verbs or ["observe"]},
                    "arguments": {"type": "object"},
                },
            }
        return ProviderMask(
            mask_surface=MASK_SURFACE_STRUCTURED,
            generation_overrides={
                "temperature": 0.0,
                "temperature_max": 0.0,
                "max_tokens": 512,
                "stop": stop_sequences,
            },
            schema_constraints=schema_constraints,
            denied_token_ids=(),
            instruction_fragments=tuple(fragments),
            metadata={
                "implementation": "local",
                "adapter_version": GOVERNANCE_ADAPTER_VERSION,
                "mask_id": authority_mask_spec.get("mask_id"),
                "secondary_surface": MASK_SURFACE_SAMPLING,
            },
        )

    def run_decode_governance(
        self,
        provider_ctx: ProviderContext,
        decode_governance_bundle: dict[str, Any],
    ) -> DecodeGovernanceDecision:
        rollback_policy = dict(decode_governance_bundle.get("rollback_policy") or {})
        max_rollbacks = int(rollback_policy.get("max_rollbacks") or 0)
        tighten = bool(rollback_policy.get("tighten_on_violation"))
        failures = list(provider_ctx.checkpoint_failures or ())
        mask_spec = dict(decode_governance_bundle.get("authority_mask_spec") or {})
        site_id = provider_ctx.site_id or str(mask_spec.get("active_site_id") or "tool_call_schema")
        decoded = dict(provider_ctx.decoded_output or {})
        if decoded:
            violation = validate_decoded_output(
                ProviderContext(
                    provider_id=self.provider_id,
                    site_id=site_id,
                    decoded_output=decoded,
                ),
                mask_spec,
            )
            if violation:
                failures = failures or [violation]
        if not failures:
            return DecodeGovernanceDecision(
                decision=DECISION_ALLOW,
                sampling_tighten=False,
                retry_hint=None,
                rollback_action=None,
                generation_overrides={},
                details={"reason": "no_violations"},
            )
        if provider_ctx.attempt <= max_rollbacks:
            overrides = {"temperature": 0.0, "temperature_max": 0.0, "max_tokens": 256}
            return DecodeGovernanceDecision(
                decision=DECISION_ROLLBACK if provider_ctx.attempt > 1 else DECISION_RETRY,
                sampling_tighten=tighten,
                retry_hint="tighten_structured_output",
                rollback_action="structured_output_rollback",
                generation_overrides=overrides,
                details={"reason": "mask_violation", "failures": failures, "site_id": site_id},
            )
        escalation = dict(decode_governance_bundle.get("escalation_hooks") or {})
        if escalation.get("operator_approval") or escalation.get("otem_gate"):
            return DecodeGovernanceDecision(
                decision=DECISION_ESCALATE,
                sampling_tighten=False,
                retry_hint="escalate",
                rollback_action=None,
                generation_overrides={},
                details={"reason": "local_mask_exhausted", "failures": failures},
            )
        return DecodeGovernanceDecision(
            decision=DECISION_BLOCK,
            sampling_tighten=False,
            retry_hint=None,
            rollback_action=None,
            generation_overrides={},
            details={"reason": "local_mask_exhausted", "failures": failures},
        )


class StubGovernanceAdapter:
    """Passthrough adapter for HTTP/frontier providers not yet fully integrated."""

    def __init__(self, provider_id: str) -> None:
        self.provider_id = provider_id

    def apply_authority_mask(
        self,
        provider_ctx: ProviderContext,
        authority_mask_spec: dict[str, Any],
    ) -> ProviderMask:
        return ProviderMask(
            mask_surface=MASK_SURFACE_SAMPLING,
            generation_overrides={"temperature": 0.0, "temperature_max": 0.0},
            schema_constraints={"passthrough": True},
            denied_token_ids=(),
            instruction_fragments=(),
            metadata={
                "implementation": "stub",
                "adapter_version": GOVERNANCE_ADAPTER_VERSION,
                "provider_id": self.provider_id,
                "mask_id": authority_mask_spec.get("mask_id"),
            },
        )

    def run_decode_governance(
        self,
        provider_ctx: ProviderContext,
        decode_governance_bundle: dict[str, Any],
    ) -> DecodeGovernanceDecision:
        return DecodeGovernanceDecision(
            decision=DECISION_ALLOW,
            sampling_tighten=False,
            retry_hint=None,
            rollback_action=None,
            generation_overrides={},
            details={"implementation": "stub", "provider_id": self.provider_id},
        )


_REGISTRY: dict[str, GovernanceProviderAdapter] = {
    "reference_mock": ReferenceMockAdapter(),
    "local": LocalGovernanceAdapter(),
    "openai_compatible": StubGovernanceAdapter("openai_compatible"),
    "anthropic": StubGovernanceAdapter("anthropic"),
    "openrouter": StubGovernanceAdapter("openrouter"),
    "claude": StubGovernanceAdapter("claude"),
    "http_chat": StubGovernanceAdapter("http_chat"),
}


def get_governance_adapter(provider_id: str) -> GovernanceProviderAdapter:
    normalized = str(provider_id or "local").strip().lower()
    adapter = _REGISTRY.get(normalized)
    if adapter is not None:
        return adapter
    if normalized in _STUB_PROVIDER_IDS:
        return StubGovernanceAdapter(normalized)
    return _REGISTRY["local"]


def apply_authority_mask(
    provider_ctx: ProviderContext,
    authority_mask_spec: dict[str, Any] | None,
) -> ProviderMask | None:
    if not authority_mask_spec:
        return None
    adapter = get_governance_adapter(provider_ctx.provider_id)
    return adapter.apply_authority_mask(provider_ctx, authority_mask_spec)


def run_decode_governance(
    provider_ctx: ProviderContext,
    decode_governance_bundle: dict[str, Any] | None,
) -> DecodeGovernanceDecision | None:
    if not decode_governance_bundle:
        return None
    adapter = get_governance_adapter(provider_ctx.provider_id)
    return adapter.run_decode_governance(provider_ctx, decode_governance_bundle)


def merge_mask_into_provider_request(
    provider_request: dict[str, Any],
    provider_mask: ProviderMask | None,
) -> dict[str, Any]:
    if provider_mask is None:
        return dict(provider_request or {})
    merged = dict(provider_request or {})
    overrides = dict(merged.get("generation_overrides") or {})
    overrides.update(dict(provider_mask.generation_overrides or {}))
    merged["generation_overrides"] = overrides
    merged["governance_schema_constraints"] = dict(provider_mask.schema_constraints or {})
    merged["governance_mask_surface"] = provider_mask.mask_surface
    return merged


def merge_mask_into_messages(
    messages: list[dict[str, Any]],
    provider_mask: ProviderMask | None,
) -> list[dict[str, Any]]:
    if provider_mask is None or not provider_mask.instruction_fragments:
        return list(messages or [])
    updated = [dict(item) for item in messages or []]
    fragment = " ".join(provider_mask.instruction_fragments)
    if not fragment:
        return updated
    for index, message in enumerate(updated):
        if str(message.get("role")) == "system":
            content = str(message.get("content") or "").strip()
            updated[index] = {
                **message,
                "content": f"{content} {fragment}".strip() if content else fragment,
            }
            return updated
    updated.insert(0, {"role": "system", "content": fragment})
    return updated


def validate_decoded_output(
    provider_ctx: ProviderContext,
    authority_mask_spec: dict[str, Any],
) -> dict[str, Any] | None:
    decoded = dict(provider_ctx.decoded_output or {})
    if not decoded:
        return None
    site_id = provider_ctx.site_id or str(authority_mask_spec.get("active_site_id") or "tool_call_schema")
    constraint = _active_site_constraint(authority_mask_spec, site_id)
    if constraint.get("denied"):
        return {"name": "site_denied", "status": "hard_fail", "details": site_id}
    verb = str(decoded.get("verb") or decoded.get("tool_call", {}).get("name") or "").strip().lower()
    if not verb:
        return None
    allowed = {str(v).strip().lower() for v in constraint.get("allowed_verbs") or ()}
    forbidden = {str(v).strip().lower() for v in constraint.get("forbidden_verbs") or ()}
    if verb in forbidden or (allowed and verb not in allowed):
        return {
            "name": "authority_mask_verb",
            "status": "hard_fail",
            "details": f"verb={verb} forbidden for site={site_id}",
        }
    return None


def adapter_registry_snapshot() -> dict[str, Any]:
    return {
        "adapter_version": GOVERNANCE_ADAPTER_VERSION,
        "providers": sorted(_REGISTRY.keys()),
        "stub_providers": sorted(_STUB_PROVIDER_IDS),
    }
