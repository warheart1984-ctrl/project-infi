#!/usr/bin/env python3
"""Deterministic mythic-to-engineering translator (Wave 6)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.linguistic_genome_lib import (  # noqa: E402
    MYTHIC_FORBIDDEN_IN_GENE,
    load_aliases,
    load_genome,
    resolve_linguistic_names,
    validate_engineering_class,
)

TERMINOLOGY_MAP = {
    "organ": "subsystem",
    "organs": "subsystems",
    "fabric": "coherence layer",
    "fabrics": "coherence layers",
    "summon wave": "release",
    "summon": "release",
    "genome": "schema",
    "surface": "interface",
    "plane": "layer",
}

ROLE_KEYWORDS = {
    "layer": "Layer",
    "fabric": "Layer",
    "coherence": "Layer",
    "bridge": "Bridge",
    "handoff": "Bridge",
    "gate": "Gate",
    "monitor": "Monitor",
    "sentinel": "Monitor",
    "interface": "Interface",
    "console": "Interface",
    "surface": "Interface",
    "lane": "Lane",
    "route": "Interface",
    "engine": "Engine",
    "manager": "Manager",
    "steward": "Manager",
}


@dataclass
class TranslationResult:
    mythic_label: str
    engineering_class: str
    module_stem: str
    gene_suggestion: str
    valid: bool
    errors: list[str] = field(default_factory=list)
    safety_net: dict[str, str] = field(default_factory=dict)
    concept_spec_snippet: str = ""
    comment_block: str = ""
    mystic_hook: str = "mystic_engine_organ (future LLM assist — not used in v1)"


def _pascal(parts: list[str]) -> str:
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def _snake(parts: list[str]) -> str:
    return "_".join(p.lower() for p in parts if p)


def _tokenize_mythic(text: str) -> list[str]:
    normalized = text.lower()
    for mythic, eng in TERMINOLOGY_MAP.items():
        normalized = normalized.replace(mythic, eng)
    tokens = re.findall(r"[a-z0-9]+", normalized)
    return tokens


def _infer_role(tokens: list[str]) -> str:
    for token in reversed(tokens):
        if token in ROLE_KEYWORDS:
            return ROLE_KEYWORDS[token]
    if "layer" in tokens or "coherence" in tokens:
        return "Layer"
    if "bridge" in tokens:
        return "Bridge"
    if "interface" in tokens or "console" in tokens:
        return "Interface"
    return "Engine"


def _engineering_from_parts(domain: str, function: str, role: str) -> str:
    return f"{domain}{function}{role}"


def _module_stem_from_class(name: str) -> str:
    stem = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return stem.lower()


def translate_mythic(
    mythic: str,
    *,
    domain: str | None = None,
    function: str | None = None,
    role: str | None = None,
    gene: str | None = None,
) -> TranslationResult:
    errors: list[str] = []
    mythic_label = mythic.strip()

    if gene:
        eng, myth = resolve_linguistic_names(gene, load_aliases())
        if eng:
            return TranslationResult(
                mythic_label=myth or mythic_label,
                engineering_class=eng,
                module_stem=_module_stem_from_class(eng),
                gene_suggestion=gene,
                valid=True,
                safety_net=_safety_net(myth or mythic_label, eng),
                concept_spec_snippet=_concept_snippet(myth or mythic_label, eng),
                comment_block=_comment_block(myth or mythic_label, eng),
            )

    if domain and function and role:
        engineering_class = _engineering_from_parts(domain, function, role)
        tokens = [_snake([domain]), _snake([function])]
    else:
        tokens = _tokenize_mythic(mythic_label)
        if not tokens:
            errors.append("mythic text empty or unparseable")
            return TranslationResult(
                mythic_label=mythic_label,
                engineering_class="",
                module_stem="",
                gene_suggestion="",
                valid=False,
                errors=errors,
            )
        role_suffix = role or _infer_role(tokens)
        stop = {"for", "the", "a", "an", "and", "of", "to", "cross", "plane"}
        content = [t for t in tokens if t not in stop and t not in ROLE_KEYWORDS]
        if len(content) > 4:
            content = content[:4]
        engineering_class = _pascal(content) + role_suffix
        tokens = content

    for forbidden in MYTHIC_FORBIDDEN_IN_GENE:
        if re.search(rf"(?<![a-z]){re.escape(forbidden)}(?![a-z])", engineering_class.lower()):
            errors.append(f"engineering_class contains mythic token: {forbidden}")
        if re.search(rf"(?<![a-z]){re.escape(forbidden)}(?![a-z])", " ".join(tokens)):
            errors.append(f"mythic tokens present in derived stem: {forbidden}")

    if not validate_engineering_class(engineering_class):
        errors.append(f"invalid engineering_class pattern: {engineering_class!r}")

    module_stem = _module_stem_from_class(engineering_class) if engineering_class else ""
    gene_suggestion = _snake(tokens) if tokens else module_stem

    return TranslationResult(
        mythic_label=mythic_label,
        engineering_class=engineering_class,
        module_stem=module_stem,
        gene_suggestion=gene_suggestion,
        valid=not errors,
        errors=errors,
        safety_net=_safety_net(mythic_label, engineering_class),
        concept_spec_snippet=_concept_snippet(mythic_label, engineering_class),
        comment_block=_comment_block(mythic_label, engineering_class),
    )


def _safety_net(mythic: str, engineering: str) -> dict[str, str]:
    return {
        "inputs": "TBD — specify governed state / operator context",
        "outputs": "TBD — specify structured result type",
        "constraints": "read-only unless explicitly scoped in concept spec",
        "failure_modes": "reject with reason code when invariants fail",
        "invariants": "TBD — minimal invariant list",
        "boundaries": "TBD — explicit non-responsibilities",
        "engineering_name": engineering,
        "mythic_name": mythic,
    }


def _concept_snippet(mythic: str, engineering: str) -> str:
    return (
        f"**Mythic:** {mythic}\n\n"
        f"**Engineering:** `{engineering}` (`<Domain><Function><Role>`) — "
        f"literal deterministic behavior TBD in concept spec.\n"
    )


def _comment_block(mythic: str, engineering: str) -> str:
    return (
        f"# Mythic: {mythic}\n"
        f"# Engineering: {engineering}\n"
        f"# Responsibilities: TBD\n"
        f"# Non-responsibilities: TBD\n"
        f"# Invariants: TBD\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Mythic-to-engineering translator")
    parser.add_argument("--mythic", help="Mythic seed text")
    parser.add_argument("--domain", help="Domain PascalCase fragment")
    parser.add_argument("--function", help="Function PascalCase fragment")
    parser.add_argument("--role", help="Role suffix e.g. Layer, Engine, Manager")
    parser.add_argument("--gene", help="Existing gene — merge from alias registry")
    parser.add_argument("--format", choices=["json", "markdown", "comments"], default="json")
    args = parser.parse_args()

    if not args.mythic and not args.gene and not (args.domain and args.function and args.role):
        parser.error("provide --mythic, --gene, or --domain/--function/--role")

    result = translate_mythic(
        args.mythic or "",
        domain=args.domain,
        function=args.function,
        role=args.role,
        gene=args.gene,
    )

    if args.format == "json":
        print(json.dumps(asdict(result), indent=2))
    elif args.format == "markdown":
        print(result.concept_spec_snippet)
    else:
        print(result.comment_block)

    return 0 if result.valid else 1


if __name__ == "__main__":
    sys.exit(main())
