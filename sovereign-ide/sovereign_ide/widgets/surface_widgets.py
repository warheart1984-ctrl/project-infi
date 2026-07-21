from __future__ import annotations

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QAbstractItemView,
        QProgressBar,
        QPlainTextEdit,
        QPushButton,
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
    QLineEdit = object
    QListWidget = object
    QListWidgetItem = object
    QAbstractItemView = object
    QProgressBar = object
    QPlainTextEdit = object
    QPushButton = object
    QVBoxLayout = object
    QWidget = object

from runtime.state import SurfaceDefinition, SovereignRuntimeContext


def _tone_palette(tone: str) -> tuple[str, str, str, str]:
    palettes = {
        "cyan": ("#22d3ee", "#08303a", "#0f141b", "#e6feff"),
        "violet": ("#a78bfa", "#281542", "#12161d", "#f6f0ff"),
        "emerald": ("#34d399", "#0f3427", "#10171a", "#effcf5"),
        "amber": ("#f59e0b", "#3f2a06", "#171513", "#fff8eb"),
        "rose": ("#fb7185", "#3d1621", "#171318", "#fff0f4"),
        "gold": ("#facc15", "#44320d", "#191613", "#fffbe6"),
    }
    return palettes.get(tone, palettes["cyan"])


class _BaseSurfaceWidget(QWidget):
    def __init__(self, ctx: SovereignRuntimeContext, surface: SurfaceDefinition):
        super().__init__()
        self.ctx = ctx
        self.surface = surface
        self._details = None
        self._build_shell()

    def _ctx_value(self, name: str, default=None):
        getter = getattr(self.ctx, "get", None)
        if callable(getter):
            return getter(name, default)
        return getattr(self.ctx, name, default)

    def _codex(self):
        return self._ctx_value("codex")

    def _federation(self):
        return self._ctx_value("federation")

    def _summary_lines(self) -> list[str]:
        return [
            f"surface.key={self.surface.key}",
            f"surface.route={self.surface.route}",
            f"backend={self.surface.backend}",
            f"frontend={self.surface.frontend}",
        ]

    def _build_shell(self) -> None:
        accent, frame_bg, body_bg, text_color = _tone_palette(self.surface.tone)
        self.setObjectName(f"surface-{self.surface.key}")
        self.setStyleSheet(
            f"""
            QWidget {{
                background: {frame_bg};
                color: {text_color};
                border: 1px solid {accent};
                border-radius: 18px;
            }}
            QLabel#surfaceTitle {{
                font-size: 17px;
                font-weight: 700;
                color: {text_color};
            }}
            QLabel#surfaceSubtitle {{
                color: #9aa8b6;
            }}
            QLabel#surfaceMeta {{
                color: {accent};
                font-size: 11px;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                font-weight: 700;
            }}
            QFrame#surfaceBody {{
                background: {body_bg};
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 14px;
            }}
            QPlainTextEdit {{
                background: transparent;
                border: 0;
                padding: 0;
                color: {text_color};
            }}
            QGroupBox {{
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 12px;
                margin-top: 0px;
            }}
            QProgressBar {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 7px;
                text-align: center;
                color: {text_color};
                height: 14px;
            }}
            QProgressBar::chunk {{
                border-radius: 7px;
                background: {accent};
            }}
            """
        )

    def _build_frame(self, title: str, subtitle: str) -> tuple[QVBoxLayout, QFrame]:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QVBoxLayout()
        header.setSpacing(6)
        title_label = QLabel(title)
        title_label.setObjectName("surfaceTitle")
        title_label.setWordWrap(True)
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("surfaceSubtitle")
        subtitle_label.setWordWrap(True)
        meta_label = QLabel(self.surface.focus_label)
        meta_label.setObjectName("surfaceMeta")
        meta_label.setWordWrap(True)
        header.addWidget(title_label)
        header.addWidget(subtitle_label)
        header.addWidget(meta_label)
        layout.addLayout(header)

        body = QFrame()
        body.setObjectName("surfaceBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 14, 14, 14)
        body_layout.setSpacing(10)
        layout.addWidget(body, 1)
        return body_layout, body

    def _body_text(self) -> str:
        lines = self._summary_lines()
        return "\n".join(lines)

    def refresh(self) -> None:
        if self._details is not None:
            self._details.setPlainText(self._body_text())

    def _attach_details(self, layout: QVBoxLayout, min_height: int = 0) -> None:
        details = QPlainTextEdit()
        details.setReadOnly(True)
        details.setPlainText(self._body_text())
        if min_height:
            details.setMinimumHeight(min_height)
        layout.addWidget(details, 1)
        self._details = details


class TimelineWidget(_BaseSurfaceWidget):
    def __init__(self, ctx: SovereignRuntimeContext):
        surface = ctx.surface_by_key("timeline") if hasattr(ctx, "surface_by_key") else None
        federation = getattr(ctx, "federation", None)
        self._timeline_state = {
            "replay.mode": "governed" if bool(getattr(federation, "bootstrapped", False)) else "offline",
            "continuity": "armed" if bool(getattr(federation, "bootstrapped", False)) else "pending",
        }
        super().__init__(
            ctx,
            surface or SurfaceDefinition(
                key="timeline",
                title="Temporal Replay Timeline",
                subtitle="Epoch playback",
                backend="Sovereign Ledger Explorer v2",
                frontend="TimelineCanvas, EventNodes, ContinuitySyncIndicator",
                route="GET /api/timeline?epoch=<int>",
                tone="cyan",
                focus_label="Focus timeline",
            ),
        )

    def _build_shell(self) -> None:
        super()._build_shell()
        layout, body = self._build_frame(self.surface.title, self.surface.subtitle)

        lanes = QHBoxLayout()
        lanes.setSpacing(10)
        for index, label in enumerate(["Epoch 014", "Epoch 015", "Epoch 016", "Epoch 017"]):
            lane = QGroupBox(label)
            lane_layout = QVBoxLayout(lane)
            lane_layout.setContentsMargins(10, 10, 10, 10)
            lane_layout.setSpacing(8)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(40 + index * 12)
            bar.setFormat(f"{label}  %p%")
            lane_layout.addWidget(bar)
            note = QLabel("Replay, continuity, and divergence are stable.")
            note.setWordWrap(True)
            lane_layout.addWidget(note)
            lanes.addWidget(lane)
        layout.addLayout(lanes)

        details = QFrame()
        details.setObjectName("surfaceBody")
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(14, 14, 14, 14)
        details_layout.setSpacing(8)
        for key, value in self._timeline_state.items():
            row = QLabel(f"{key}: {value}")
            row.setWordWrap(True)
            details_layout.addWidget(row)
        activity = QLabel("timeline.sync=ready for epoch playback")
        activity.setWordWrap(True)
        details_layout.addWidget(activity)
        layout.addWidget(details)
        self._attach_details(layout, min_height=72)

    def _body_text(self) -> str:
        return "\n".join(
            super()._summary_lines()
            + [f"{key}={value}" for key, value in self._timeline_state.items()]
            + ["timeline.sync=ready for epoch playback"]
        )


class ShaderWidget(_BaseSurfaceWidget):
    def __init__(self, ctx: SovereignRuntimeContext):
        surface = ctx.surface_by_key("shader") if hasattr(ctx, "surface_by_key") else None
        super().__init__(
            ctx,
            surface or SurfaceDefinition(
                key="shader",
                title="Quantum Glyph Shader Engine",
                subtitle="Harmonic visual grammar",
                backend="Harmonic Engine constants",
                frontend="DynamicPulse, RotationalHarmony, GLSL shader layer",
                route="POST /api/shader/update",
                tone="violet",
                focus_label="Focus shader",
            ),
        )

    def _build_shell(self) -> None:
        super()._build_shell()
        layout, body = self._build_frame(self.surface.title, self.surface.subtitle)

        preview_row = QHBoxLayout()
        preview_row.setSpacing(12)

        preview = QFrame()
        preview.setObjectName("surfaceBody")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(14, 14, 14, 14)
        preview_layout.setSpacing(8)
        for label, value in [
            ("Renderer", "shader-driven glyph composition"),
            ("Pulse input", "harmonic constants"),
            ("Effect", "deterministic visual loop"),
        ]:
            chip = QLabel(f"{label}: {value}")
            chip.setWordWrap(True)
            preview_layout.addWidget(chip)
        preview_row.addWidget(preview, 1)

        knobs = QGroupBox("Glyph controls")
        knobs_layout = QVBoxLayout(knobs)
        knobs_layout.setContentsMargins(12, 12, 12, 12)
        knobs_layout.setSpacing(8)
        for label, value in [("Density", "Medium"), ("Rotation", "Stable"), ("Glow", "Low")]:
            row = QLabel(f"{label}: {value}")
            row.setWordWrap(True)
            knobs_layout.addWidget(row)
        preview_row.addWidget(knobs, 1)
        layout.addLayout(preview_row)

        footer = QLabel("This surface is intentionally more visual than textual to mirror the shader lane in the docs.")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        self._attach_details(layout, min_height=56)

    def _body_text(self) -> str:
        return "\n".join(
            super()._summary_lines()
            + [
                "renderer=shader-driven glyph composition",
                "pulse.input=harmonic constants",
                "effect.status=deterministic visual loop",
            ]
        )


class MonitorWidget(_BaseSurfaceWidget):
    def __init__(self, ctx: SovereignRuntimeContext):
        surface = ctx.surface_by_key("monitor") if hasattr(ctx, "surface_by_key") else None
        codex = getattr(ctx, "codex", None)
        federation = getattr(ctx, "federation", None)
        self._monitor_state = [
            ("Codex base", getattr(codex, "base", None)),
            ("Federation", "bootstrapped" if bool(getattr(federation, "bootstrapped", False)) else "pending"),
            ("Telemetry", "summary"),
            ("Organism map", "online"),
        ]
        super().__init__(
            ctx,
            surface or SurfaceDefinition(
                key="monitor",
                title="Federated AI Organism Monitor",
                subtitle="Node vitality",
                backend="Telemetry Analyzer + AAES-OS node metrics",
                frontend="MetricsPanel, Chart.js graphs, organism map",
                route="GET /api/organism/state",
                tone="emerald",
                focus_label="Focus monitor",
            ),
        )

    def _build_shell(self) -> None:
        super()._build_shell()
        layout, body = self._build_frame(self.surface.title, self.surface.subtitle)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        for index, (label, value) in enumerate(self._monitor_state):
            box = QGroupBox()
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(12, 12, 12, 12)
            box_layout.setSpacing(6)
            heading = QLabel(label.upper())
            heading.setWordWrap(True)
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            box_layout.addWidget(heading)
            box_layout.addWidget(value_label)
            row = index // 2
            col = index % 2
            grid.addWidget(box, row, col)

        layout.addLayout(grid)

        health_row = QHBoxLayout()
        health_row.setSpacing(10)
        health_label = QLabel("Node vitality")
        health_bar = QProgressBar()
        health_bar.setRange(0, 100)
        health_bar.setValue(88)
        health_bar.setFormat("88%")
        health_row.addWidget(health_label)
        health_row.addWidget(health_bar, 1)
        layout.addLayout(health_row)

        note = QLabel("telemetry.mode=summary")
        note.setWordWrap(True)
        layout.addWidget(note)
        self._attach_details(layout, min_height=56)

    def _body_text(self) -> str:
        return "\n".join(
            super()._summary_lines()
            + [f"{label}={value}" for label, value in self._monitor_state]
            + ["telemetry.mode=summary"]
        )


class ConsensusWidget(_BaseSurfaceWidget):
    def __init__(self, ctx: SovereignRuntimeContext):
        surface = ctx.surface_by_key("consensus") if hasattr(ctx, "surface_by_key") else None
        super().__init__(
            ctx,
            surface or SurfaceDefinition(
                key="consensus",
                title="Governance Consensus Map",
                subtitle="Promotion quorum",
                backend="Promotion v2.0 Protocol",
                frontend="Radial consensus graph and filter panel",
                route="GET /api/consensus/votes",
                tone="amber",
                focus_label="Focus consensus",
            ),
        )

    def _build_shell(self) -> None:
        super()._build_shell()
        layout, body = self._build_frame(self.surface.title, self.surface.subtitle)

        quorum = QFrame()
        quorum.setObjectName("surfaceBody")
        quorum_layout = QVBoxLayout(quorum)
        quorum_layout.setContentsMargins(14, 14, 14, 14)
        quorum_layout.setSpacing(10)
        for label, value, pct in [
            ("Quorum", "Reached", 72),
            ("Votes in favor", "14", 84),
            ("Votes pending", "3", 18),
        ]:
            row = QLabel(f"{label}: {value}")
            row.setWordWrap(True)
            quorum_layout.addWidget(row)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(pct)
            quorum_layout.addWidget(bar)
        layout.addWidget(quorum)

        routes = QHBoxLayout()
        routes.setSpacing(8)
        for tag in ["Promotion v2.0", "Radial graph", "Filter panel", "Vote stream"]:
            chip = QGroupBox()
            chip_layout = QVBoxLayout(chip)
            chip_layout.setContentsMargins(10, 8, 10, 8)
            label = QLabel(tag)
            label.setWordWrap(True)
            chip_layout.addWidget(label)
            routes.addWidget(chip)
        layout.addLayout(routes)

        note = QLabel("authority.surface=consensus view")
        note.setWordWrap(True)
        layout.addWidget(note)
        self._attach_details(layout, min_height=48)

    def _body_text(self) -> str:
        return "\n".join(
            super()._summary_lines()
            + [
                "quorum.status=governed",
                "votes.flow=readonly map",
                "authority.surface=consensus view",
            ]
        )


class LedgerWidget(_BaseSurfaceWidget):
    def __init__(self, ctx: SovereignRuntimeContext):
        surface = ctx.surface_by_key("ledger") if hasattr(ctx, "surface_by_key") else None
        codex = getattr(ctx, "codex", None)
        self._ledger_rows = [
            "Proof block 031: conformance receipt",
            "Proof block 032: lineage signature",
            "Proof block 033: bootstrap summary",
        ]
        self._ledger_tail = f"conformance.families={sorted(getattr(codex, 'conformance', {}).keys())}"
        super().__init__(
            ctx,
            surface or SurfaceDefinition(
                key="ledger",
                title="Sovereign Ledger Explorer v2",
                subtitle="Immutable proof blocks",
                backend="Proof Block Generator + Ledger Controller",
                frontend="3D blockchain viewer and proof overlays",
                route="GET /api/ledger/blocks",
                tone="rose",
                focus_label="Focus ledger",
            ),
        )

    def _build_shell(self) -> None:
        super()._build_shell()
        layout, body = self._build_frame(self.surface.title, self.surface.subtitle)

        stack = QFrame()
        stack.setObjectName("surfaceBody")
        stack_layout = QVBoxLayout(stack)
        stack_layout.setContentsMargins(14, 14, 14, 14)
        stack_layout.setSpacing(8)
        for index, row_text in enumerate(self._ledger_rows, start=1):
            row = QGroupBox(f"Receipt 0{index}")
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(10, 10, 10, 10)
            row_layout.setSpacing(6)
            row_layout.addWidget(QLabel(row_text))
            row_layout.addWidget(QLabel("visible proof chain, lineage, and receipts"))
            stack_layout.addWidget(row)
        layout.addWidget(stack)

        footer = QFrame()
        footer.setObjectName("surfaceBody")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(14, 14, 14, 14)
        footer_layout.setSpacing(8)
        footer_layout.addWidget(QLabel("evidence.chain=visible"))
        footer_layout.addWidget(QLabel("proof.overlay=ready"))
        footer_layout.addWidget(QLabel(self._ledger_tail))
        layout.addWidget(footer)
        self._attach_details(layout, min_height=48)

    def _body_text(self) -> str:
        return "\n".join(
            super()._summary_lines()
            + [
                "evidence.chain=visible",
                "proof.overlay=ready",
                self._ledger_tail,
            ]
        )


class MandalaWidget(QWidget):
    def __init__(self, ctx: SovereignRuntimeContext):
        super().__init__()
        self.ctx = ctx
        self.surface = ctx.surface_by_key("mandala") if hasattr(ctx, "surface_by_key") else SurfaceDefinition(
            key="mandala",
            title="Neural Mandala Composer",
            subtitle="Resonance synthesis",
            backend="Harmonic Engine pulse data",
            frontend="WebAudio + shader-driven mandala",
            route="POST /api/audio/pulse",
            tone="gold",
            focus_label="Focus mandala",
        )
        self._build_ui()

    def _ctx_value(self, name: str, default=None):
        getter = getattr(self.ctx, "get", None)
        if callable(getter):
            return getter(name, default)
        return getattr(self.ctx, name, default)

    def _codex(self):
        return self._ctx_value("codex")

    def _federation(self):
        return self._ctx_value("federation")

    def _build_ui(self) -> None:
        accent, frame_bg, body_bg, text_color = _tone_palette(self.surface.tone)
        self.setStyleSheet(
            f"""
            QWidget {{
                background: {frame_bg};
                color: {text_color};
                border: 1px solid {accent};
                border-radius: 18px;
            }}
            QLabel#mandalaTitle {{
                font-size: 17px;
                font-weight: 700;
                color: {text_color};
            }}
            QLabel#mandalaSubtitle {{
                color: #9aa8b6;
            }}
            QLabel#mandalaMeta {{
                color: {accent};
                font-size: 11px;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                font-weight: 700;
            }}
            QGroupBox {{
                background: {body_bg};
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 12px;
            }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel(self.surface.title)
        title.setObjectName("mandalaTitle")
        title.setWordWrap(True)
        subtitle = QLabel(self.surface.subtitle)
        subtitle.setObjectName("mandalaSubtitle")
        subtitle.setWordWrap(True)
        meta = QLabel(self.surface.focus_label)
        meta.setObjectName("mandalaMeta")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(meta)

        orb = QFrame()
        orb.setObjectName("surfaceBody")
        orb_layout = QVBoxLayout(orb)
        orb_layout.setContentsMargins(14, 14, 14, 14)
        orb_layout.setSpacing(10)
        orb_layout.addWidget(QLabel("Mandala runtime summary"))
        orb_layout.addWidget(QLabel("The live canvas remains the first rich, visually centered surface."))
        orb_layout.addWidget(QLabel(f"Codex base: {getattr(self._codex(), 'base', None)}"))
        orb_layout.addWidget(QLabel(f"Federation: {'bootstrapped' if bool(getattr(self._federation(), 'bootstrapped', False)) else 'pending'}"))
        layout.addWidget(orb)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        metrics.setVerticalSpacing(12)
        tiles = [
            ("Constitution loaded", bool(getattr(self._codex(), "constitution", {}))),
            ("Spec families", ", ".join(sorted(getattr(self._codex(), "specs", {}).keys())) or "none"),
            ("Conformance families", ", ".join(sorted(getattr(self._codex(), "conformance", {}).keys())) or "none"),
            ("CAS-1", "online"),
        ]
        for index, (label, value) in enumerate(tiles):
            box = QGroupBox()
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(12, 10, 12, 10)
            box_layout.setSpacing(5)
            box_layout.addWidget(QLabel(label.upper()))
            box_layout.addWidget(QLabel(str(value)))
            metrics.addWidget(box, index // 2, index % 2)
        layout.addLayout(metrics)
        layout.addStretch(1)

    def refresh(self) -> None:
        return None


class PrimeArchitectPanel(QFrame):
    def __init__(self, ctx: SovereignRuntimeContext):
        super().__init__()
        self.ctx = ctx
        self._selection = None
        self._chain_list = None
        self._log = None
        self._summary = None
        self._report = None
        self._build_ui()

    def _ctx_value(self, name: str, default=None):
        getter = getattr(self.ctx, "get", None)
        if callable(getter):
            return getter(name, default)
        return getattr(self.ctx, name, default)

    def _architect(self):
        return self._ctx_value("architect")

    def _build_ui(self) -> None:
        accent, frame_bg, body_bg, text_color = _tone_palette("gold")
        self.setObjectName("primeArchitectPanel")
        self.setStyleSheet(
            f"""
            QFrame#primeArchitectPanel {{
                background: {frame_bg};
                color: {text_color};
                border: 1px solid {accent};
                border-radius: 18px;
            }}
            QLabel#primeArchitectTitle {{
                font-size: 17px;
                font-weight: 700;
                color: {text_color};
            }}
            QLabel#primeArchitectSubtitle {{
                color: #9aa8b6;
            }}
            QLabel#primeArchitectMeta {{
                color: {accent};
                font-size: 11px;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                font-weight: 700;
            }}
            QLineEdit {{
                background: {body_bg};
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 10px;
                padding: 8px 10px;
                color: {text_color};
            }}
            QPushButton {{
                background: #17212d;
                border: 1px solid #274056;
                border-radius: 999px;
                padding: 7px 13px;
                color: {text_color};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: #1e2a39;
                border-color: #355471;
            }}
            QPlainTextEdit {{
                background: {body_bg};
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                color: {text_color};
            }}
            QFrame#primeChainCard {{
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
            }}
            QFrame#primeChainCard[active="true"] {{
                background: rgba(250, 204, 21, 0.10);
                border: 1px solid rgba(250, 204, 21, 0.95);
            }}
            QLabel#primeChainTitle {{
                font-size: 14px;
                font-weight: 700;
                color: {text_color};
            }}
            QLabel#primeChainCountBadge {{
                color: #facc15;
                background: rgba(60, 45, 8, 0.95);
                border: 1px solid rgba(138, 106, 10, 0.95);
                border-radius: 999px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: 700;
            }}
            QLabel#primeChainReplayPill {{
                border-radius: 999px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: 700;
            }}
            QLabel#primeChainReplayPill[status="ok"] {{
                color: #9effa5;
                background: rgba(18, 53, 29, 0.95);
                border: 1px solid rgba(45, 106, 55, 0.95);
            }}
            QLabel#primeChainReplayPill[status="review"] {{
                color: #fbbf24;
                background: rgba(63, 42, 6, 0.95);
                border: 1px solid rgba(180, 103, 12, 0.95);
            }}
            QLabel#primeChainReplayPill[status="stale"] {{
                color: #cbd5e1;
                background: rgba(30, 41, 59, 0.95);
                border: 1px solid rgba(71, 85, 105, 0.95);
            }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Prime Architect Command Panel")
        title.setObjectName("primeArchitectTitle")
        title.setWordWrap(True)
        subtitle = QLabel("Directly execute the promotion, lineage, and replay commands from the live shell.")
        subtitle.setObjectName("primeArchitectSubtitle")
        subtitle.setWordWrap(True)
        meta = QLabel("Visible command layer")
        meta.setObjectName("primeArchitectMeta")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(meta)

        self._summary = QLabel(self._summary_text())
        self._summary.setWordWrap(True)
        layout.addWidget(self._summary)

        selection_row = QHBoxLayout()
        selection_row.setSpacing(8)
        selection_label = QLabel("Selection")
        selection_field = QLineEdit()
        selection_field.setPlaceholderText("selected")
        selection_field.setText("selected")
        self._selection = selection_field
        selection_row.addWidget(selection_label)
        selection_row.addWidget(selection_field, 1)
        layout.addLayout(selection_row)

        chain_label = QLabel("Chain history")
        layout.addWidget(chain_label)
        chain_list = QListWidget()
        if QAbstractItemView is not object:
            chain_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        chain_list.currentItemChanged.connect(self._on_chain_selected)
        self._chain_list = chain_list
        layout.addWidget(chain_list, 1)
        self._refresh_chain_history()

        actions = QHBoxLayout()
        actions.setSpacing(8)
        for label, handler in [
            ("Approve selected", self.approve_selected),
            ("Trace lineage", self.trace_lineage),
            ("Verify replay", self.verify_replay),
        ]:
            button = QPushButton(label)
            button.clicked.connect(handler)
            actions.addWidget(button)
        layout.addLayout(actions)

        log_label = QLabel("Command output")
        layout.addWidget(log_label)
        log = QPlainTextEdit()
        log.setReadOnly(True)
        log.setMinimumHeight(140)
        log.setPlainText(self._initial_log())
        self._log = log
        layout.addWidget(log, 1)

        report_label = QLabel("Last replay report")
        layout.addWidget(report_label)
        report = QPlainTextEdit()
        report.setReadOnly(True)
        report.setMinimumHeight(170)
        report.setPlainText(self._initial_report())
        self._report = report
        layout.addWidget(report, 1)

    def _summary_text(self) -> str:
        architect = self._architect()
        if architect is None:
            return "Prime Architect runtime unavailable."
        lines = list(getattr(architect, "summary_lines", lambda: [])())
        if not lines:
            return "Prime Architect runtime loaded."
        return "\n".join(lines)

    def _initial_log(self) -> str:
        architect = self._architect()
        if architect is None:
            return "Prime Architect runtime unavailable."
        manifest = list(getattr(architect, "command_manifest", ()))
        return "\n".join(
            [
                "prime.architect=online",
                f"commands={len(manifest)}",
                "ready=approve_selected | trace | replay",
            ]
        )

    def _initial_report(self) -> str:
        architect = self._architect()
        if architect is None:
            return "No replay report available."
        report = architect.verify_replay()
        return self._format_report("Latest replay", report)

    def _selection_value(self) -> str:
        if self._selection is None:
            return "selected"
        value = self._selection.text().strip()
        return value or "selected"

    def _selected_chain_id(self) -> str | None:
        if self._chain_list is None:
            return None
        item = self._chain_list.currentItem()
        if item is None:
            return None
        role = Qt.ItemDataRole.UserRole if Qt is not None else 0
        chain_id = item.data(role)
        if not chain_id:
            return None
        value = str(chain_id).strip()
        return value or None

    def _refresh_chain_history(self) -> None:
        if self._chain_list is None:
            return
        architect = self._architect()
        current = self._selected_chain_id()
        self._chain_list.blockSignals(True)
        self._chain_list.clear()
        if architect is None:
            self._chain_list.addItem("Prime Architect runtime unavailable")
            self._chain_list.blockSignals(False)
            return

        history = list(getattr(architect, "chain_history", lambda: [])())
        if not history:
            self._chain_list.addItem("No lineage chains yet")
            self._chain_list.blockSignals(False)
            return

        selected_row = 0
        for index, entry in enumerate(history):
            chain_id = str(entry.get("chain_id", ""))
            item = QListWidgetItem()
            role = Qt.ItemDataRole.UserRole if Qt is not None else 0
            item.setData(role, chain_id)
            self._chain_list.addItem(item)
            row_widget = self._create_chain_row_widget(entry, active=current is not None and chain_id == current)
            self._chain_list.setItemWidget(item, row_widget)
            item.setSizeHint(row_widget.sizeHint())
            if current is not None and chain_id == current:
                selected_row = index
        self._chain_list.setCurrentRow(selected_row)
        self._chain_list.blockSignals(False)
        self._sync_chain_highlight()
        self._update_inline_report_for_selection()

    def _on_chain_selected(self, current, previous) -> None:  # noqa: ANN001
        self._sync_chain_highlight()
        self._update_inline_report_for_selection()

    def _update_inline_report_for_selection(self) -> None:
        if self._report is None:
            return
        architect = self._architect()
        if architect is None:
            self._update_report("No replay report", {"error": "prime architect runtime unavailable"})
            return
        chain_id = self._selected_chain_id()
        if chain_id is None:
            report = architect.verify_replay()
            title = "Replay report [latest]"
        else:
            report = architect.verify_replay(chain_id)
            title = f"Replay report [{chain_id}]"
        self._update_report(title, report)

    def _sync_chain_highlight(self) -> None:
        if self._chain_list is None:
            return
        current = self._selected_chain_id()
        role = Qt.ItemDataRole.UserRole if Qt is not None else 0
        for index in range(self._chain_list.count()):
            item = self._chain_list.item(index)
            if item is None:
                continue
            chain_id = str(item.data(role) or "")
            widget = self._chain_list.itemWidget(item)
            if widget is None:
                continue
            widget.setProperty("active", chain_id == current)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def _status_tags_for_entry(self, entry: dict[str, object]) -> list[str]:
        tags = [str(tag) for tag in entry.get("status_tags", []) if str(tag)]
        status = str(entry.get("status", "")).strip().lower()
        if status and status not in tags:
            tags.append(status)
        if not tags:
            tags = ["stale"]
        ordered: list[str] = []
        for tag in tags:
            normalized = tag.lower()
            if normalized not in ordered:
                ordered.append(normalized)
        if "latest" in ordered and "approved" in ordered:
            return ["latest", "approved"]
        if "latest" in ordered:
            return ["latest"]
        if "approved" in ordered:
            return ["approved"]
        return ["stale"]

    def _replay_status_for_entry(self, entry: dict[str, object]) -> str:
        status = str(entry.get("status", "")).strip().lower()
        if status == "approved":
            return "replay ok"
        if status == "review":
            return "replay review"
        if status == "latest":
            return "replay ok"
        return "replay stale"

    def _replay_status_key_for_entry(self, entry: dict[str, object]) -> str:
        status = str(entry.get("status", "")).strip().lower()
        if status in {"approved", "latest"}:
            return "ok"
        if status == "review":
            return "review"
        return "stale"

    def _chip_style(self, tag: str) -> str:
        styles = {
            "latest": ("#9effa5", "#12351d", "#2d6a37"),
            "approved": ("#facc15", "#3c2d08", "#8a6a0a"),
            "review": ("#f59e0b", "#3f2a06", "#b36a0c"),
            "stale": ("#94a3b8", "#202938", "#475569"),
        }
        fg, bg, border = styles.get(tag, styles["stale"])
        return (
            "QLabel {"
            f"color: {fg};"
            f"background: {bg};"
            f"border: 1px solid {border};"
            "border-radius: 999px;"
            "padding: 3px 9px;"
            "font-size: 10px;"
            "font-weight: 700;"
            "text-transform: uppercase;"
            "}"
        )

    def _create_chip(self, tag: str) -> QLabel:
        chip = QLabel(tag)
        chip.setStyleSheet(self._chip_style(tag))
        return chip

    def _create_chain_row_widget(self, entry: dict[str, object], *, active: bool = False) -> QWidget:
        chain_id = str(entry.get("chain_id", ""))
        event_count = int(entry.get("event_count", 0))
        last_command_id = str(entry.get("last_command_id", ""))
        status_tags = self._status_tags_for_entry(entry)

        card = QFrame()
        card.setObjectName("primeChainCard")
        card.setProperty("active", active)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        title = QLabel(chain_id)
        title.setObjectName("primeChainTitle")
        title.setWordWrap(True)
        header_row.addWidget(title, 1)
        count_badge = QLabel(f"{event_count}")
        count_badge.setObjectName("primeChainCountBadge")
        count_badge.setToolTip(f"{event_count} event(s)")
        header_row.addWidget(count_badge)
        replay_pill = QLabel(self._replay_status_for_entry(entry))
        replay_pill.setObjectName("primeChainReplayPill")
        replay_pill.setProperty("status", self._replay_status_key_for_entry(entry))
        header_row.addWidget(replay_pill)
        for tag in status_tags:
            header_row.addWidget(self._create_chip(tag))
        card_layout.addLayout(header_row)

        detail = QLabel(f"{event_count} event(s)  |  last: {last_command_id}")
        detail.setWordWrap(True)
        detail.setStyleSheet("color: #9aa8b6;")
        card_layout.addWidget(detail)
        return card

    def _format_report(self, title: str, payload: object) -> str:
        try:
            import json

            body = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        except Exception:
            body = str(payload)
        return f"{title}\n{body}"

    def _append_log(self, title: str, payload: object) -> None:
        if self._log is None:
            return
        self._log.setPlainText(self._format_report(title, payload))

    def _update_report(self, title: str, payload: object) -> None:
        if self._report is None:
            return
        self._report.setPlainText(self._format_report(title, payload))

    def approve_selected(self) -> None:
        architect = self._architect()
        if architect is None:
            self._append_log("approve_selected", {"error": "prime architect runtime unavailable"})
            return
        result = architect.approve_selected(selected=self._selection_value())
        self._append_log("approve_selected", result)
        self.refresh()

    def trace_lineage(self) -> None:
        architect = self._architect()
        if architect is None:
            self._append_log("trace_lineage", {"error": "prime architect runtime unavailable"})
            return
        result = architect.trace_lineage(self._selected_chain_id())
        self._append_log("trace_lineage", result)
        self._update_report("Trace lineage", result)
        self.refresh()

    def verify_replay(self) -> None:
        architect = self._architect()
        if architect is None:
            self._append_log("verify_replay", {"error": "prime architect runtime unavailable"})
            return
        chain_target = self._selected_chain_id()
        result = architect.verify_replay(chain_target)
        self._append_log("verify_replay", result)
        target_label = chain_target or "latest"
        self._update_report(f"Replay report [{target_label}]", result)
        self.refresh()

    def refresh(self) -> None:
        if self._summary is not None:
            self._summary.setText(self._summary_text())
        self._refresh_chain_history()
