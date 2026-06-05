"""Read-only ingestion adapters for temporal replay."""

# Engineering: TemporalReplayIngestorsEngine
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.temporal_replay.emitter_registry import resolve_emitter
from src.temporal_replay.event import new_event_id, payload_hash
from src.temporal_replay.paths import bridge_audit_path, default_runtime_dir

from src.project_infi_law import PROJECT_INFI_CONTRACT_VERSION
from src.ugr.invariants.cloud_manifold import CLOUD_INVARIANT_SET_VERSION


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _law_from_receipt_schema(schema: dict[str, Any]) -> dict[str, Any]:
    op_sig = dict(schema.get("operator_sig") or {})
    return {
        "law_id": "urg.cloud_forge",
        "law_version": str(schema.get("law_version") or schema.get("urg_version") or ""),
        "contract_version": PROJECT_INFI_CONTRACT_VERSION,
        "invariant_version": str(schema.get("invariant_version") or CLOUD_INVARIANT_SET_VERSION),
    }


def _boundary_from_receipt(schema: dict[str, Any]) -> dict[str, Any]:
    op_sig = dict(schema.get("operator_sig") or {})
    return {
        "boundary_digest": str(schema.get("boundary_digest") or ""),
        "tenant_id": str(op_sig.get("tenant_id") or "default"),
        "cloud_identity_hash": str(schema.get("cloud_identity_hash") or ""),
    }


def _extract_invariant_flags(row: dict[str, Any]) -> dict[str, Any]:
    results = row.get("invariant_results") or row.get("cloud_invariants") or []
    if isinstance(results, dict):
        results = list(results.values())
    codes: list[str] = []
    hard = False
    if isinstance(results, list):
        for item in results:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("invariant") or "")
            status = str(item.get("status") or "")
            if status == "hard_fail":
                hard = True
            if name:
                codes.append(name)
    status = str(row.get("status") or "")
    if status in {"blocked", "rejected", "vetoed"}:
        hard = True
    return {"hard_fail": hard, "codes": codes}


class MissionLedgerIngestor:
    def __init__(self, *, runtime_dir: Path | None = None, tenant_id: str | None = None):
        from src.ugr.mission.mission_ledger import MissionLedger

        self._ledger = MissionLedger(runtime_dir=runtime_dir, tenant_id=tenant_id)

    def ingest(self, mission_id: str, *, start_sequence: int = 0) -> list[dict[str, Any]]:
        rows = self._ledger.list_for_mission(mission_id)
        events: list[dict[str, Any]] = []
        seq = start_sequence
        for row in rows:
            ts = str(row.get("timestamp") or row.get("stamped_at") or _utc_now_iso())
            if isinstance(row.get("stamped_at"), (int, float)):
                ts = datetime.fromtimestamp(float(row["stamped_at"]), tz=timezone.utc).isoformat()
            emitter = resolve_emitter("ledger_transition")
            law = {
                "law_id": str(row.get("law_id") or "urg.cloud_forge"),
                "law_version": str(row.get("law_version") or ""),
                "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                "invariant_version": str(row.get("invariant_version") or CLOUD_INVARIANT_SET_VERSION),
            }
            boundary = {
                "boundary_digest": str(row.get("boundary_digest") or ""),
                "tenant_id": str(row.get("tenant_id") or self._ledger.tenant_id),
                "cloud_identity_hash": str(row.get("cloud_identity_hash") or ""),
            }
            events.append(
                {
                    "event_id": new_event_id("ledger_transition", mission_id, seq),
                    "subject_type": "mission",
                    "subject_id": mission_id,
                    "timestamp_utc": ts,
                    "sequence": seq,
                    "kind": "ledger_transition",
                    "summary": str(row.get("summary") or row.get("type") or row.get("action_id") or "ledger row"),
                    "emitter": emitter,
                    "law_context": law,
                    "boundary": boundary,
                    "causal_parents": [],
                    "payload_ref": {
                        "store": "mission_ledger",
                        "path": str(self._ledger.path),
                        "hash": payload_hash(row),
                    },
                    "invariant_flags": _extract_invariant_flags(row),
                }
            )
            seq += 1
        return events


