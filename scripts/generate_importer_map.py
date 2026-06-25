"""Generate docs/rebuild/importer_map.md from src/**/*_organ.py grep inventory."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUT = ROOT / "docs" / "rebuild" / "importer_map.md"

STATUS_ONLY_NAMES = {
    "memory_path_governance_organ.py",
    "mission_board_organ.py",
    "v8_runtime_organ.py",
    "v9_runtime_organ.py",
}


def main() -> None:
    organs = sorted(SRC.rglob("*_organ.py"))
    importers: dict[str, set[str]] = {}

    for py in SRC.rglob("*.py"):
        if py.name.endswith("_organ.py"):
            continue
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(py.relative_to(SRC)).replace("\\", "/")
        for organ in organs:
            stem = organ.stem
            mod = str(organ.relative_to(SRC)).replace("\\", "/").replace(".py", "").replace("/", ".")
            if mod in text or f"{stem}." in text or f"import {stem}" in text:
                importers.setdefault(organ.name, set()).add(rel)

    lines = [
        "# Importer map (generated)",
        "",
        "Grep-driven inventory of `*_organ.py` under `src/` tagged "
        "`{runtime | status-only | dead}`.",
        "",
        "| Organ | Tag | Importers |",
        "|---|---|---|",
    ]

    for organ in organs:
        name = organ.name
        imps = sorted(importers.get(name, []))
        if not imps:
            tag = "dead"
        elif name in STATUS_ONLY_NAMES:
            tag = "status-only"
        elif imps == ["jarvis_organ_status_routes.py"] or (
            len(imps) == 1 and imps[0] == "jarvis_organ_status_routes.py"
        ):
            tag = "status-only"
        elif "api.py" in imps or any("jarvis_operator" in i for i in imps):
            tag = "runtime"
        elif len(imps) <= 2 and all(
            i in {"jarvis_organ_status_routes.py", "api.py"} for i in imps
        ):
            tag = "status-only"
        else:
            tag = "runtime"
        imp_str = ", ".join(f"`{i}`" for i in imps[:8])
        if len(imps) > 8:
            imp_str += f" (+{len(imps) - 8} more)"
        lines.append(f"| `{name}` | {tag} | {imp_str or '(none)'} |")

    lines.append("")
    lines.append(f"**Total organs:** {len(organs)}")
    lines.append("")
    dead = [o.name for o in organs if not importers.get(o.name)]
    status_only = [
        o.name
        for o in organs
        if importers.get(o.name)
        and (
            o.name in STATUS_ONLY_NAMES
            or importers[o.name] == {"jarvis_organ_status_routes.py"}
        )
    ]
    lines.append(f"**Dead (no importers):** {len(dead)}")
    lines.append(f"**Status-only candidates:** {len(status_only)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(organs)} organs)")


if __name__ == "__main__":
    main()
