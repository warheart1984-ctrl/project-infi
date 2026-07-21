from __future__ import annotations

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QApplication,
        QFrame,
        QHBoxLayout,
        QLabel,
        QGraphicsDropShadowEffect,
        QPushButton,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )
except Exception:  # pragma: no cover
    QApplication = None
    Qt = None
    QFrame = object
    QHBoxLayout = object
    QLabel = object
    QGraphicsDropShadowEffect = object
    QPushButton = object
    QSplitter = object
    QVBoxLayout = object
    QWidget = object

from runtime.state import SURFACE_DEFINITIONS, SovereignRuntimeContext
from sovereign_ide.widgets import (
    ConsensusWidget,
    LedgerWidget,
    MandalaWidget,
    MonitorWidget,
    PrimeArchitectPanel,
    ShaderWidget,
    TimelineWidget,
)


class SovereignShell(QWidget):
    def __init__(self, ctx):
        if QApplication is None:
            self.ctx = ctx
            self.visible = False
            return

        app = QApplication.instance() or QApplication([])
        self._app = app
        super().__init__()
        self.ctx = ctx
        self._splitter = None
        self._summary_label = None
        self._surface_widgets: dict[str, QWidget] = {}
        self._surface_buttons: dict[str, QPushButton] = {}
        self._surface_order: list[str] = []
        self._active_surface_key: str | None = None
        self._auxiliary_widgets: list[QWidget] = []
        self.setWindowTitle("Sovereign IDE")
        self.resize(1680, 980)
        self._build_ui()

    def _ctx_value(self, name: str, default=None):
        getter = getattr(self.ctx, "get", None)
        if callable(getter):
            return getter(name, default)
        return getattr(self.ctx, name, default)

    def _surface_definitions(self):
        surfaces = self._ctx_value("surface_definitions", SURFACE_DEFINITIONS)
        return tuple(surfaces)

    def _build_ui(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #0b0f14;
                color: #eef2f7;
                font-family: "Segoe UI", "Inter", sans-serif;
            }
            QFrame#hero {
                background: #111821;
                border: 1px solid #223042;
                border-radius: 18px;
            }
            QLabel#heroEyebrow {
                color: #8fa2b7;
                text-transform: uppercase;
                letter-spacing: 0.16em;
                font-size: 11px;
                font-weight: 700;
            }
            QLabel#heroTitle {
                font-size: 24px;
                font-weight: 800;
                line-height: 1.05;
                color: #f4f7fb;
            }
            QLabel#heroSummary {
                color: #9caec1;
                line-height: 1.5;
            }
            QPushButton {
                background: #17212d;
                border: 1px solid #274056;
                border-radius: 999px;
                padding: 7px 13px;
                color: #eaf1f8;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1e2a39;
                border-color: #355471;
            }
            QPushButton:pressed {
                background: #101722;
            }
            QPushButton[active="true"] {
                background: linear-gradient(180deg, #1f3650, #17293c);
                border-color: #5fcfd0;
                color: #f7fcff;
                box-shadow: 0 0 0 1px rgba(95, 207, 208, 0.14), 0 10px 20px rgba(5, 10, 15, 0.28);
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("hero")
        if QGraphicsDropShadowEffect is not object:
            shadow = QGraphicsDropShadowEffect(hero)
            shadow.setBlurRadius(34)
            shadow.setOffset(0, 10)
            shadow.setColor(Qt.GlobalColor.black)
            hero.setGraphicsEffect(shadow)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(20, 18, 20, 18)
        hero_layout.setSpacing(10)

        eyebrow = QLabel("Sovereign IDE")
        eyebrow.setObjectName("heroEyebrow")
        title = QLabel("Workspace shell for the six governed surfaces")
        title.setObjectName("heroTitle")
        title.setWordWrap(True)
        summary = QLabel("\n".join(self._summary_lines()))
        summary.setObjectName("heroSummary")
        summary.setWordWrap(True)
        self._summary_label = summary

        controls = self._build_control_row()
        hero_layout.addWidget(eyebrow)
        hero_layout.addWidget(title)
        hero_layout.addWidget(summary)
        hero_layout.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        self._splitter = splitter

        widget_factories = {
            "timeline": TimelineWidget,
            "shader": ShaderWidget,
            "monitor": MonitorWidget,
            "consensus": ConsensusWidget,
            "ledger": LedgerWidget,
            "mandala": MandalaWidget,
        }

        for surface in self._surface_definitions():
            widget_factory = widget_factories.get(surface.key)
            if widget_factory is None:
                continue
            widget = widget_factory(self.ctx)
            self._surface_widgets[surface.key] = widget
            self._surface_order.append(surface.key)
            splitter.addWidget(widget)

        for index in range(len(self._surface_order)):
            splitter.setStretchFactor(index, 1)

        root.addWidget(hero)
        architect_panel = PrimeArchitectPanel(self.ctx)
        self._auxiliary_widgets.append(architect_panel)
        root.addWidget(architect_panel)
        root.addWidget(splitter, 1)
        self.focus_surface("timeline")

    def _build_control_row(self):
        row = QHBoxLayout()
        row.setSpacing(5)
        for surface in self._surface_definitions():
            button = QPushButton(surface.focus_label)
            button.setProperty("active", False)
            button.clicked.connect(lambda _checked=False, key=surface.key: self.focus_surface(key))
            row.addWidget(button)
            self._surface_buttons[surface.key] = button

        sync_button = QPushButton("Sync runtime")
        sync_button.setProperty("active", False)
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
            f"surfaces={len(self._surface_order)}",
        ]

    def focus_surface(self, key: str) -> None:
        if self._splitter is None or key not in self._surface_widgets:
            return

        self._active_surface_key = key
        for surface_key, button in self._surface_buttons.items():
            button.setProperty("active", surface_key == key)
            button.style().unpolish(button)
            button.style().polish(button)

        weights = [1] * len(self._surface_order)
        index = self._surface_order.index(key)
        weights[index] = 4
        self._splitter.setSizes([weight * 180 for weight in weights])

    def sync_runtime(self) -> None:
        if self._summary_label is not None:
            self._summary_label.setText("\n".join(self._summary_lines()))
        for widget in self._surface_widgets.values():
            refresh = getattr(widget, "refresh", None)
            if callable(refresh):
                refresh()
        for widget in self._auxiliary_widgets:
            refresh = getattr(widget, "refresh", None)
            if callable(refresh):
                refresh()

    def show(self):  # type: ignore[override]
        if QApplication is None:
            self.visible = True
            print("[SovereignShell] PyQt6 unavailable; shell shown in fallback mode.")
            return None

        super().show()
        self.raise_()
        self.activateWindow()
        return self
