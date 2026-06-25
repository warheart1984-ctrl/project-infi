"""Shared pytest fixtures for AAIS test isolation."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _constitutional_boot_test_mode():
    """Tests skip fail-closed constitutional boot unless explicitly enabled."""
    prior = os.environ.get("CONSTITUTIONAL_BOOT_SKIP")
    os.environ["CONSTITUTIONAL_BOOT_SKIP"] = "1"
    yield
    if prior is None:
        os.environ.pop("CONSTITUTIONAL_BOOT_SKIP", None)
    else:
        os.environ["CONSTITUTIONAL_BOOT_SKIP"] = prior


@pytest.fixture(autouse=True)
def _reset_constitutional_boot_flag():
    import importlib

    gg = importlib.import_module("constitutional.runtime.governance_gate")

    prior = gg._BOOT_COMPLETED
    gg._BOOT_COMPLETED = False
    yield
    gg._BOOT_COMPLETED = prior


@pytest.fixture(scope="session", autouse=True)
def _genome_boot_warn_for_fastapi():
    """FastAPI lifespan uses strict genome boot by default; warn for test sessions."""
    prior = os.environ.get("AAIS_GENOME_BOOT")
    os.environ["AAIS_GENOME_BOOT"] = "warn"
    yield
    if prior is None:
        os.environ.pop("AAIS_GENOME_BOOT", None)
    else:
        os.environ["AAIS_GENOME_BOOT"] = prior


@pytest.fixture(autouse=True)
def _reset_otem_execution_substrate_singleton():
    from src.otem.execution import reset_otem_execution_substrate

    reset_otem_execution_substrate()
    yield
    reset_otem_execution_substrate()
