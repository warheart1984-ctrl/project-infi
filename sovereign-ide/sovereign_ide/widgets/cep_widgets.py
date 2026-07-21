from __future__ import annotations

from typing import Any

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPlainTextEdit,
        QProgressBar,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
except Exception:  # pragma: no cover
    Qt = None
    QFrame = object
    QGridLayout = object
    QGroupBox = object
    QHBoxLayout = object
    QLabel = object
    QListWidget = object
    QListWidgetItem = object
    QPlainTextEdit = object
    QProgressBar = object
    QTabWidget = object
    QVBoxLayout = object
    QWidget = object

from cep import (
    AUDIT_OUT,
    CEPClient,
    CONFORMANCE_JOBS,
    DECISIONS_OUT,
    EVIDENCE_JOBS,
    LINEAGE_JOBS,
    PROMOTIONS_IN,
    REPLAY_JOBS,
)
from runtime.agent_loop import ConstitutionalAgent, SovereignEnvironment


def _ctx_value(ctx: Any, name: str, default=None):
    getter = getattr(ctx, "get", None)
    if callable(getter):
        return getter(name, default)
    return getattr(ctx, name, default)


def _text_report(title: str, payload: object) -> str:
    try:
        import json

        body = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    except Exception:
        body = str(payload)
    return f"{title}\n{body}"


def _cep_client(ctx: Any) -> CEPClient | None:
    client = _ctx_value(ctx, "cep_client")
    if client is not None:
        return client
    cep = _ctx_value(ctx, "cep")
    if cep is None:
        return None
    return CEPClient(cep)