class ReceiptIngestor:
    def __init__(self, *, runtime_dir: Path | None = None, tenant_id: str | None = None):
        from src.ugr.mission.mission_receipt_store import MissionReceiptStore

        self._store = MissionReceiptStore(runtime_dir=runtime_dir, tenant_id=tenant_id)

    def ingest(self, mission_id: str, *, start_sequence: int = 0) -> list[dict[str, Any]]:
        record = self._store.get_receipt(mission_id, tenant_id=self._store.tenant_id)
        if not record:
            return []
        schema = dict(record.get("mission_receipt_schema") or {})
        if not schema:
            return []
        issued = schema.get("issued_at")
        if isinstance(issued, (int, float)):
            ts = datetime.fromtimestamp(float(issued), tz=timezone.utc).isoformat()
        else:
            ts = _utc_now_iso()
        seq = start_sequence
        emitter = resolve_emitter("mission_receipt")
        return [
            {
                "event_id": new_event_id("mission_receipt", mission_id, seq),
                "subject_type": "mission",
                "subject_id": mission_id,
                "timestamp_utc": ts,
                "sequence": seq,
                "kind": "mission_receipt",
                "summary": f"MissionReceipt outcome={schema.get('outcome')}",
                "emitter": emitter,
                "law_context": _law_from_receipt_schema(schema),
                "boundary": _boundary_from_receipt(schema),
                "causal_parents": [],
                "payload_ref": {
                    "store": "urg_receipts",
                    "path": str(self._store.path),
                    "hash": payload_hash(schema),
                },
                "receipt_ref": {
                    "mission_id": mission_id,
                    "ledger_root": str(schema.get("ledger_root") or ""),
                    "receipt_sig": str(schema.get("receipt_sig") or ""),
                },
            }
        ]


class UgrTraceIngestor:
    def ingest_trace(self, trace: dict[str, Any], *, subject_id: str, start_sequence: int = 0) -> list[dict[str, Any]]:
        tid = str(trace.get("trace_id") or subject_id)
        ts = str(trace.get("timestamp") or trace.get("created_at") or _utc_now_iso())
        rail = dict(trace.get("rail_decision") or {})
        emitter = resolve_emitter("deliberation")
        law = {
            "law_id": "urg.cloud_forge",
            "law_version": str((trace.get("cloud_forge") or {}).get("law_version") or ""),
            "contract_version": PROJECT_INFI_CONTRACT_VERSION,
            "invariant_version": CLOUD_INVARIANT_SET_VERSION,
        }
        boundary = {
            "boundary_digest": "",
            "tenant_id": str(trace.get("tenant_id") or "default"),
            "cloud_identity_hash": "",
        }
        return [
            {
                "event_id": new_event_id("deliberation", tid, start_sequence),
                "subject_type": "ugr_trace",
                "subject_id": tid,
                "timestamp_utc": ts,
                "sequence": start_sequence,
                "kind": "deliberation",
                "summary": f"UGR deliberation status={trace.get('status')} rail={rail.get('rail')}",
                "emitter": emitter,
                "law_context": law,
                "boundary": boundary,
                "causal_parents": [],
                "payload_ref": {
                    "store": "ugr_traces",
                    "path": "ugr/traces.jsonl",
                    "hash": payload_hash(trace),
                },
            }
        ]

    def ingest_for_mission(self, mission_id: str, *, start_sequence: int = 0) -> list[dict[str, Any]]:
        from src.ugr.operator_console.trace_viewer import load_deliberation_traces

        payload = load_deliberation_traces(limit=200)
        events: list[dict[str, Any]] = []
        seq = start_sequence
        for trace in payload.get("traces") or []:
            if str(trace.get("mission_id") or "") not in {"", mission_id}:
                if str(trace.get("mission_id") or "") != mission_id:
                    continue
            events.extend(self.ingest_trace(trace, subject_id=str(trace.get("trace_id") or mission_id), start_sequence=seq))
            seq += 1
        return events


