#!/usr/bin/env python3
"""Tests for mythic_engineering_translator (Wave 6)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mythic_engineering_translator import translate_mythic


def test_coherence_fabric_mythic():
    r = translate_mythic("Coherence fabric for cross-plane alignment")
    assert r.valid
    assert r.engineering_class.endswith("Layer")
    assert "Coherence" in r.engineering_class or "coherence" in r.mythic_label.lower()


def test_runtime_plane_steward():
    r = translate_mythic(
        "Runtime plane steward",
        domain="Runtime",
        function="Plane",
        role="Manager",
    )
    assert r.valid
    assert r.engineering_class == "RuntimePlaneManager"


def test_gene_registry_merge():
    r = translate_mythic("", gene="operator_cognition_coherence_fabric")
    assert r.valid
    assert r.engineering_class == "OperatorCognitionCoherenceLayer"
    assert r.mythic_label == "Coherence Fabric"


def test_rejects_mythic_tokens_in_class():
    r = translate_mythic("", domain="Summon", function="Wave", role="Engine")
    assert not r.valid
    assert any("mythic token" in e for e in r.errors)