class _ReportFrame(QFrame):
    def __init__(self, title: str, body: str):
        super().__init__()
        self.setObjectName("cepReportFrame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setWordWrap(True)
        heading.setStyleSheet("font-weight: 700;")
        text = QLabel(body)
        text.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(text)


class CEPPipelineView(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self._summary = None
        self._audit_log = None
        self._build_ui()

    def _cep(self):
        return _ctx_value(self.ctx, "cep")

    def _client(self) -> CEPClient | None:
        return _cep_client(self.ctx)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("CEP Pipeline")
        title.setWordWrap(True)
        subtitle = QLabel("Ingress -> Evidence -> Lineage -> Replay -> Conformance -> Decision")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        self._stages: list[QGroupBox] = []
        for index, (label, topic) in enumerate(
            [
                ("Ingress", PROMOTIONS_IN),
                ("Evidence", EVIDENCE_JOBS),
                ("Lineage", LINEAGE_JOBS),
                ("Replay", REPLAY_JOBS),
                ("Conformance", CONFORMANCE_JOBS),
                ("Decisions", DECISIONS_OUT),
            ]
        ):
            box = QGroupBox(label)
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(10, 10, 10, 10)
            box_layout.setSpacing(6)
            box_layout.addWidget(QLabel(f"topic: {topic}"))
            count = QLabel("count: 0")
            count.setObjectName(f"cepStageCount{index}")
            box_layout.addWidget(count)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            box_layout.addWidget(bar)
            grid.addWidget(box, index // 2, index % 2)
            self._stages.append(box)
        layout.addLayout(grid)

        self._summary = QLabel(self._summary_text())
        self._summary.setWordWrap(True)
        layout.addWidget(self._summary)

        self._audit_log = QPlainTextEdit()
        self._audit_log.setReadOnly(True)
        self._audit_log.setMinimumHeight(160)
        self._audit_log.setPlainText(self._audit_text())
        layout.addWidget(self._audit_log, 1)

    def _summary_text(self) -> str:
        cep = self._cep()
        client = self._client()
        if cep is None:
            return "CEP runtime unavailable."
        queue = getattr(cep, "queue", None)
        snapshot = queue.snapshot() if queue is not None else {}
        pending = len(getattr(cep, "pending_proposals", []))
        decisions = len(client.list_decisions()) if client is not None else len(getattr(cep, "decision_log", []))
        audit_events = len(client.list_audit_events()) if client is not None else len(getattr(getattr(cep, "governance", None), "audit_log", []))
        return f"pending_proposals={pending}\ndecisions={decisions}\naudit_events={audit_events}\nqueues={snapshot}"

    def _audit_text(self) -> str:
        cep = self._cep()
        client = self._client()
        if cep is None:
            return "CEP audit stream unavailable."
        audit_log = client.list_audit_events() if client is not None else list(getattr(cep.governance, "audit_log", []))
        lineage = list(getattr(cep, "lineage_log", []))
        decisions = client.list_decisions() if client is not None else list(getattr(cep, "decision_log", []))
        return _text_report(
            "CEP audit",
            {
                "audit_log": audit_log[-10:],
                "lineage": lineage[-10:],
                "decisions": [decision.__dict__ for decision in decisions[-10:]],
            },
        )

    def refresh(self) -> None:
        if self._summary is not None:
            self._summary.setText(self._summary_text())
        if self._audit_log is not None:
            self._audit_log.setPlainText(self._audit_text())
        cep = self._cep()
        if cep is None:
            return
        snapshot = cep.queue.snapshot()
        counts = [
            snapshot.get(PROMOTIONS_IN, 0),
            snapshot.get(EVIDENCE_JOBS, 0),
            snapshot.get(LINEAGE_JOBS, 0),
            snapshot.get(REPLAY_JOBS, 0),
            snapshot.get(CONFORMANCE_JOBS, 0),
            snapshot.get(DECISIONS_OUT, 0),
        ]
        for index, count in enumerate(counts):
            box = self._stages[index]
            count_label = box.findChild(QLabel, f"cepStageCount{index}")
            if count_label is not None:
                count_label.setText(f"count: {count}")
            bar = box.findChild(QProgressBar)
            if bar is not None:
                bar.setValue(min(100, count * 20))


class RoutingBrainView(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self._summary = None
        self._agent_list = None
        self._build_ui()

    def _environment(self) -> SovereignEnvironment | None:
        return _ctx_value(self.ctx, "agent_loop")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Routing Brain")
        title.setWordWrap(True)
        subtitle = QLabel("Agents, drift, conformance, and promotion pressure")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self._summary = QLabel(self._summary_text())
        self._summary.setWordWrap(True)
        layout.addWidget(self._summary)

        agent_list = QListWidget()
        self._agent_list = agent_list
        layout.addWidget(agent_list, 1)
        self._refresh_agent_list()

    def _summary_text(self) -> str:
        env = self._environment()
        if env is None:
            return "Routing brain unavailable."
        return f"time={env.time}\nagents={len(env.agents)}\naudit_packets={len(env.audit_stream)}\nreplay_frames={len(env.timeline)}"

    def _refresh_agent_list(self) -> None:
        if self._agent_list is None:
            return
        env = self._environment()
        self._agent_list.clear()
        if env is None:
            self._agent_list.addItem("No agent loop available")
            return
        for agent in env.agents:
            self._agent_list.addItem(
                f"{agent.id} | evidence={len(agent.evidence_buffer)} | lineage={len(agent.lineage)} | drift={agent.drift_value:.3f} | conformance={agent.conformance_status}"
            )

    def refresh(self) -> None:
        if self._summary is not None:
            self._summary.setText(self._summary_text())
        self._refresh_agent_list()


class ConstitutionEditor(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self._invariants = None
        self._constitution_text = None
        self._build_ui()

    def _environment(self) -> SovereignEnvironment | None:
        return _ctx_value(self.ctx, "agent_loop")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Constitution Editor")
        title.setWordWrap(True)
        subtitle = QLabel("Invariant list and constitutional amendment preview")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self._invariants = QListWidget()
        layout.addWidget(self._invariants, 1)

        self._constitution_text = QPlainTextEdit()
        self._constitution_text.setReadOnly(True)
        self._constitution_text.setMinimumHeight(160)
        layout.addWidget(self._constitution_text, 1)
        self.refresh()

    def refresh(self) -> None:
        env = self._environment()
        constitution = getattr(env, "global_constitution", None) if env is not None else None
        self._invariants.clear()
        if constitution is None:
            self._invariants.addItem("No constitution loaded")
            self._constitution_text.setPlainText("No constitution loaded")
            return
        for invariant in constitution.invariants:
            self._invariants.addItem(f"{invariant.invariant_id}: {invariant.description}")
        self._constitution_text.setPlainText(
            _text_report(
                "Constitution",
                {
                    "invariants": constitution.list_ids(),
                    "evidence_minimum": getattr(_ctx_value(self.ctx, "cep"), "governance", None) is not None,
                },
            )
        )


class DetailPanel(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self._tabs = None
        self._fields: dict[str, QPlainTextEdit] = {}
        self._build_ui()

    def _environment(self) -> SovereignEnvironment | None:
        return _ctx_value(self.ctx, "agent_loop")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        title = QLabel("Selected Detail")
        title.setWordWrap(True)
        layout.addWidget(title)

        tabs = QTabWidget()
        self._tabs = tabs
        for key, label in [
            ("invariant", "Invariant Detail"),
            ("promotion", "Promotion Request Detail"),
            ("replay", "Replay Job Detail"),
            ("agent", "Agent Detail"),
            ("decision", "Decision Detail"),
            ("audit", "Audit Detail"),
        ]:
            editor = QPlainTextEdit()
            editor.setReadOnly(True)
            editor.setMinimumHeight(140)
            self._fields[key] = editor
            tabs.addTab(editor, label)
        layout.addWidget(tabs, 1)
        self.refresh()

    def set_detail(self, key: str, payload: object) -> None:
        editor = self._fields.get(key)
        if editor is None:
            return
        editor.setPlainText(_text_report(key, payload))

    def refresh(self) -> None:
        env = self._environment()
        if env is None:
            for key in self._fields:
                self.set_detail(key, {"error": "agent loop unavailable"})
            return
        constitution = env.global_constitution
        agent = env.agents[0] if env.agents else None
        self.set_detail(
            "invariant",
            {
                "invariants": constitution.list_ids(),
                "time": env.time,
                "count": len(constitution.invariants),
            },
        )
        if agent is not None:
            self.set_detail(
                "agent",
                {
                    "agent_id": agent.id,
                    "evidence_count": len(agent.evidence_buffer),
                    "lineage_depth": len(agent.lineage),
                    "drift": agent.drift_value,
                    "conformance_status": agent.conformance_status,
                    "audit_packets": len(agent.audit_log),
                },
            )
        else:
            self.set_detail("agent", {"agents": 0})
        self.set_detail(
            "promotion",
            {
                "pending_proposals": len(env.cep.pending_proposals),
                "decisions": len(env.cep.decision_log),
            },
        )
        client = _cep_client(self.ctx)
        decisions = client.list_decisions() if client is not None else list(env.cep.decision_log)
        audit_events = client.list_audit_events() if client is not None else list(env.cep.governance.audit_log)
        self.set_detail(
            "decision",
            {
                "decision_count": len(decisions),
                "latest": decisions[-1].__dict__ if decisions else None,
            },
        )
        self.set_detail(
            "audit",
            {
                "audit_event_count": len(audit_events),
                "latest": audit_events[-1] if audit_events else None,
            },
        )
        self.set_detail(
            "replay",
            {
                "timeline_entries": len(env.timeline),
                "replay_store": list(env.replay_store._frames.keys()),
            },
        )
