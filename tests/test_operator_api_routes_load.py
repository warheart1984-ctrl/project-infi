"""Regression: operator_api_routes loads with src.api bootstrap."""

from __future__ import annotations

import importlib


def test_src_api_imports_with_operator_routes():
    api = importlib.import_module("src.api")
    rules = {rule.rule for rule in api.app.url_map.iter_rules()}
    assert "/api/operator/ledger" in rules
