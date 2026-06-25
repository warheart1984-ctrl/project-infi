"""Decode governance executor — Approach 2 speculative + rollback runtime."""

from __future__ import annotations

from typing import Any, Callable

from src.aais_governed_llm_module import validate_governed_llm_envelope
from src.invariant_engine import InvariantEngine
from src.ugr.governed_llm_executor import (
    UGR_LLM_EXECUTOR_VERSION,
    UGR_LLM_TEMPERATURE,
    apply_ugr_temperature_cap,
    execute_governed_llm_proposal,
    llm_execution_enabled,
)


def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))


DECODE_GOVERNANCE_EXECUTOR_VERSION = "1.0"


def _temperature_invariant(provider_request: dict[str, Any] | None) -> dict[str, Any]:
    overrides = dict((provider_request or {}).get("generation_overrides") or {})
    temperature = float(overrides.get("temperature", overrides.get("temperature_max", 1.0)))
    temperature_max = float(overrides.get("temperature_max", temperature))
    if temperature <= UGR_LLM_TEMPERATURE and temperature_max <= UGR_LLM_TEMPERATURE:
        return {"name": "temperature_zero", "status": "pass", "details": f"temperature={temperature}"}
    return {
        "name": "temperature_zero",
        "status": "hard_fail",
        "details": f"temperature must be 0; got {temperature}/{temperature_max}",
    }


