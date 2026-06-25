"""CRK-T1 boundary — CIT/MIT/EIT/AIT live under fitness routes and panel names."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTES = REPO_ROOT / "src" / "constitutional_cockpit_routes.py"
COMPONENTS = REPO_ROOT / "frontend" / "src" / "components" / "constitutional"


def test_fitness_api_routes_registered() -> None:
    text = ROUTES.read_text(encoding="utf-8")
    assert '/api/fitness/comprehension/' in text
    assert '/api/fitness/meaning/' in text
    assert '/api/fitness/evidence/' in text
    assert '/api/fitness/outcome/' in text
    assert '/api/fitness/attention' in text


def test_userland_component_names_present() -> None:
    assert (COMPONENTS / "ComprehensionFitness.jsx").is_file()
    assert (COMPONENTS / "MeaningFitness.jsx").is_file()
    assert (COMPONENTS / "EvidenceFitness.jsx").is_file()
    assert (COMPONENTS / "OutcomeVariance.jsx").is_file()
    assert (COMPONENTS / "ConstitutionalFitnessSummary.jsx").is_file()


def test_legacy_strip_modules_are_reexports_only() -> None:
    for legacy, export_name in (
        ("CITStrip.jsx", "CITStrip"),
        ("MeaningStrip.jsx", "MeaningStrip"),
        ("EITStrip.jsx", "EITStrip"),
        ("OutcomeStrip.jsx", "OutcomeStrip"),
    ):
        path = COMPONENTS / legacy
        text = path.read_text(encoding="utf-8")
        assert "deprecated" in text.lower()
        assert f"as {export_name}" in text
