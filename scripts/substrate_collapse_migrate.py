"""One-shot substrate layout migration (Steps 1–6).

Run from repo root:
  python scripts/substrate_collapse_migrate.py
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (old_path, new_path) relative to ROOT
MOVES: list[tuple[str, str]] = [
    # Step 1
    ("nova/continuity/substrate.py", "nova/law_continuity/runtime.py"),
    # Step 2
    ("constitutional_state", "constitutional/core"),
    ("constitutional_substrate", "constitutional/runtime"),
    # Step 3
    ("src/otem_execution_substrate.py", "src/otem/execution.py"),
    ("src/otem_substrate_store.py", "src/otem/store.py"),
    ("src/otem_substrate_reconciler.py", "src/otem/reconciler.py"),
    # Step 4
    ("src/inter_substrate_diplomacy_runtime.py", "src/diplomacy/runtime.py"),
    ("src/inter_substrate_diplomacy_registry.py", "src/diplomacy/registry.py"),
    ("src/inter_substrate_diplomacy_organ.py", "src/diplomacy/organ.py"),
    # Step 5
    ("src/ul_substrate.py", "src/aais_ul/ul_runtime.py"),
    ("src/aais_ul_substrate.py", "src/aais_ul/runtime.py"),
    ("src/aais_ul_substrate_organ.py", "src/aais_ul/organ.py"),
    # Step 5 — also relocate the monolithic UL layer into the package (avoids shadowing)
    ("src/aais_ul.py", "src/aais_ul/layer.py"),
    # Step 6 — continuity organ under src/continuity for now (UGR continuity package)
    ("src/continuity_substrate_organ.py", "src/continuity/organ.py"),
]

IMPORT_REPLACEMENTS: list[tuple[str, str]] = [
    (r"\bfrom nova\.continuity\.substrate\b", "from nova.law_continuity.runtime"),
    (r"\bimport nova\.continuity\.substrate\b", "import nova.law_continuity.runtime"),
    (r"\bfrom constitutional_state\b", "from constitutional.core"),
    (r"\bimport constitutional_state\b", "import constitutional.core"),
    (r"\bfrom constitutional_substrate\b", "from constitutional.runtime"),
    (r"\bimport constitutional_substrate\b", "import constitutional.runtime"),
    (r"\bfrom src\.otem_execution_substrate\b", "from src.otem.execution"),
    (r"\bimport src\.otem_execution_substrate\b", "import src.otem.execution"),
    (r"\bfrom src\.otem_substrate_store\b", "from src.otem.store"),
    (r"\bimport src\.otem_substrate_store\b", "import src.otem.store"),
    (r"\bfrom src\.otem_substrate_reconciler\b", "from src.otem.reconciler"),
    (r"\bimport src\.otem_substrate_reconciler\b", "import src.otem.reconciler"),
    (r"\bfrom src\.inter_substrate_diplomacy_runtime\b", "from src.diplomacy.runtime"),
    (r"\bimport src\.inter_substrate_diplomacy_runtime\b", "import src.diplomacy.runtime"),
    (r"\bfrom src\.inter_substrate_diplomacy_registry\b", "from src.diplomacy.registry"),
    (r"\bimport src\.inter_substrate_diplomacy_registry\b", "import src.diplomacy.registry"),
    (r"\bfrom src\.inter_substrate_diplomacy_organ\b", "from src.diplomacy.organ"),
    (r"\bimport src\.inter_substrate_diplomacy_organ\b", "import src.diplomacy.organ"),
    (r"\bfrom src\.ul_substrate\b", "from src.aais_ul.ul_runtime"),
    (r"\bimport src\.ul_substrate\b", "import src.aais_ul.ul_runtime"),
    (r"\bfrom src\.aais_ul_substrate\b", "from src.aais_ul.runtime"),
    (r"\bimport src\.aais_ul_substrate\b", "import src.aais_ul.runtime"),
    (r"\bfrom src\.aais_ul_substrate_organ\b", "from src.aais_ul.organ"),
    (r"\bimport src\.aais_ul_substrate_organ\b", "import src.aais_ul.organ"),
    (r"\bfrom src\.continuity_substrate_organ\b", "from src.continuity.organ"),
    (r"\bimport src\.continuity_substrate_organ\b", "import src.continuity.organ"),
    # string module paths in configs / dynamic imports
    (r'"src\.otem_execution_substrate"', '"src.otem.execution"'),
    (r"'src\.otem_execution_substrate'", "'src.otem.execution'"),
    (r'"src\.otem_substrate_store"', '"src.otem.store"'),
    (r"'src\.otem_substrate_store'", "'src.otem.store'"),
    (r'"src\.inter_substrate_diplomacy_runtime"', '"src.diplomacy.runtime"'),
    (r"'src\.inter_substrate_diplomacy_runtime'", "'src.diplomacy.runtime'"),
    (r'"src\.inter_substrate_diplomacy_registry"', '"src.diplomacy.registry"'),
    (r"'src\.inter_substrate_diplomacy_registry'", "'src.diplomacy.registry'"),
    (r'"src\.inter_substrate_diplomacy_organ"', '"src.diplomacy.organ"'),
    (r"'src\.inter_substrate_diplomacy_organ'", "'src.diplomacy.organ'"),
]

SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}

INIT_PACKAGES: list[str] = [
    "constitutional",
    "constitutional/core",
    "constitutional/runtime",
    "nova/law_continuity",
    "src/otem",
    "src/diplomacy",
    "src/aais_ul",
]


def _ensure_init(path: Path) -> None:
    init = path / "__init__.py"
    if not init.exists():
        init.write_text('"""Package."""\n', encoding="utf-8")
        print(f"  created {init.relative_to(ROOT)}")


def move_path(old_rel: str, new_rel: str) -> None:
    old = ROOT / old_rel
    new = ROOT / new_rel
    if not old.exists():
        print(f"  skip missing {old_rel}")
        return
    if new.exists():
        print(f"  skip exists {new_rel}")
        return
    new.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(old), str(new))
    print(f"  moved {old_rel} -> {new_rel}")


def apply_import_replacements(content: str) -> str:
    for pattern, repl in IMPORT_REPLACEMENTS:
        content = re.sub(pattern, repl, content)
    return content


def patch_files() -> int:
    changed = 0
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix not in {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".ts", ".tsx", ".js", ".jsx"}:
            continue
        if path == Path(__file__).resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        updated = apply_import_replacements(text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed += 1
            print(f"  patched {path.relative_to(ROOT)}")
    return changed


def patch_nova_continuity_init() -> None:
    init = ROOT / "nova" / "continuity" / "__init__.py"
    if not init.exists():
        return
    text = init.read_text(encoding="utf-8")
    text = text.replace(
        "from nova.continuity.substrate import",
        "from nova.law_continuity.runtime import",
    )
    init.write_text(text, encoding="utf-8")
    print(f"  patched {init.relative_to(ROOT)}")


def main() -> None:
    print("=== substrate collapse migration ===")
    print("--- moves ---")
    for old, new in MOVES:
        move_path(old, new)
    print("--- package inits ---")
    for pkg in INIT_PACKAGES:
        _ensure_init(ROOT / pkg)
    print("--- import patches ---")
    patch_nova_continuity_init()
    n = patch_files()
    print(f"done: {n} files patched")


if __name__ == "__main__":
    main()
