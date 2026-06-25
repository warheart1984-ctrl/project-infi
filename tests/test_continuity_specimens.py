"""CSS-1 continuity specimen library tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.continuity.specimens import (
    CANONICAL_SPECIMEN_TYPES,
    DarzSpecimenArchive,
    compare_specimens,
    export_specimen_artifacts,
    generate_specimen_from_runtime,
    load_specimen,
    load_specimen_library,
    morphology_class,
    validate_specimen,
)


LIBRARY = Path("specimens")


def test_csl1_loads_four_canonical_specimens_and_required_files() -> None:
    specimens = load_specimen_library(LIBRARY)

    assert [item.specimen_type for item in specimens] == list(CANONICAL_SPECIMEN_TYPES)
    assert [item.specimen_id for item in specimens] == [
        "css1.001.baseline",
        "css1.002.identity_reinforcement",
        "css1.003.governance_conflict",
        "css1.004.continuity_fracture",
    ]
    for folder in sorted(LIBRARY.iterdir()):
        if folder.is_dir():
            assert (folder / "specimen.json").is_file()
            assert (folder / "replay_trace.json").is_file()
            assert (folder / "lineage_graph.json").is_file()
            assert (folder / "wave_signature.json").is_file()
            assert (folder / "receipt.json").is_file()


def test_css1_validates_schema_replay_receipt_and_wave_ranges() -> None:
    specimen = load_specimen(LIBRARY / "001_baseline" / "specimen.json")
    report = validate_specimen(specimen)

    assert report.schema_valid is True
    assert report.replay_valid is True
    assert report.proof_status == "PROVEN"
    assert report.wave_valid is True
    assert report.violations == ()


def test_srvp1_identifies_fracture_as_failed_proof_but_valid_specimen() -> None:
    specimen = load_specimen(LIBRARY / "004_continuity_fracture" / "specimen.json")
    report = validate_specimen(specimen)

    assert report.schema_valid is True
    assert report.replay_valid is False
    assert report.proof_status == "FAILED"
    assert "srvp.proof_failed" in report.violations
    assert "srvp.replay_unstable" in report.violations


def test_sce1_compares_specimen_wave_and_lineage_morphology() -> None:
    baseline = load_specimen(LIBRARY / "001_baseline" / "specimen.json")
    fracture = load_specimen(LIBRARY / "004_continuity_fracture" / "specimen.json")

    report = compare_specimens(baseline, fracture)

    assert report.specimen_a == "css1.001.baseline"
    assert report.specimen_b == "css1.004.continuity_fracture"
    assert report.delta_A == pytest.approx(0.72)
    assert report.delta_phi == pytest.approx(0.74)
    assert report.delta_C == pytest.approx(0.78)
    assert report.delta_R == pytest.approx(0.62)
    assert report.lineage_distance > 0
    assert report.classification == "continuity_fracture_divergence"


def test_css1_accepts_reinforces_lineage_relation() -> None:
    specimen = load_specimen(LIBRARY / "002_identity_reinforcement" / "specimen.json")
    assert any(edge["relation"] == "REINFORCES" for edge in specimen.lineage)

    report = validate_specimen(specimen)

    assert report.schema_valid is True
    assert morphology_class(specimen) == "identity_dominant_continuity"


def test_sgp1_generates_specimen_from_runtime_events_and_exports_artifacts(tmp_path: Path) -> None:
    specimen = generate_specimen_from_runtime(
        specimen_id="css1.generated.identity",
        specimen_type="identity_reinforcement",
        thread_id="ct.generated.identity",
        events=[
            {
                "event_id": "evt.generated.ugr",
                "event_type": "EvidenceEvent",
                "timestamp": 1.0,
                "kernel": "UGR",
                "payload": {"summary": "identity evidence"},
            },
            {
                "event_id": "evt.generated.darz",
                "event_type": "ContinuityEvent",
                "timestamp": 2.0,
                "kernel": "DARZ",
                "payload": {"summary": "identity reinforced"},
            },
        ],
        lineage=[
            {"from": "evt.generated.ugr", "to": "evt.generated.darz", "relation": "REINFORCES"},
        ],
        metrics={
            "coherence": 0.93,
            "identity_drift": 0.01,
            "replay_stability": 1.0,
            "governance_alignment": 0.92,
            "resonance": 0.84,
        },
        wave={"A": 0.42, "f": 0.36, "phi": 0.97, "C": 0.93, "R": 0.84},
        receipt={"proof_status": "PROVEN", "replay_hash": "replay.generated", "substrate_hash": "substrate.generated"},
        conditions={"description": "Generated identity reinforcement specimen."},
    )
    output_dir = export_specimen_artifacts(specimen, tmp_path / "generated_identity")

    assert validate_specimen(specimen).schema_valid is True
    assert (output_dir / "specimen.json").is_file()
    assert (output_dir / "lineage_graph.json").is_file()
    assert (output_dir / "wave_signature.json").is_file()
    assert (output_dir / "receipt.json").is_file()
    assert (output_dir / "replay_trace.json").is_file()


def test_slc1_archives_and_reloads_specimens_as_node_memory(tmp_path: Path) -> None:
    archive = DarzSpecimenArchive(tmp_path / "darz_specimen_memory")
    baseline = load_specimen(LIBRARY / "001_baseline" / "specimen.json")
    fracture = load_specimen(LIBRARY / "004_continuity_fracture" / "specimen.json")

    archive.export_specimen(baseline)
    archive.export_specimen(fracture)

    assert archive.list_specimen_ids() == ["css1.001.baseline", "css1.004.continuity_fracture"]
    assert archive.ingest_specimen("css1.004.continuity_fracture").specimen_type == "continuity_fracture"
