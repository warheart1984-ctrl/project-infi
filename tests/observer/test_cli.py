"""Tests for Mission #002 Observer CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from constitutional.runtime import ConstitutionalStateRuntime
from observer.cli import cmd_list_states, cmd_verify, load_packet
from operator_kernel.constitutional_task import register_operator_task
from operator_kernel.observer_packet import write_observer_packet_for_task
from operator_kernel.status_mapping import sync_operator_status_to_csr


@pytest.fixture(autouse=True)
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    yield


def test_observer_load_and_verify_packet(monkeypatch: pytest.MonkeyPatch) -> None:
    isolated = ConstitutionalStateRuntime()
    monkeypatch.setattr("operator_kernel.observer_packet.CSR", isolated)
    monkeypatch.setattr("operator_kernel.csr.CSR", isolated)

    task_id = "mission-002"
    register_operator_task(isolated, task_id, goal="observer kit")
    meta: dict = {"status": "closed"}
    sync_operator_status_to_csr(isolated, task_id, meta)
    packet_dir = write_observer_packet_for_task(task_id)

    load_packet(packet_dir)
    import argparse

    code = cmd_verify(argparse.Namespace(state_id=task_id))
    assert code == 0


def test_observer_list_states_empty(capsys: pytest.CaptureFixture[str]) -> None:
    import argparse

    code = cmd_list_states(argparse.Namespace())
    assert code == 0