def run_checkpoint_validators(
    envelope: dict[str, Any],
    *,
    bridge_result: dict[str, Any],
    decode_bundle: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Traverse checkpoint nodes — mirrors llm_lane invariant checks."""
    bundle = dict(decode_bundle or {})
    nodes = list((bundle.get("check_graph") or {}).get("nodes") or [])
    checkpoint_validators = [
        str(node.get("validator"))
        for node in nodes
        if str(node.get("position")) == "checkpoint"
    ]
    if not checkpoint_validators:
        checkpoint_validators = [
            "bridge_invariant",
            "governed_llm_envelope",
            "proposal_only",
            "temperature_zero",
        ]

    normalized = dict(bridge_result.get("normalized_input") or {})
    governance = dict(bridge_result.get("governance_packet") or {})
    results: list[dict[str, Any]] = []
    for validator in checkpoint_validators:
        if validator == "bridge_invariant":
            existing = bridge_result.get("bridge_invariant")
            if isinstance(existing, dict) and existing.get("status") == "pass":
                outcome = existing
            else:
                outcome = InvariantEngine.validate_bridge_packet(normalized, governance)
            results.append(
                {
                    "name": validator,
                    "status": "pass" if outcome.get("allows") else "hard_fail",
                    "details": outcome.get("status"),
                }
            )
        elif validator == "governed_llm_envelope":
            if validate_governed_llm_envelope(envelope):
                results.append({"name": validator, "status": "pass", "details": envelope.get("status")})
            else:
                results.append({"name": validator, "status": "hard_fail", "details": "invalid envelope"})
        elif validator == "proposal_only":
            if envelope.get("proposal_only") is True:
                results.append({"name": validator, "status": "pass", "details": "ok"})
            else:
                results.append({"name": validator, "status": "hard_fail", "details": "proposal_only required"})
        elif validator == "temperature_zero":
            capped = apply_ugr_temperature_cap(dict(envelope.get("provider_request") or {}))
            results.append(_temperature_invariant(capped))
        elif validator == "wonder_gate":
            from src.wonder.validation import validate_wonder_permitted

            outcome = validate_wonder_permitted(
                normalized,
                governance,
                bridge_result=bridge_result,
            )
            if outcome.get("status") == "skipped":
                results.append({"name": validator, "status": "skipped", "details": outcome.get("summary")})
            else:
                results.append(
                    {
                        "name": validator,
                        "status": "pass" if outcome.get("allows") else "hard_fail",
                        "details": outcome.get("summary"),
                        "wonder_verdict": outcome.get("wonder_verdict"),
                    }
                )
        elif validator in ("rls_admissibility", "rls_reasoning_admissible"):
            from src.rls.validation import validate_rls_admissible

            outcome = validate_rls_admissible(
                normalized,
                governance,
                bridge_result=bridge_result,
                envelope=envelope,
                record_quarantine=False,
            )
            if outcome.get("status") == "skipped":
                results.append({"name": validator, "status": "skipped", "details": outcome.get("summary")})
            else:
                results.append(
                    {
                        "name": validator,
                        "status": "pass" if outcome.get("allows") else "hard_fail",
                        "details": outcome.get("summary"),
                        "rls_verdict": outcome.get("rls_verdict"),
                    }
                )
        else:
            results.append({"name": validator, "status": "skipped", "details": "unknown validator"})
    return results


def _apply_rollback_policy(
    rollback_policy: dict[str, Any],
    *,
    session_id: str | None = None,
) -> list[str]:
    applied: list[str] = []
    actions = list(rollback_policy.get("actions") or [])
    for action in actions:
        if not action.get("enabled"):
            continue
        target = str(action.get("target") or "")
        if target == "conversation_memory_assistant_turn" and session_id:
            try:
                from src.conversation_memory import conversation_memory

                session = conversation_memory.get_session(session_id)
                if session is not None:
                    session.rollback_last_assistant_turn()
                    applied.append(target)
                else:
                    applied.append(f"{target}:noop")
            except Exception:
                applied.append(f"{target}:noop")
        elif target in {"draft_buffer", "proposed_odl_node"}:
            applied.append(f"{target}:marked")
        else:
            applied.append(f"{target}:skipped")
    return applied


def _escalate(
    escalation_hooks: dict[str, Any],
    *,
    attempts: int,
    violations: list[dict[str, Any]],
    session_id: str | None = None,
    otem_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    escalate_to = str(escalation_hooks.get("escalate_to") or "block")
    if escalation_hooks.get("constitutional_amendment_gate"):
        return {
            "status": "BLOCKED",
            "escalate_to": "constitutional_amendment",
            "reason": "constitutional_amendment_gate",
            "violations": violations,
        }
    if escalation_hooks.get("otem_ceiling_gate"):
        return {
            "status": "ESCALATED",
            "escalate_to": "otem_ceiling",
            "reason": "containment_mode_active",
            "violations": violations,
        }
    if escalation_hooks.get("otem_gate"):
        try:
            from src.otem_execution_approval_bridge import maybe_enqueue_otem_execution_approval

            gate = maybe_enqueue_otem_execution_approval(
                session_id,
                {
                    "status": "detected",
                    "task": "decode_governance_exhausted",
                    "restated_task": "decode_governance_exhausted",
                    "plan": [],
                    "workflow_handoff": {
                        "template_name": "decode_governance_escalation",
                        "rationale": "Decode governance checkpoint violations exhausted rollback budget.",
                        "details": {"attempts": attempts, "violations": violations},
                    },
                    **(otem_result or {}),
                },
            )
            if gate:
                return {
                    "status": "ESCALATED",
                    "escalate_to": "otem",
                    "gate": gate,
                    "reason": "checkpoint_violations_exhausted",
                }
            return {
                "status": "BLOCKED",
                "escalate_to": escalate_to,
                "reason": "otem_gate_not_enqueued",
                "violations": violations,
            }
        except Exception as exc:
            return {
                "status": "BLOCKED",
                "escalate_to": escalate_to,
                "reason": "otem_gate_unavailable",
                "error": str(exc),
            }
    if escalation_hooks.get("operator_approval"):
        return {
            "status": "ESCALATED",
            "escalate_to": "operator",
            "reason": "operator_approval_required",
            "violations": violations,
        }
    return {
        "status": "BLOCKED",
        "escalate_to": "block",
        "reason": "checkpoint_violations_exhausted",
        "violations": violations,
    }


def execute_with_decode_governance(
    envelope: dict[str, Any],
    *,
    bridge_result: dict[str, Any],
    question: str = "",
    governance_ir: dict[str, Any] | None = None,
    decode_bundle: dict[str, Any] | None = None,
    provider_registry_instance: Any | None = None,
    force_execute: bool = False,
    generate_candidate: Callable[..., dict[str, Any]] | None = None,
    session_id: str | None = None,
    preview_only: bool = False,
) -> dict[str, Any]:
    """Run governed LLM execution with checkpoint traversal and rollback."""
    if preview_only:
        normalized = dict(bridge_result.get("normalized_input") or {})
        payload = dict(normalized.get("payload") or envelope or {})
        requires_amendment = bool(payload.get("requires_constitutional_amendment"))
        return _wrap_ul_payload({
            "status": "preview",
            "allows": not requires_amendment,
            "preview_only": True,
            "executor_version": DECODE_GOVERNANCE_EXECUTOR_VERSION,
            "governance_ir_fingerprint": (governance_ir or {}).get("ir_fingerprint"),
            "proposal_only": True,
            "execution_authority": "none",
        })

    bundle = dict(decode_bundle or bridge_result.get("decode_governance_bundle") or {})
    rollback_policy = dict(bundle.get("rollback_policy") or {})
    escalation_hooks = dict(bundle.get("escalation_hooks") or {})
    max_rollbacks = int(rollback_policy.get("max_rollbacks") or 0)

    ingress = None
    if bundle:
        from src.invariant_compiler import apply_ingress_plan

        normalized = dict(bridge_result.get("normalized_input") or {})
        governance = dict(bridge_result.get("governance_packet") or {})
        ingress = apply_ingress_plan(normalized, governance, decode_bundle=bundle)
        if not ingress.get("allows"):
            return _wrap_ul_payload({
                "status": "BLOCKED",
                "reason": "ingress_plan_failed",
                "ingress": ingress,
                "executor_version": DECODE_GOVERNANCE_EXECUTOR_VERSION,
                "governance_ir_fingerprint": (governance_ir or {}).get("ir_fingerprint"),
                "proposal_only": True,
                "execution_authority": "none",
            })

    pre_checkpoint = run_checkpoint_validators(envelope, bridge_result=bridge_result, decode_bundle=bundle)
    if any(item.get("status") == "hard_fail" for item in pre_checkpoint):
        return _wrap_ul_payload({
            "status": "BLOCKED",
            "reason": "pre_execution_checkpoint_failed",
            "checkpoint_results": pre_checkpoint,
            "executor_version": DECODE_GOVERNANCE_EXECUTOR_VERSION,
            "proposal_only": True,
            "execution_authority": "none",
        })

    generator = generate_candidate or execute_governed_llm_proposal
    attempts = 0
    rollbacks_applied: list[list[str]] = []
    violations_trace: list[dict[str, Any]] = []
    last_execution: dict[str, Any] | None = None

    total_attempts = max(1, max_rollbacks + 1)
    for attempt in range(1, total_attempts + 1):
        attempts = attempt
        execution = generator(
            envelope,
            bridge_result=bridge_result,
            question=question,
            provider_registry_instance=provider_registry_instance,
            force_execute=force_execute or llm_execution_enabled(),
        )
        last_execution = execution
        if execution.get("status") != "EXECUTED":
            return _wrap_ul_payload({
                **execution,
                "decode_governance": {
                    "attempts": attempts,
                    "ingress": ingress,
                    "pre_checkpoint": pre_checkpoint,
                    "rollbacks_applied": rollbacks_applied,
                },
                "executor_version": DECODE_GOVERNANCE_EXECUTOR_VERSION,
            })

        post_checkpoint = run_checkpoint_validators(envelope, bridge_result=bridge_result, decode_bundle=bundle)
        failed = [item for item in post_checkpoint if item.get("status") == "hard_fail"]
        if not failed:
            return _wrap_ul_payload({
                **execution,
                "decode_governance": {
                    "attempts": attempts,
                    "ingress": ingress,
                    "pre_checkpoint": pre_checkpoint,
                    "post_checkpoint": post_checkpoint,
                    "rollbacks_applied": rollbacks_applied,
                    "governance_ir_fingerprint": (governance_ir or {}).get("ir_fingerprint"),
                    "bundle_fingerprint": bundle.get("bundle_fingerprint"),
                },
                "executor_version": DECODE_GOVERNANCE_EXECUTOR_VERSION,
            })

        violations_trace.extend(failed)
        if attempt <= max_rollbacks:
            applied = _apply_rollback_policy(rollback_policy, session_id=session_id)
            rollbacks_applied.append(applied)

            adapter_decision = None
            if bundle.get("authority_mask_spec"):
                from src.providers.governance_adapters import (
                    DECISION_ESCALATE,
                    ProviderContext,
                    run_decode_governance,
                )

                provider_request = dict(envelope.get("provider_request") or {})
                provider_ctx = ProviderContext(
                    provider_id=str(provider_request.get("provider") or "local").strip().lower(),
                    site_id=str(
                        (bundle.get("authority_mask_spec") or {}).get("active_site_id")
                        or "tool_call_schema"
                    ),
                    checkpoint_failures=tuple(failed),
                    attempt=attempt,
                    decoded_output={"content": execution.get("content")},
                )
                adapter_decision = run_decode_governance(provider_ctx, bundle)
                if adapter_decision is not None:
                    applied.append(f"adapter:{adapter_decision.decision}")
                    if adapter_decision.generation_overrides:
                        envelope = dict(envelope)
                        merged_request = dict(envelope.get("provider_request") or {})
                        overrides = dict(merged_request.get("generation_overrides") or {})
                        overrides.update(adapter_decision.generation_overrides)
                        merged_request["generation_overrides"] = overrides
                        envelope["provider_request"] = merged_request
                    if adapter_decision.decision == DECISION_ESCALATE:
                        escalation = _escalate(
                            escalation_hooks,
                            attempts=attempt,
                            violations=violations_trace,
                            session_id=session_id,
                            otem_result=dict(bridge_result.get("otem_result") or {}),
                        )
                        status = escalation.get("status", "BLOCKED")
                        return _wrap_ul_payload({
                            "status": status if status in {"EXECUTED", "SKIPPED"} else "BLOCKED",
                            "reason": escalation.get("reason", "adapter_escalate"),
                            "executor_version": DECODE_GOVERNANCE_EXECUTOR_VERSION,
                            "module_id": execution.get("module_id"),
                            "provider": execution.get("provider"),
                            "content": execution.get("content"),
                            "proposal_only": status != "EXECUTED",
                            "execution_authority": "none" if status != "EXECUTED" else "governed_commit",
                            "decode_governance": {
                                "attempts": attempts,
                                "ingress": ingress,
                                "pre_checkpoint": pre_checkpoint,
                                "post_checkpoint": post_checkpoint,
                                "rollbacks_applied": rollbacks_applied,
                                "adapter_decision": adapter_decision.to_dict(),
                                "violations": violations_trace,
                            },
                        })

            if rollback_policy.get("tighten_on_violation") or (
                adapter_decision is not None and adapter_decision.sampling_tighten
            ):
                capped = apply_ugr_temperature_cap(dict(envelope.get("provider_request") or {}))
                envelope = dict(envelope)
                envelope["provider_request"] = capped
            continue

    escalation = _escalate(
        escalation_hooks,
        attempts=attempts,
        violations=violations_trace,
        session_id=session_id,
        otem_result=dict(bridge_result.get("otem_result") or {}),
    )
    status = escalation.get("status", "BLOCKED")
    return _wrap_ul_payload({
        "status": status if status in {"EXECUTED", "SKIPPED"} else "BLOCKED",
        "reason": escalation.get("reason", "decode_governance_exhausted"),
        "executor_version": DECODE_GOVERNANCE_EXECUTOR_VERSION,
        "module_id": last_execution.get("module_id") if last_execution else None,
        "provider": last_execution.get("provider") if last_execution else None,
        "content": (last_execution or {}).get("content"),
        "proposal_only": status != "EXECUTED",
        "execution_authority": "none" if status != "EXECUTED" else "governed_commit",
        "decode_governance": {
            "attempts": attempts,
            "ingress": ingress,
            "pre_checkpoint": pre_checkpoint,
            "violations": violations_trace,
            "rollbacks_applied": rollbacks_applied,
            "escalation": escalation,
            "governance_ir_fingerprint": (governance_ir or {}).get("ir_fingerprint"),
            "bundle_fingerprint": bundle.get("bundle_fingerprint"),
        },
    })
