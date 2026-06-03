#!/usr/bin/env python3
"""Add # Engineering: (and # Mythic:) file headers to subsystem shells flagged by naming-gate."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
ALIASES_PATH = ROOT / "governance" / "legacy_engineering_aliases.v1.json"
ENGINEERING_HEADER = re.compile(r"^#\s*Engineering:\s*.+", re.MULTILINE)
DOCSTRING_END = re.compile(
    r'^(\s*)(?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')\s*\n',
    re.MULTILINE,
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.linguistic_genome_lib import derive_engineering_class, load_aliases, resolve_linguistic_names


def looks_like_subsystem_shell(text: str) -> bool:
    return (
        "MODULE_ID" in text
        or "cisiv_stage" in text
        or ("build_" in text and "_status" in text)
    )


def gene_for_rel(rel: str, path_to_gene: dict[str, str], aliases: dict) -> str:
    if rel in path_to_gene:
        return path_to_gene[rel]
    stem = Path(rel).stem
    for candidate in (
        stem,
        f"{stem}_organ",
        stem.replace("_engine", "_organ"),
        stem.replace("_module", "_organ"),
    ):
        if candidate in aliases:
            return candidate
    return stem


def header_block(engineering: str, mythic: str) -> str:
    return f"# Mythic: {mythic}\n# Engineering: {engineering}\n"


def insert_after_docstring(content: str, block: str) -> str:
    if ENGINEERING_HEADER.search(content):
        return content
    match = DOCSTRING_END.match(content)
    if match:
        end = match.end()
        return content[:end] + block + content[end:]
    return block + content


def main() -> int:
    aliases = load_aliases(ROOT)
    path_to_gene = {
        e["legacy_path"].replace("\\", "/"): e["gene"]
        for e in json.loads(ALIASES_PATH.read_text(encoding="utf-8")).get("aliases", [])
        if e.get("legacy_path") and e.get("gene")
    }
    updated: list[str] = []
    for py in sorted(SRC.rglob("*.py")):
        rel = py.relative_to(ROOT).as_posix()
        text = py.read_text(encoding="utf-8", errors="replace")
        if not looks_like_subsystem_shell(text) or ENGINEERING_HEADER.search(text):
            continue
        gene = gene_for_rel(rel, path_to_gene, aliases)
        engineering, mythic = resolve_linguistic_names(gene, aliases)
        if not engineering:
            engineering, mythic = derive_engineering_class(gene)
        block = header_block(engineering, mythic)
        new_text = insert_after_docstring(text, block)
        if new_text != text:
            py.write_text(new_text, encoding="utf-8")
            updated.append(rel)
    print(f"[engineering-headers] updated {len(updated)} file(s)")
    for rel in updated:
        print(f"  {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
