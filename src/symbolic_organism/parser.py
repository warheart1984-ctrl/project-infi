"""Parser helpers for the symbolic organism VM."""

from __future__ import annotations

from src.symbolic_organism.vm import Expr, Symbol


def parse_program(text: str) -> Expr:
    """Parse a flat glyph program into symbols.

    This intentionally keeps v0 parsing simple. Structured execution is handled
    by the VM; this helper gives callers the `Expr` shape requested by the API.
    """

    return [Symbol(glyph) for glyph in text.strip() if not glyph.isspace()]


def format_expr(expr: Expr) -> str:
    """Render a symbolic expression back to a glyph string."""

    return "".join(symbol.glyph for symbol in expr)