class LineageIngestor:
    def ingest(self, mission_id: str, *, start_sequence: int = 0) -> list[dict[str, Any]]:
        from src.ul_lineage import build_graph

        graph = build_graph(mission_id)
        events: list[dict[str, Any]] = []
        seq = start_sequence
        for node in graph.get("nodes") or []:
            if not isinstance(node, dict):
                continue
            law_enf = dict(node.get("law_enforcement") or {})
            emitter = resolve_emitter("lineage_node", module=str(node.get("source_module") or ""))
            law = {
                "law_id": "project_infi_law",
                "law_version": str(law_enf.get("contract_version") or ""),
                "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                "invariant_version": CLOUD_INVARIANT_SET_VERSION,
            }
            events.append(
                {
                    "event_id": new_event_id("lineage_node", mission_id, seq),
                    "subject_type": "mission",
                    "subject_id": mission_id,
                    "timestamp_utc": str(node.get("timestamp_utc") or _utc_now_iso()),
                    "sequence": seq,
                    "kind": "lineage_node",
                    "summary": f"Lineage {node.get('node_type')} @ {node.get('cisiv_stage')}",
                    "emitter": emitter,
                    "law_context": law,
                    "boundary": {"tenant_id": "", "boundary_digest": "", "cloud_identity_hash": ""},
                    "causal_parents": [],
                    "payload_ref": {
                        "store": "ul_lineage",
                        "path": f"lineage/{mission_id}/ul_lineage_graph.v1.json",
                        "hash": str(node.get("payload_hash") or payload_hash(node)),
                    },
                }
            )
            seq += 1
        return events


class RunLedgerIngestor:
    def ingest_run(self, run_id: str, *, start_sequence: int = 0) -> list[dict[str, Any]]:
        from src.run_ledger import RunLedger

        ledger = RunLedger()
        run = ledger.get_run(run_id)
        if not run:
            return []
        events: list[dict[str, Any]] = []
        seq = start_sequence
        for step in run.get("steps") or []:
            if not isinstance(step, dict):
                continue
            emitter = resolve_emitter("jarvis_run_step")
            events.append(
                {
                    "event_id": new_event_id("jarvis_run_step", run_id, seq),
                    "subject_type": "jarvis_run",
                    "subject_id": run_id,
                    "timestamp_utc": str(step.get("timestamp") or run.get("updated_at") or _utc_now_iso()),
                    "sequence": seq,
                    "kind": "jarvis_run_step",
                    "summary": str(step.get("summary") or step.get("name") or "run step"),
                    "emitter": emitter,
                    "law_context": {
                        "law_id": "project_infi_law",
                        "law_version": "",
                        "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                        "invariant_version": CLOUD_INVARIANT_SET_VERSION,
                    },
                    "boundary": {"tenant_id": "", "boundary_digest": "", "cloud_identity_hash": ""},
                    "causal_parents": [],
                    "payload_ref": {
                        "store": "run_ledger",
                        "path": "run-ledger.json",
                        "hash": payload_hash(step),
                    },
                }
            )
            seq += 1
        return events


class WorkflowLawIngestor:
    def ingest_run(self, workflow_run: dict[str, Any], *, start_sequence: int = 0) -> list[dict[str, Any]]:
        run_id = str(workflow_run.get("id") or "")
        law_log = workflow_run.get("law_event_log") or []
        if not isinstance(law_log, list):
            return []
        events: list[dict[str, Any]] = []
        seq = start_sequence
        enforcement = dict(workflow_run.get("law_enforcement") or {})
        for entry in law_log:
            if not isinstance(entry, dict):
                continue
            ts = str(entry.get("timestamp") or workflow_run.get("updated_at") or _utc_now_iso())
            emitter = resolve_emitter("law_event")
            events.append(
                {
                    "event_id": new_event_id("law_event", run_id, seq),
                    "subject_type": "workflow_run",
                    "subject_id": run_id,
                    "timestamp_utc": ts,
                    "sequence": seq,
                    "kind": "law_event",
                    "summary": str(entry.get("summary") or entry.get("action_id") or "law event"),
                    "emitter": emitter,
                    "law_context": {
                        "law_id": "project_infi_law",
                        "law_version": str(enforcement.get("contract_version") or ""),
                        "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                        "invariant_version": CLOUD_INVARIANT_SET_VERSION,
                    },
                    "boundary": {"tenant_id": "", "boundary_digest": "", "cloud_identity_hash": ""},
                    "causal_parents": [],
                    "payload_ref": {
                        "store": "workflow_run",
                        "path": run_id,
                        "hash": payload_hash(entry),
                    },
                }
            )
            seq += 1
        return events


