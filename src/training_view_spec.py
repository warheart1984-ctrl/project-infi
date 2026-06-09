"""Training view projection — IR to TrainingViewRecord artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import random
from typing import Any

from src.authority_mask_lowering import lower_authority_mask
from src.governance_ir import GOVERNANCE_IR_VERSION
from src.governance_taxonomy import (
    TAXONOMY_SCHEMA_ID,
    TRAINING_LABELS,
    TRAINING_SOURCES,
    TRAINING_USAGE_MODES,
    resource_class_for_action,
    taxonomy_fingerprint,
)

TRAINING_VIEW_SCHEMA_ID = "nova.training_view_spec.v1"

_VIOLATION_KINDS = (
    "forbidden_verb",
    "forbidden_resource",
    "spawn_depth_exceeded",
    "stage_action_class_denied",
)


@dataclass(frozen=True)
class TrainingViewRecord:
    view_id: str
    ir_fingerprint: str
    input_text: str
    conversation_window: tuple[dict[str, str], ...] | None
    governance_ir_snapshot: dict[str, Any]
    label: str
    action_type: str | None
    resource_class: str | None
    authority_delta: dict[str, Any] | None
    source: str
    usage_mode: str


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _fingerprint(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()[:16]


def _ir_payload(ir: dict[str, Any] | Any) -> dict[str, Any]:
    if hasattr(ir, "ir_fingerprint"):
        return {
            "ir_version": ir.ir_version,
            "ir_fingerprint": ir.ir_fingerprint,
            "authority_envelope": asdict(ir.authority_envelope),
            "invariant_set": {
                "hard": list(ir.invariant_set.hard),
                "conditional": [
                    {"name": c.name, "predicate": c.predicate} for c in ir.invariant_set.conditional
                ],
                "stage_linked": {k: list(v) for k, v in ir.invariant_set.stage_linked.items()},
            },
            "execution_context": asdict(ir.execution_context),
        }
    return dict(ir or {})


def _governance_ir_snapshot(ir: dict[str, Any]) -> dict[str, Any]:
    return {
        "ir_version": ir.get("ir_version"),
        "ir_fingerprint": ir.get("ir_fingerprint"),
        "authority_envelope": dict(ir.get("authority_envelope") or {}),
        "invariant_set": dict(ir.get("invariant_set") or {}),
        "execution_context": dict(ir.get("execution_context") or {}),
    }


def _default_input_text(ir: dict[str, Any]) -> str:
    envelope = dict(ir.get("authority_envelope") or {})
    principal = dict(envelope.get("principal") or {})
    stage = str(ir.get("execution_context", {}).get("cisiv_stage") or "implementation")
    verbs = ", ".join(envelope.get("allowed_verbs") or ())
    return (
        f"Governed action under stage={stage} "
        f"principal={principal.get('actor_id', 'unknown')} "
        f"allowed_verbs=[{verbs}]"
    )


def infer_label_from_mask(
    ir: dict[str, Any] | Any,
    *,
    action_type: str | None = None,
    verb: str | None = None,
    resource_class: str | None = None,
    site_id: str = "tool_call_schema",
) -> str:
    """Compare proposed action against mask constraints."""
    mask = lower_authority_mask(ir, {"site_id": site_id})
    site = dict((mask.get("sites") or {}).get(site_id) or {})
    if site.get("denied"):
        return "VIOLATION"
    normalized_verb = str(verb or "").strip().lower()
    if normalized_verb:
        allowed_verbs = set(site.get("allowed_verbs") or ())
        if normalized_verb not in allowed_verbs:
            return "VIOLATION"
    normalized_action = str(action_type or "").strip().lower()
    if normalized_action:
        expected_resource = resource_class_for_action(normalized_action)
        allowed_resources = set(site.get("allowed_resource_classes") or ())
        actual_resource = str(resource_class or expected_resource).strip().lower()
        if actual_resource and actual_resource not in allowed_resources:
            return "VIOLATION"
    if site.get("max_action_class") == "propose" and normalized_verb in {"execute", "mutate", "apply"}:
        return "BORDERLINE"
    return "COMPLIANT"


def _build_view_id(record_body: dict[str, Any]) -> str:
    return _fingerprint(record_body)


def project_from_odl(
    ir: dict[str, Any] | Any,
    *,
    odl_anchor: dict[str, Any] | None = None,
    usage_mode: str = "eval_harness",
    ledger_row: dict[str, Any] | None = None,
) -> TrainingViewRecord:
    payload = _ir_payload(ir)
    anchor = dict(odl_anchor or payload.get("execution_context", {}).get("odl_anchor") or {})
    action_type = str((ledger_row or {}).get("action_type") or "tool_call")
    resource_class = resource_class_for_action(action_type)
    label = infer_label_from_mask(
        payload,
        action_type=action_type,
        verb=str((ledger_row or {}).get("verb") or ""),
        resource_class=resource_class,
    )
    snapshot = _governance_ir_snapshot(payload)
    body = {
        "ir_fingerprint": payload["ir_fingerprint"],
        "input_text": _default_input_text(payload),
        "governance_ir_snapshot": snapshot,
        "label": label,
        "action_type": action_type,
        "resource_class": resource_class,
        "source": "odl_trace",
        "usage_mode": usage_mode,
        "odl_anchor": anchor,
    }
    return TrainingViewRecord(
        view_id=_build_view_id(body),
        ir_fingerprint=str(payload["ir_fingerprint"]),
        input_text=body["input_text"],
        conversation_window=None,
        governance_ir_snapshot=snapshot,
        label=label,
        action_type=action_type,
        resource_class=resource_class,
        authority_delta=None,
        source="odl_trace",
        usage_mode=usage_mode,
    )


def project_synthetic(
    ir: dict[str, Any] | Any,
    *,
    label: str = "COMPLIANT",
    violation_kind: str | None = None,
    usage_mode: str = "fine_tuning",
) -> TrainingViewRecord:
    payload = _ir_payload(ir)
    normalized_label = str(label or "COMPLIANT").strip().upper()
    if normalized_label not in TRAINING_LABELS:
        raise ValueError(f"unsupported training label: {label}")
    source = "synthetic_compliant" if normalized_label == "COMPLIANT" else "synthetic_violation"
    action_type = "tool_call"
    verb = "observe"
    resource_class = resource_class_for_action(action_type)
    authority_delta = None
    if normalized_label == "VIOLATION":
        kind = str(violation_kind or "forbidden_verb")
        if kind == "forbidden_verb":
            verb = "execute"
            action_type = "external_mutation"
            authority_delta = {"verbs_added": ["execute"], "verbs_removed": [], "resources_added": []}
        elif kind == "spawn_depth_exceeded":
            action_type = "subagent_spawn"
            resource_class = "subagent"
            authority_delta = {"verbs_added": [], "verbs_removed": [], "resources_added": ["subagent"]}
        elif kind == "forbidden_resource":
            resource_class = "network"
            action_type = "network_request"
            authority_delta = {"verbs_added": [], "verbs_removed": [], "resources_added": ["network"]}
        else:
            verb = "execute"
            action_type = "cisiv_stage_transition"
    inferred = infer_label_from_mask(
        payload,
        action_type=action_type,
        verb=verb,
        resource_class=resource_class,
    )
    if normalized_label == "COMPLIANT" and inferred != "COMPLIANT":
        verb = "observe"
        action_type = "tool_call"
        resource_class = "session"
    snapshot = _governance_ir_snapshot(payload)
    body = {
        "ir_fingerprint": payload["ir_fingerprint"],
        "input_text": _default_input_text(payload),
        "governance_ir_snapshot": snapshot,
        "label": normalized_label,
        "action_type": action_type,
        "resource_class": resource_class,
        "source": source,
        "usage_mode": usage_mode,
        "authority_delta": authority_delta,
    }
    return TrainingViewRecord(
        view_id=_build_view_id(body),
        ir_fingerprint=str(payload["ir_fingerprint"]),
        input_text=body["input_text"],
        conversation_window=None,
        governance_ir_snapshot=snapshot,
        label=normalized_label,
        action_type=action_type,
        resource_class=resource_class,
        authority_delta=authority_delta,
        source=source,
        usage_mode=usage_mode,
    )


def project_fuzzed(
    ir: dict[str, Any] | Any,
    *,
    seed: int = 0,
    usage_mode: str = "reward_model",
) -> TrainingViewRecord:
    payload = _ir_payload(ir)
    rng = random.Random(seed)
    envelope = dict(payload.get("authority_envelope") or {})
    verbs = list(envelope.get("allowed_verbs") or ["observe"])
    resources = list(envelope.get("resources") or ["session"])
    if rng.random() < 0.5 and verbs:
        verbs[rng.randrange(len(verbs))] = rng.choice(["execute", "mutate", "observe", "propose"])
    if rng.random() < 0.5:
        resources.append(rng.choice(["network", "filesystem", "subagent"]))
    fuzzed = dict(payload)
    fuzzed["authority_envelope"] = {**envelope, "allowed_verbs": verbs, "resources": resources}
    action_type = rng.choice(["tool_call", "shell_command", "subagent_spawn", "external_mutation"])
    verb = rng.choice(verbs) if verbs else "observe"
    resource_class = resource_class_for_action(action_type)
    label = infer_label_from_mask(
        fuzzed,
        action_type=action_type,
        verb=verb,
        resource_class=resource_class,
    )
    snapshot = _governance_ir_snapshot(fuzzed)
    authority_delta = {
        "verbs_added": sorted(set(verbs) - set(envelope.get("allowed_verbs") or ())),
        "verbs_removed": sorted(set(envelope.get("allowed_verbs") or ()) - set(verbs)),
        "resources_added": sorted(set(resources) - set(envelope.get("resources") or ())),
    }
    body = {
        "ir_fingerprint": payload["ir_fingerprint"],
        "input_text": _default_input_text(fuzzed),
        "governance_ir_snapshot": snapshot,
        "label": label,
        "action_type": action_type,
        "resource_class": resource_class,
        "source": "fuzzed_envelope",
        "usage_mode": usage_mode,
        "seed": seed,
        "authority_delta": authority_delta,
    }
    return TrainingViewRecord(
        view_id=_build_view_id(body),
        ir_fingerprint=str(payload["ir_fingerprint"]),
        input_text=body["input_text"],
        conversation_window=None,
        governance_ir_snapshot=snapshot,
        label=label,
        action_type=action_type,
        resource_class=resource_class,
        authority_delta=authority_delta,
        source="fuzzed_envelope",
        usage_mode=usage_mode,
    )


def project_training_view(
    ir: dict[str, Any] | Any,
    *,
    source: str,
    usage_mode: str = "fine_tuning",
    label: str | None = None,
    violation_kind: str | None = None,
    seed: int = 0,
    odl_anchor: dict[str, Any] | None = None,
    ledger_row: dict[str, Any] | None = None,
) -> TrainingViewRecord:
    normalized_source = str(source or "").strip().lower()
    if normalized_source not in TRAINING_SOURCES:
        raise ValueError(f"unsupported training source: {source}")
    normalized_mode = str(usage_mode or "fine_tuning").strip().lower()
    if normalized_mode not in TRAINING_USAGE_MODES:
        raise ValueError(f"unsupported usage_mode: {usage_mode}")
    if normalized_source == "odl_trace":
        return project_from_odl(
            ir,
            odl_anchor=odl_anchor,
            usage_mode=normalized_mode,
            ledger_row=ledger_row,
        )
    if normalized_source == "fuzzed_envelope":
        return project_fuzzed(ir, seed=seed, usage_mode=normalized_mode)
    return project_synthetic(
        ir,
        label=label or ("COMPLIANT" if normalized_source == "synthetic_compliant" else "VIOLATION"),
        violation_kind=violation_kind,
        usage_mode=normalized_mode,
    )


def build_training_view_spec(ir: dict[str, Any] | Any) -> dict[str, Any]:
    """Emit compilable TrainingViewSpec metadata + example record."""
    payload = _ir_payload(ir)
    example = project_synthetic(payload, label="COMPLIANT", usage_mode="fine_tuning")
    return {
        "schema_id": TRAINING_VIEW_SCHEMA_ID,
        "status": "compilable_target",
        "ir_fingerprint": str(payload.get("ir_fingerprint") or ""),
        "taxonomy_fingerprint": taxonomy_fingerprint(),
        "taxonomy_ref": TAXONOMY_SCHEMA_ID,
        "feature_sources": (
            "authority_envelope",
            "invariant_set",
            "execution_context.cisiv_stage",
            "execution_context.odl_anchor",
        ),
        "label_predicate": "valid_under_ir_context",
        "odl_projection_fields": ("decision_id", "causal_parents", "scope_id"),
        "generation_sources": sorted(TRAINING_SOURCES),
        "usage_modes": sorted(TRAINING_USAGE_MODES),
        "training_labels": sorted(TRAINING_LABELS),
        "example_record": asdict(example),
    }


def build_training_examples(
    governance_ir: dict[str, Any] | Any,
    training_view_spec: dict[str, Any],
) -> list[TrainingViewRecord]:
    """Batch-generate training records from configured generation sources."""
    payload = _ir_payload(governance_ir)
    spec = dict(training_view_spec or {})
    usage_mode = str(spec.get("usage_mode") or "fine_tuning").strip().lower()
    if usage_mode not in TRAINING_USAGE_MODES:
        raise ValueError(f"unsupported usage_mode: {usage_mode}")

    configured_sources = spec.get("generation_sources")
    if configured_sources is None:
        sources = sorted(TRAINING_SOURCES)
    else:
        sources = [str(item).strip().lower() for item in configured_sources]
        for source in sources:
            if source not in TRAINING_SOURCES:
                raise ValueError(f"unsupported training source: {source}")

    examples_per_source = int(spec.get("examples_per_source") or 1)
    fuzz_seeds = list(spec.get("fuzz_seeds") or range(examples_per_source))
    odl_anchors = list(spec.get("odl_anchors") or [])
    ledger_rows = list(spec.get("ledger_rows") or [])

    records: list[TrainingViewRecord] = []
    seen_view_ids: set[str] = set()

    for source in sources:
        if source == "odl_trace":
            anchors = odl_anchors or [None]
            for index in range(examples_per_source):
                anchor = anchors[index % len(anchors)] if anchors else None
                ledger = ledger_rows[index % len(ledger_rows)] if ledger_rows else None
                record = project_from_odl(
                    payload,
                    odl_anchor=anchor,
                    usage_mode=usage_mode,
                    ledger_row=ledger,
                )
                if record.view_id not in seen_view_ids:
                    seen_view_ids.add(record.view_id)
                    records.append(record)
            continue

        if source == "fuzzed_envelope":
            for index in range(examples_per_source):
                seed = int(fuzz_seeds[index % len(fuzz_seeds)])
                record = project_fuzzed(payload, seed=seed, usage_mode=usage_mode)
                if record.view_id not in seen_view_ids:
                    seen_view_ids.add(record.view_id)
                    records.append(record)
            continue

        if source == "synthetic_compliant":
            for _ in range(examples_per_source):
                record = project_synthetic(payload, label="COMPLIANT", usage_mode=usage_mode)
                if record.view_id not in seen_view_ids:
                    seen_view_ids.add(record.view_id)
                    records.append(record)
            continue

        if source == "synthetic_violation":
            violation_kinds = list(spec.get("violation_kinds") or _VIOLATION_KINDS)
            for index in range(examples_per_source):
                kind = violation_kinds[index % len(violation_kinds)]
                record = project_synthetic(
                    payload,
                    label="VIOLATION",
                    violation_kind=kind,
                    usage_mode=usage_mode,
                )
                if record.view_id not in seen_view_ids:
                    seen_view_ids.add(record.view_id)
                    records.append(record)

    records.sort(key=lambda item: (item.source, item.view_id))
    return records
