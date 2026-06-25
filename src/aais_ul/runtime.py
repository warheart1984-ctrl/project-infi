"""AAIS UL Runtime Substrate — primary structural and governed command layer.

Combines AAIS-UL payload adaptation with the ARIS governed command substrate
(ForgeGate) so every runtime ingress, bridge hop, pipeline turn, and capability
result passes through one inspectable envelope before Jarvis delivery.
"""

# Mythic: Aais Ul Substrate Organ
# Engineering: AaisUlSubstrateEngine
from __future__ import annotations

from typing import Any

from src.aais_ul.layer import (
    DEFAULT_REGISTRY,
    ULRegistry,
    adapt_ingress,
    build_ul_snapshot,
)
from src.aais_ul.ul_runtime import SubstrateRuntime


SUBSTRATE_ID = "aais.ul_substrate"
SUBSTRATE_CONTRACT_VERSION = "aais.ul_substrate.v1"
SUBSTRATE_DOCTRINE = (
    "Nothing enters Jarvis raw. Everything passes through UL adaptation and "
    "the governed command substrate before execution."
)


class AAISULSubstrate:
    """Unified AAIS runtime substrate: UL adaptation + governed command dispatch."""

    def __init__(self, *, registry: ULRegistry | None = None) -> None:
        self.registry = registry or DEFAULT_REGISTRY
        self._command_runtime: Any | None = None

    def _command_engine(self) -> Any:
        if self._command_runtime is None:
            self._command_runtime = SubstrateRuntime()
        return self._command_runtime

    def adapt_ingress(self, raw: Any, *, required: bool = True) -> dict[str, Any]:
        """Mandatory UL adaptation for any raw ingress value."""
        return adapt_ingress(raw, registry=self.registry, required=required)

    def build_envelope(
        self,
        *,
        modules: list[dict[str, Any]] | None = None,
        provider_preview: dict[str, Any] | None = None,
        guardrail_state: dict[str, Any] | None = None,
        bridge_results: list[dict[str, Any]] | None = None,
        pipeline: dict[str, Any] | None = None,
        pipeline_packets: list[dict[str, Any]] | None = None,
        capability_results: list[dict[str, Any]] | None = None,
        proposals: list[dict[str, Any]] | None = None,
        ingress: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Build the full UL substrate envelope for one runtime surface."""
        ul_trace = build_ul_snapshot(
            modules=modules,
            provider_preview=provider_preview,
            guardrail_state=guardrail_state,
            bridge_results=bridge_results,
            pipeline=pipeline,
            pipeline_packets=pipeline_packets,
            capability_results=capability_results,
            proposals=proposals,
            ingress=ingress,
            registry=self.registry,
        )
        return {
            "substrate_id": SUBSTRATE_ID,
            "contract_version": SUBSTRATE_CONTRACT_VERSION,
            "doctrine": SUBSTRATE_DOCTRINE,
            "ul_trace": ul_trace,
            "adapter_count": len(self.registry.adapters),
            "primary": ul_trace.get("count", 0) > 0,
        }

    def wrap_bridge_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Attach UL substrate envelope to one cognitive bridge result."""
        envelope = self.build_envelope(
            bridge_results=[result],
            proposals=[result.get("governed_llm")] if result.get("governed_llm") else None,
            ingress=[result.get("normalized_input")] if result.get("normalized_input") else None,
        )
        wrapped = dict(result)
        wrapped["ul_substrate"] = envelope
        wrapped["ul_trace"] = envelope["ul_trace"]
        return wrapped

    def wrap_pipeline(self, pipeline: dict[str, Any]) -> dict[str, Any]:
        """Attach UL substrate envelope to one governed direct pipeline trace."""
        all_packets = [
            *(pipeline.get("forward_packets") or []),
            *(pipeline.get("service_packets") or []),
            *(pipeline.get("return_packets") or []),
        ]
        envelope = self.build_envelope(
            pipeline=pipeline,
            pipeline_packets=all_packets,
            bridge_results=list(pipeline.get("bridge_hops") or []),
        )
        wrapped = dict(pipeline)
        wrapped["ul_substrate"] = envelope
        wrapped["ul_trace"] = envelope["ul_trace"]
        return wrapped

    def wrap_capability_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Attach UL substrate envelope to one capability module result."""
        envelope = self.build_envelope(capability_results=[result])
        wrapped = dict(result)
        wrapped["ul_substrate"] = envelope
        wrapped["ul_trace"] = envelope["ul_trace"]
        return wrapped

    def wrap_modular_preview(self, preview: dict[str, Any]) -> dict[str, Any]:
        """Attach or refresh UL substrate on one modular provider preview."""
        ingress_items = [
            item
            for item in (preview.get("cloud_forge"), preview.get("cloud_forge_readout"))
            if isinstance(item, dict) and item
        ]
        envelope = self.build_envelope(
            modules=list(preview.get("modules") or []),
            provider_preview=preview.get("provider_payload"),
            guardrail_state=preview.get("guardrail_state"),
            ingress=ingress_items or None,
        )
        wrapped = dict(preview)
        wrapped["ul_substrate"] = envelope
        wrapped["ul_trace"] = envelope["ul_trace"]
        return wrapped

    def wrap_runtime_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Attach UL substrate envelope to one runtime subsystem snapshot."""
        envelope = self.build_envelope(ingress=[snapshot])
        wrapped = dict(snapshot)
        wrapped["ul_substrate"] = envelope
        wrapped["ul_trace"] = envelope["ul_trace"]
        return wrapped

    def wrap_operator_action(self, result: dict[str, Any]) -> dict[str, Any]:
        """Attach UL substrate to one Jarvis operator action response."""
        tool_result = dict(result.get("tool_result") or {})
        envelope = self.build_envelope(
            ingress=[tool_result] if tool_result else None,
            bridge_results=[result.get("cognitive_bridge")] if result.get("cognitive_bridge") else None,
        )
        wrapped = dict(result)
        wrapped["ul_substrate"] = envelope
        wrapped["ul_trace"] = envelope["ul_trace"]
        if tool_result:
            wrapped["tool_result"] = {**tool_result, "ul_substrate": envelope, "ul_trace": envelope["ul_trace"]}
        return wrapped

    def _maybe_emit_substrate_reward(self, payload: dict[str, Any], *, surface: str) -> None:
        trace_id = str(payload.get("trace_id") or payload.get("mission_id") or "")
        if not trace_id:
            return
        try:
            from src.ugr.rewards.reward_hooks import emit_substrate_envelope_attached

            emit_substrate_envelope_attached(
                tenant_id=str(payload.get("tenant_id") or "global"),
                operator_id=str(payload.get("operator_id") or "operator"),
                trace_id=trace_id,
                surface=surface,
            )
        except Exception:
            pass

    def wrap_ugr_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """Attach UL substrate to one UGR runtime response."""
        self._maybe_emit_substrate_reward(response, surface="ugr_response")
        envelope = self.build_envelope(
            ingress=[response],
            bridge_results=[response.get("bridge")] if response.get("bridge") else None,
        )
        wrapped = dict(response)
        wrapped["ul_substrate"] = envelope
        wrapped["ul_trace"] = envelope["ul_trace"]
        return wrapped

    def wrap_service_bridge_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Attach UL substrate to one capability service bridge result."""
        tool_result = dict(result.get("tool_result") or {}) if isinstance(result.get("tool_result"), dict) else {}
        capability_meta = dict(tool_result.get("capability") or {}) if isinstance(tool_result.get("capability"), dict) else {}
        ingress_items = [
            item
            for item in (result.get("execution_preview"), tool_result, capability_meta)
            if isinstance(item, dict) and item
        ]
        envelope = self.build_envelope(ingress=ingress_items or None)
        wrapped = dict(result)
        wrapped["ul_substrate"] = envelope
        wrapped["ul_trace"] = envelope["ul_trace"]
        if tool_result:
            wrapped["tool_result"] = {
                **tool_result,
                "ul_substrate": envelope,
                "ul_trace": envelope["ul_trace"],
            }
        return wrapped

    def wrap_cloud_forge_bundle(self, bundle: dict[str, Any]) -> dict[str, Any]:
        """Attach UL substrate to one Cloud Forge scheduling bundle."""
        readout = bundle.get("cloud_forge_readout")
        ingress_items = [
            item
            for item in (bundle, readout)
            if isinstance(item, dict) and item
        ]
        envelope = self.build_envelope(ingress=ingress_items or None)
        wrapped = dict(bundle)
        wrapped["ul_substrate"] = envelope
        wrapped["ul_trace"] = envelope["ul_trace"]
        if isinstance(readout, dict) and readout:
            wrapped["cloud_forge_readout"] = {
                **readout,
                "ul_substrate": envelope,
                "ul_trace": envelope["ul_trace"],
            }
        return wrapped

    def wrap_contractor_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Attach UL substrate to one Forge/ForgeEval contractor response."""
        ingress_items = [payload]
        ul_snapshot = payload.get("ul_snapshot")
        if isinstance(ul_snapshot, dict) and ul_snapshot.get("payloads"):
            ingress_items.append(ul_snapshot)
        envelope = self.build_envelope(ingress=ingress_items)
        wrapped = dict(payload)
        wrapped["ul_substrate"] = envelope
        wrapped["ul_trace"] = envelope["ul_trace"]
        return wrapped

    def execute_governed_command(
        self,
        source: str,
        *,
        context: dict[str, Any] | None = None,
        operator_present: bool = False,
    ) -> dict[str, Any]:
        """Execute governed substrate commands through the ARIS ForgeGate."""
        runtime = self._command_engine()
        result = runtime.execute(
            source,
            context=dict(context or {}),
            operator_present=operator_present,
        )
        envelope = self.build_envelope(
            ingress=[
                {
                    "type": "governed_command",
                    "source": source[:120],
                    "allowed": bool(result.allowed),
                }
            ]
        )
        return {
            "substrate_id": SUBSTRATE_ID,
            "contract_version": SUBSTRATE_CONTRACT_VERSION,
            "allowed": bool(result.allowed),
            "gate": {
                "allowed": bool(result.gate.allowed),
                "violations": [
                    {"rule": v.rule, "message": v.message}
                    for v in (result.gate.violations or [])
                ],
            },
            "audit": list(result.audit or []),
            "outputs": list(result.outputs or []),
            "error": result.error,
            "ul_substrate": envelope,
            "ul_trace": envelope["ul_trace"],
        }

    def status_payload(self) -> dict[str, Any]:
        """Return substrate inventory for blueprint and operator surfaces."""
        return {
            "substrate_id": SUBSTRATE_ID,
            "contract_version": SUBSTRATE_CONTRACT_VERSION,
            "doctrine": SUBSTRATE_DOCTRINE,
            "adapter_count": len(self.registry.adapters),
            "adapters": [adapter.name for adapter in self.registry.adapters],
            "command_substrate": "src.ul_substrate.ForgeGate",
            "identity_source": "UL",
            "governance_model": "CISIV",
        }


aais_ul_substrate = AAISULSubstrate()


def wrap_bridge_result(result: dict[str, Any]) -> dict[str, Any]:
    return aais_ul_substrate.wrap_bridge_result(result)


def wrap_pipeline(pipeline: dict[str, Any]) -> dict[str, Any]:
    return aais_ul_substrate.wrap_pipeline(pipeline)


def wrap_capability_result(result: dict[str, Any]) -> dict[str, Any]:
    return aais_ul_substrate.wrap_capability_result(result)


def wrap_modular_preview(preview: dict[str, Any]) -> dict[str, Any]:
    return aais_ul_substrate.wrap_modular_preview(preview)


def wrap_runtime_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    return aais_ul_substrate.wrap_runtime_snapshot(snapshot)


def wrap_operator_action(result: dict[str, Any]) -> dict[str, Any]:
    return aais_ul_substrate.wrap_operator_action(result)


def wrap_ugr_response(response: dict[str, Any]) -> dict[str, Any]:
    return aais_ul_substrate.wrap_ugr_response(response)


def wrap_service_bridge_result(result: dict[str, Any]) -> dict[str, Any]:
    return aais_ul_substrate.wrap_service_bridge_result(result)


def attach_ul_substrate(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Attach UL substrate when absent; no-op when already wrapped."""
    if not isinstance(payload, dict):
        return {}
    if payload.get("ul_substrate"):
        return payload
    return aais_ul_substrate.wrap_runtime_snapshot(dict(payload))


def wrap_cloud_forge_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    return aais_ul_substrate.wrap_cloud_forge_bundle(bundle)


def wrap_contractor_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return aais_ul_substrate.wrap_contractor_payload(payload)


def substrate_status() -> dict[str, Any]:
    return aais_ul_substrate.status_payload()