class SlingshotIngestor:
    def ingest_case(self, case_id: str, *, start_sequence: int = 0) -> list[dict[str, Any]]:
        try:
            from slingshot.common import DEFAULT_SLINGSHOT_ROOT, receipts_dir
        except ImportError:
            return []
        root = DEFAULT_SLINGSHOT_ROOT
        receipt_dir = receipts_dir(case_id, runtime_root=root)
        if not receipt_dir.is_dir():
            return []
        events: list[dict[str, Any]] = []
        seq = start_sequence
        for path in sorted(receipt_dir.glob("*.json")):
            try:
                receipt = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            emitter = resolve_emitter("slingshot_receipt")
            events.append(
                {
                    "event_id": new_event_id("slingshot_receipt", case_id, seq),
                    "subject_type": "slingshot_case",
                    "subject_id": case_id,
                    "timestamp_utc": _utc_now_iso(),
                    "sequence": seq,
                    "kind": "slingshot_receipt",
                    "summary": f"Slingshot impact status={receipt.get('impact_status')}",
                    "emitter": emitter,
                    "law_context": {
                        "law_id": "slingshot",
                        "law_version": str(receipt.get("receipt_version") or ""),
                        "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                        "invariant_version": CLOUD_INVARIANT_SET_VERSION,
                    },
                    "boundary": {"tenant_id": "", "boundary_digest": "", "cloud_identity_hash": ""},
                    "causal_parents": [],
                    "payload_ref": {
                        "store": "slingshot",
                        "path": str(path),
                        "hash": str(receipt.get("receipt_hash") or payload_hash(receipt)),
                    },
                }
            )
            seq += 1
        return events


def _make_event(
    *,
    kind: str,
    subject_type: str,
    subject_id: str,
    seq: int,
    summary: str,
    timestamp_utc: str | None = None,
    payload: Any = None,
    invariant_flags: dict[str, Any] | None = None,
    module: str | None = None,
) -> dict[str, Any]:
    emitter = resolve_emitter(kind, module=module)
    flags = invariant_flags or {}
    return {
        "event_id": new_event_id(kind, subject_id, seq),
        "subject_type": subject_type,
        "subject_id": subject_id,
        "timestamp_utc": timestamp_utc or _utc_now_iso(),
        "sequence": seq,
        "kind": kind,
        "summary": summary,
        "emitter": emitter,
        "law_context": {
            "law_id": "project_infi_law",
            "law_version": "",
            "contract_version": PROJECT_INFI_CONTRACT_VERSION,
            "invariant_version": CLOUD_INVARIANT_SET_VERSION,
        },
        "boundary": {"tenant_id": "", "boundary_digest": "", "cloud_identity_hash": ""},
        "causal_parents": [],
        "payload_ref": {
            "store": "session_metadata",
            "path": subject_id,
            "hash": payload_hash(payload if payload is not None else summary),
        },
        "invariant_flags": flags,
    }


