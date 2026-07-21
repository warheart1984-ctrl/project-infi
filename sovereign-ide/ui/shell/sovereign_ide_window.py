from __future__ import annotations

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QApplication,
        QDockWidget,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QPushButton,
        QSplitter,
        QStackedWidget,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except Exception:  # pragma: no cover
    QApplication = None
    Qt = None
    QDockWidget = object
    QFrame = object
    QHBoxLayout = object
    QLabel = object
    QMainWindow = object
    QPushButton = object
    QSplitter = object
    QStackedWidget = object
    QTextEdit = object
    QTreeWidget = object
    QTreeWidgetItem = object
    QVBoxLayout = object
    QWidget = object

from sovereign_ide.widgets import CEPPipelineView, ConstitutionEditor, DetailPanel, RoutingBrainView, TimelineWidget, PrimeArchitectPanel


class SovereignIDEWindow(QMainWindow):
    def __init__(self, ctx):
        if QApplication is None:
            self.ctx = ctx
            self.visible = False
            return

        app = QApplication.instance() or QApplication([])
        self._app = app
        super().__init__()
        self.ctx = ctx
        self._stack = None
        self._nav = None
        self._detail_panel = None
        self._console = None
        self._summary_label = None
        self._pages: dict[str, QWidget] = {}
        self.setWindowTitle("Sovereign IDE")
        self.resize(1760, 1080)
        self._build_ui()

    def _ctx_value(self, name: str, default=None):
        getter = getattr(self.ctx, "get", None)
        if callable(getter):
            return getter(name, default)
        return getattr(self.ctx, name, default)

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        header = QFrame()
        header.setObjectName("sovereignHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(18, 16, 18, 16)
        header_layout.setSpacing(8)
        eyebrow = QLabel("Sovereign IDE")
        eyebrow.setObjectName("sovereignEyebrow")
        title = QLabel("Constitutional multi-agent workspace with CEP, routing, and replay")
        title.setObjectName("sovereignTitle")
        title.setWordWrap(True)
        self._summary_label = QLabel("\n".join(self._summary_lines()))
        self._summary_label.setObjectName("sovereignSummary")
        self._summary_label.setWordWrap(True)
        controls = self._build_controls()
        header_layout.addWidget(eyebrow)
        header_layout.addWidget(title)
        header_layout.addWidget(self._summary_label)
        header_layout.addLayout(controls)
        root_layout.addWidget(header)

        stack = QStackedWidget()
        self._stack = stack
        timeline_page = TimelineWidget(self.ctx)
        routing_page = RoutingBrainView(self.ctx)
        cep_page = CEPPipelineView(self.ctx)
        constitution_page = QWidget()
        constitution_layout = QVBoxLayout(constitution_page)
        constitution_layout.setContentsMargins(0, 0, 0, 0)
        constitution_layout.setSpacing(12)
        constitution_editor = ConstitutionEditor(self.ctx)
        architect_panel = PrimeArchitectPanel(self.ctx)
        constitution_layout.addWidget(constitution_editor, 1)
        constitution_layout.addWidget(architect_panel, 1)
        constitution_page.refresh = lambda: (constitution_editor.refresh(), architect_panel.refresh())  # type: ignore[attr-defined]

        self._pages = {
            "timeline": timeline_page,
            "routing": routing_page,
            "cep": cep_page,
            "constitution": constitution_page,
        }
        for page in self._pages.values():
            stack.addWidget(page)
        root_layout.addWidget(stack, 1)
        self.setCentralWidget(root)

        nav = QTreeWidget()
        nav.setHeaderHidden(True)
        self._nav = nav
        self._populate_nav()
        nav.itemClicked.connect(self._on_nav_clicked)
        nav_dock = QDockWidget("Navigation", self)
        nav_dock.setWidget(nav)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, nav_dock)

        detail_panel = DetailPanel(self.ctx)
        self._detail_panel = detail_panel
        detail_dock = QDockWidget("Details", self)
        detail_dock.setWidget(detail_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, detail_dock)

        console = QTextEdit()
        console.setReadOnly(True)
        self._console = console
        console_dock = QDockWidget("Console", self)
        console_dock.setWidget(console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, console_dock)

        self._select_page("timeline")
        self.sync_runtime()

    def _build_controls(self):
        row = QHBoxLayout()
        row.setSpacing(8)
        for label, page_key in [
            ("Timeline Mode", "timeline"),
            ("Graph Mode", "routing"),
            ("CEP Pipeline", "cep"),
            ("Constitution Editor", "constitution"),
        ]:
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, key=page_key: self._select_page(key))
            row.addWidget(button)
        step_button = QPushButton("Advance loop")
        step_button.clicked.connect(self.advance_loop)
        row.addWidget(step_button)
        sync_button = QPushButton("Sync runtime")
        sync_button.clicked.connect(self.sync_runtime)
        row.addWidget(sync_button)
        row.addStretch(1)
        return row

    def _summary_lines(self) -> list[str]:
        if hasattr(self.ctx, "summary_lines"):
            return list(self.ctx.summary_lines())
        codex = self._ctx_value("codex")
        federation = self._ctx_value("federation")
        return [
            f"codex.base={getattr(codex, 'base', None)}",
            f"codex.constitution_loaded={bool(getattr(codex, 'constitution', {}))}",
            f"federation.bootstrapped={getattr(federation, 'bootstrapped', False)}",
        ]

    def _populate_nav(self) -> None:
        if self._nav is None:
            return
        structure = {
            "Constitutional Spine": ["Constitution", "Invariants", "Evidence Layer", "Lineage Layer", "Drift Gates", "Conformance Suites"],
            "CEP": ["Promotion Requests", "Replay Jobs", "Conformance Jobs", "Decisions Ledger", "CEP Audit Stream"],
            "Sovereign Layer": ["Sovereigns", "Agents", "Routing Brain", "Audit Surfaces", "Treasury"],
            "Temporal Layer": ["Timelines", "Replay Windows", "Temporal Promotion"],
            "Cosmology Layer": ["Singularity Field", "Multiversal Registry", "Fractal Constitution"],
        }
        for root_label, children in structure.items():
            root_item = QTreeWidgetItem([root_label])
            for child in children:
                root_item.addChild(QTreeWidgetItem([child]))
            self._nav.addTopLevelItem(root_item)
        self._nav.expandAll()

    def _page_for_label(self, label: str) -> str:
        if label in {"Constitution", "Invariants", "Evidence Layer", "Lineage Layer", "Drift Gates", "Conformance Suites", "Cosmology Layer", "Singularity Field", "Multiversal Registry", "Fractal Constitution"}:
            return "constitution"
        if label in {"Promotion Requests", "Replay Jobs", "Conformance Jobs", "Decisions Ledger", "CEP Audit Stream", "CEP"}:
            return "cep"
        if label in {"Sovereigns", "Agents", "Routing Brain", "Audit Surfaces", "Treasury"}:
            return "routing"
        return "timeline"

    def _select_page(self, key: str) -> None:
        if self._stack is None or key not in self._pages:
            return
        self._stack.setCurrentWidget(self._pages[key])
        if self._detail_panel is not None:
            self._detail_panel.refresh()

    def _on_nav_clicked(self, item, _column) -> None:  # noqa: ANN001
        if item is None:
            return
        self._select_page(self._page_for_label(item.text(0)))
        if self._detail_panel is not None:
            self._detail_panel.refresh()

    def sync_runtime(self) -> None:
        if self._summary_label is not None:
            self._summary_label.setText("\n".join(self._summary_lines()))
        for widget in self._pages.values():
            refresh = getattr(widget, "refresh", None)
            if callable(refresh):
                refresh()
        if self._detail_panel is not None:
            self._detail_panel.refresh()
        if self._console is not None:
            lines = list(self._summary_lines())
            cep = self._ctx_value("cep")
            agent_loop = self._ctx_value("agent_loop")
        if cep is not None:
            lines.append(f"cep.pending_proposals={len(getattr(cep, 'pending_proposals', []))}")
            lines.append(f"cep.decisions={len(getattr(cep, 'decision_log', []))}")
        cep_client = self._ctx_value("cep_client")
        temporal_api = self._ctx_value("temporal_api")
        if cep_client is not None:
            lines.append(f"cep.client_loaded={True}")
        if temporal_api is not None:
            lines.append(f"temporal.replay_store={len(getattr(getattr(temporal_api, 'replay_store', None), '_frames', {}))}")
        if agent_loop is not None:
            lines.append(f"agents={len(getattr(agent_loop, 'agents', []))}")
            lines.append(f"time={getattr(agent_loop, 'time', 0)}")
            self._console.setPlainText("\n".join(lines))

    def advance_loop(self) -> None:
        agent_loop = self._ctx_value("agent_loop")
        if agent_loop is None:
            return
        agent_loop.step()
        self.sync_runtime()

    def show(self):  # type: ignore[override]
        if QApplication is None:
            self.visible = True
            print("[SovereignIDEWindow] PyQt6 unavailable; shell shown in fallback mode.")
            return None
        super().show()
        self.raise_()
        self.activateWindow()
        return self
