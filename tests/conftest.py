"""Shared pytest isolation hooks for AAIS full-suite stability."""

from __future__ import annotations

import os
import uuid

import pytest

from tests.governance_bootstrap import (
    bootstrap_governance_harness,
    ensure_memory_board_gateway_admitted,
    reset_governance_test_group,
    _register_core_lanes,
)

_TEST_ORDER = {
    "test_phase_gate.py": 0,
    "test_module_governance.py": 1,
    "test_memory_board_enforcer.py": 2,
    "test_chat_turn_governance.py": 3,
    "test_jarvis_protocol.py": 4,
    "test_api.py": 10,
}


@pytest.fixture(scope="session")
def governance_bootstrap(tmp_path_factory):
    """Session-scoped governance bootstrap: lanes, membrane, gateway admission, synthetic token."""
    runtime_root = str(tmp_path_factory.mktemp("aais-governance-bootstrap"))
    state = bootstrap_governance_harness(runtime_root=runtime_root)
    yield state
    os.environ.pop("AAIS_TEST_ADMISSION_TOKEN", None)
    os.environ.pop("AAIS_TEST_COLD_START", None)


@pytest.fixture(scope="module")
def governance_test_group_reset(governance_bootstrap):
    """Reset governance state between test modules that mutate registries."""
    reset_governance_test_group()
    yield governance_bootstrap
    reset_governance_test_group()


@pytest.fixture(autouse=True)
def _aais_test_isolation(monkeypatch, governance_bootstrap):
    monkeypatch.setenv("AAIS_GOVERNED_PIPELINE_CACHE_SEC", "0")
    monkeypatch.setenv("AAIS_COHERENCE_FABRIC_CACHE_SEC", "0")
    monkeypatch.setenv("AAIS_GENOME_BOOT", "warn")
    monkeypatch.setenv("AAIS_TEST_COLD_START", "1")
    monkeypatch.setenv("AAIS_TEST_ADMISSION_TOKEN", governance_bootstrap.admission_token)

    from src.governed_direct_pipeline import clear_governed_pipeline_cache
    from src.otem_execution_substrate import reset_otem_execution_substrate

    clear_governed_pipeline_cache()
    reset_otem_execution_substrate(clear_persisted=True)
    _register_core_lanes()
    ensure_memory_board_gateway_admitted()
    yield
    clear_governed_pipeline_cache()
    reset_otem_execution_substrate(clear_persisted=True)


def pytest_collection_modifyitems(config, items):
    """Run governance unit tests before chat API integration tests."""
    indexed: list[tuple[int, int, object]] = []
    for position, item in enumerate(items):
        file_name = str(item.fspath.basename)
        order = _TEST_ORDER.get(file_name, 5)
        indexed.append((order, position, item))
    indexed.sort(key=lambda entry: (entry[0], entry[1]))
    items[:] = [entry[2] for entry in indexed]


def pytest_configure(config):
    if not os.environ.get("AAIS_TEST_ADMISSION_TOKEN"):
        os.environ["AAIS_TEST_ADMISSION_TOKEN"] = uuid.uuid4().hex