class SessionCognitiveIngestor:
    """Ingest Jarvis session cognitive trace: response steps, OTEM, Nova, bridge."""

    def ingest(self, session_id: str, *, start_sequence: int = 0) -> list[dict[str, Any]]:
        try:
            from src.conversation_memory import conversation_memory
        except Exception:
            return []

        session = conversation_memory.get_session(session_id)
        if session is None:
            return []

        meta = dict(getattr(session, "metadata", None) or {})
        events: list[dict[str, Any]] = []
        seq = start_sequence

        trace = dict(meta.get("response_trace") or {})
        for step in trace.get("steps") or []:
            if isinstance(step, str):
                summary = step[:220]
            elif isinstance(step, dict):
                summary = str(step.get("summary") or step.get("message") or step)[:220]
            else:
                summary = str(step)[:220]
            events.append(
                _make_event(
                    kind="cognitive_step",
                    subject_type="session",
                    subject_id=session_id,
                    seq=seq,
                    summary=summary or "cognitive step",
                    module="src.api",
                )
            )
            seq += 1

        otem = dict(meta.get("otem_boundary_trace") or trace.get("otem_boundary") or {})
        if otem:
            hard = bool(otem.get("incomplete_egress_detected") or otem.get("truncation_detected"))
            events.append(
                _make_event(
                    kind="otem_gate",
                    subject_type="session",
                    subject_id=session_id,
                    seq=seq,
                    summary=(
                        f"OTEM boundary plans={otem.get('plan_step_count', 0)} "
                        f"status={otem.get('structural_completion_status', 'unknown')}"
                    ),
                    payload=otem,
                    invariant_flags={"hard_fail": hard, "codes": ["otem_boundary"] if hard else []},
                    module="src.otem_runtime",
                )
            )
            seq += 1

        nova = dict(meta.get("nova_invariant_consumer") or {})
        if nova:
            drift = bool(nova.get("drift_detected") or nova.get("hard_block"))
            events.append(
                _make_event(
                    kind="nova_coherence",
                    subject_type="session",
                    subject_id=session_id,
                    seq=seq,
                    summary=f"Nova invariant consumer claim={nova.get('claim_label', 'asserted')}",
                    payload=nova,
                    invariant_flags={"hard_fail": drift, "codes": list(nova.get("violations") or [])},
                    module="src.invariant_engine_organ",
                )
            )
            seq += 1

        coherence = dict(trace.get("coherence_protocol") or meta.get("coherence_protocol") or {})
        if coherence:
            blocked = str(trace.get("blocked_by") or "") == "coherence_fabric"
            events.append(
                _make_event(
                    kind="nova_coherence",
                    subject_type="session",
                    subject_id=session_id,
                    seq=seq,
                    summary=f"Coherence fabric lane={coherence.get('lane', 'unknown')}",
                    payload=coherence,
                    invariant_flags={"hard_fail": blocked, "codes": ["coherence_fabric"] if blocked else []},
                    module="src.operator_cognition_coherence_fabric",
                )
            )
            seq += 1

        bridge = dict(meta.get("cognitive_bridge") or {})
        if bridge:
            blocked = str(bridge.get("decision") or bridge.get("status") or "").lower() in {
                "block",
                "blocked",
            }
            events.append(
                _make_event(
                    kind="cognitive_step",
                    subject_type="session",
                    subject_id=session_id,
                    seq=seq,
                    summary=f"Cognitive bridge decision={bridge.get('decision') or bridge.get('status')}",
                    payload=bridge,
                    invariant_flags={"hard_fail": blocked, "codes": ["cognitive_bridge"] if blocked else []},
                    module="src.cognitive_bridge",
                )
            )
            seq += 1

        pipeline = dict(trace.get("governed_pipeline") or {})
        intent_note = pipeline.get("intent_agency_note") or trace.get("intent_agency_note")
        if intent_note:
            events.append(
                _make_event(
                    kind="intent_agency",
                    subject_type="session",
                    subject_id=session_id,
                    seq=seq,
                    summary=str(intent_note)[:220],
                    module="src.intent_agency_organ",
                )
            )
            seq += 1

        slingshot = dict(meta.get("slingshot") or {})
        if slingshot.get("active") or slingshot.get("case_id"):
            events.append(
                _make_event(
                    kind="slingshot_receipt",
                    subject_type="session",
                    subject_id=session_id,
                    seq=seq,
                    summary=f"Slingshot case={slingshot.get('case_id')} status={slingshot.get('status')}",
                    payload=slingshot,
                    module="slingshot.impact",
                )
            )
            seq += 1

        return events


class PlatformJobIngestor:
    """Ingest platform job lifecycle from store audit rows when available."""

    def ingest(self, job_id: str, *, org_id: str = "default-org", start_sequence: int = 0) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        seq = start_sequence
        try:
            from platform.store import PlatformStore
            from pathlib import Path
            import os

            root = Path(os.getenv("AAIS_RUNTIME_DIR", ".runtime")).expanduser()
            store = PlatformStore(root / "platform")
            job = store.get_job(job_id)
            if job:
                events.append(
                    _make_event(
                        kind="platform_job",
                        subject_type="platform_job",
                        subject_id=job_id,
                        seq=seq,
                        summary=f"Job {job.get('subsystem')}.{job.get('kind')} status={job.get('status')}",
                        payload=job,
                        module="platform.jobs.registry",
                    )
                )
                seq += 1
                for rel in job.get("related_jobs") or []:
                    if not isinstance(rel, dict):
                        continue
                    events.append(
                        _make_event(
                            kind="platform_job",
                            subject_type="platform_job",
                            subject_id=job_id,
                            seq=seq,
                            summary=f"Related {rel.get('relationship')} -> {rel.get('job_id')}",
                            payload=rel,
                            module="platform.jobs.registry",
                        )
                    )
                    seq += 1
        except Exception:
            pass
        return events


