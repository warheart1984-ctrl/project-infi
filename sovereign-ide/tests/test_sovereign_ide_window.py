from __future__ import annotations

try:
    from PyQt6.QtWidgets import QApplication
except Exception:  # pragma: no cover
    QApplication = None

from sovereign_ide.app import build_runtime
from ui.shell.sovereign_ide_window import SovereignIDEWindow


def test_sovereign_ide_window_builds_canonical_panes() -> None:
    if QApplication is None:
        return

    runtime = build_runtime()
    app = QApplication.instance() or QApplication([])
    window = SovereignIDEWindow(runtime["ctx"])

    assert window._nav is not None
    assert window._stack is not None
    assert window._detail_panel is not None
    assert window._console is not None
    assert window._stack.count() == 4
    assert window.windowTitle() == "Sovereign IDE"