class CapabilityAuditIngestor:
    def ingest_session(self, session_id: str, *, start_sequence: int = 0) -> list[dict[str, Any]]:
        path = bridge_audit_path(session_id)
        if not path.is_file():
            return []
        events: list[dict[str, Any]] = []
        seq = start_sequence
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                emitter = resolve_emitter("capability_audit")
                events.append(
                    {
                        "event_id": new_event_id("capability_audit", session_id, seq),
                        "subject_type": "session",
                        "subject_id": session_id,
                        "timestamp_utc": str(row.get("timestamp") or _utc_now_iso()),
                        "sequence": seq,
                        "kind": "capability_audit",
                        "summary": f"Capability {row.get('capability_id')} ok={row.get('ok')}",
                        "emitter": emitter,
                        "law_context": {
                            "law_id": "project_infi_law",
                            "law_version": "",
                            "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                            "invariant_version": CLOUD_INVARIANT_SET_VERSION,
                        },
                        "boundary": {"tenant_id": "", "boundary_digest": "", "cloud_identity_hash": ""},
                        "causal_parents": [],
                        "payload_ref": {
                            "store": "capability_audit",
                            "path": str(path),
                            "hash": payload_hash(row),
                        },
                    }
                )
                seq += 1
        return events


def ingest_subject(
    subject_type: str,
    subject_id: str,
    *,
    runtime_dir: Path | None = None,
    tenant_id: str | None = None,
    workflow_run: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Aggregate all ingestors for one replay subject."""
    root = runtime_dir or default_runtime_dir()
    events: list[dict[str, Any]] = []
    seq = 0

    if subject_type == "mission":
        events.extend(MissionLedgerIngestor(runtime_dir=root, tenant_id=tenant_id).ingest(subject_id, start_sequence=seq))
        seq = len(events)
        events.extend(ReceiptIngestor(runtime_dir=root, tenant_id=tenant_id).ingest(subject_id, start_sequence=seq))
        seq = len(events)
        graph_events = LineageIngestor().ingest(subject_id, start_sequence=seq)
        events.extend(graph_events)
        seq = len(events)
        try:
            from src.ul_lineage import build_graph

            session_id = str(build_graph(subject_id).get("session_id") or "").strip()
            if session_id:
                events.extend(SessionCognitiveIngestor().ingest(session_id, start_sequence=seq))
                seq = len(events)
                events.extend(CapabilityAuditIngestor().ingest_session(session_id, start_sequence=seq))
                seq = len(events)
        except Exception:
            pass
        events.extend(UgrTraceIngestor().ingest_for_mission(subject_id, start_sequence=seq))
    elif subject_type == "ugr_trace":
        from src.ugr.operator_console.trace_viewer import load_deliberation_traces

        payload = load_deliberation_traces(trace_id=subject_id)
        for trace in payload.get("traces") or []:
            events.extend(UgrTraceIngestor().ingest_trace(trace, subject_id=subject_id, start_sequence=len(events)))
    elif subject_type == "jarvis_run":
        events.extend(RunLedgerIngestor().ingest_run(subject_id, start_sequence=seq))
    elif subject_type == "workflow_run":
        if workflow_run:
            events.extend(WorkflowLawIngestor().ingest_run(workflow_run, start_sequence=seq))
    elif subject_type == "slingshot_case":
        events.extend(SlingshotIngestor().ingest_case(subject_id, start_sequence=seq))
    elif subject_type == "session":
        events.extend(SessionCognitiveIngestor().ingest(subject_id, start_sequence=seq))
        seq = len(events)
        events.extend(CapabilityAuditIngestor().ingest_session(subject_id, start_sequence=seq))
    elif subject_type == "platform_job":
        events.extend(PlatformJobIngestor().ingest(subject_id, start_sequence=seq))

    from src.temporal_replay.event import normalize_event, sort_events

    return sort_events([normalize_event(e) for e in events])
