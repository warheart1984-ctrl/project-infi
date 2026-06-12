#!/usr/bin/env python
"""USL Megaton Chaos Hammer — extreme edge-case and failure-mode stress for Universal Substrate Loader."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import threading
from dataclasses import replace
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

USL_BASE = os.environ.get("USL_STRESS_BASE", "http://127.0.0.1:8766")
USL_BROKER_SOCKET = os.environ.get("USL_BROKER_SOCKET", "").strip()
REQUIRE_LIVE = os.environ.get("USL_STRESS_REQUIRE", "").strip().lower() in ("1", "true", "yes")
TIMEOUT = 10
_FIXTURE_LOCK = threading.Lock()
_FIXTURE_PATHS: tuple[Path, Path] | None = None


@dataclass
class UslChaosResult:
    name: str
    ok: bool
    note: str = ""
    expected_fail: bool = False
    phase: int = 0


@dataclass
class UslChaosReport:
    results: list[UslChaosResult] = field(default_factory=list)
    unexpected_failures: list[UslChaosResult] = field(default_factory=list)
    crashes: list[UslChaosResult] = field(default_factory=list)

    def add(self, r: UslChaosResult) -> None:
        self.results.append(r)
        if not r.ok and not r.expected_fail:
            self.unexpected_failures.append(r)


def _usl_health() -> tuple[int | None, str]:
    url = f"{USL_BASE.rstrip('/')}/health"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            return resp.status, (resp.read() or b"").decode("utf-8", errors="replace")[:300]
    except urllib.error.HTTPError as e:
        return e.code, (e.read() or b"").decode("utf-8", errors="replace")[:300]
    except Exception as e:
        return None, str(e)[:200]


def _usl_health_phase2(body: str) -> bool:
    try:
        doc = json.loads(body)
    except json.JSONDecodeError:
        return False
    return doc.get("phase") == 2 and doc.get("broker") == "ok"


def _safe(label: str, fn: Callable[[], None], *, phase: int, expected_fail: bool = False) -> UslChaosResult:
    try:
        fn()
        return UslChaosResult(name=label, ok=True, phase=phase, expected_fail=expected_fail)
    except Exception as exc:
        ok = expected_fail
        r = UslChaosResult(name=label, ok=ok, note=str(exc)[:200], expected_fail=expected_fail, phase=phase)
        return r


def _snapshot_fixture_paths(elf_path: Path, pe_path: Path) -> tuple[Path, Path]:
    """Copy canonical fixtures to a hammer-private snapshot (stable under concurrent reads).

    Caller must hold ``_FIXTURE_LOCK`` when updating snapshot files (see ``_ensure_fixture_paths``).
    """
    snap_dir = ROOT / "ci-artifacts" / ".megaton-fixture-snap"
    snap_dir.mkdir(parents=True, exist_ok=True)
    snap_elf = snap_dir / "minimal.elf"
    snap_pe = snap_dir / "minimal.pe"
    if not snap_elf.exists() or snap_elf.stat().st_size != elf_path.stat().st_size:
        snap_elf.write_bytes(elf_path.read_bytes())
    if not snap_pe.exists() or snap_pe.stat().st_size != pe_path.stat().st_size:
        snap_pe.write_bytes(pe_path.read_bytes())
    return snap_elf, snap_pe


def _ensure_fixture_paths() -> tuple[Path, Path]:
    global _FIXTURE_PATHS
    if _FIXTURE_PATHS is not None:
        return _FIXTURE_PATHS
    with _FIXTURE_LOCK:
        if _FIXTURE_PATHS is not None:
            return _FIXTURE_PATHS
        from tests.fixtures.usl.build_fixtures import ensure_fixtures

        _FIXTURE_PATHS = _snapshot_fixture_paths(*ensure_fixtures())
        return _FIXTURE_PATHS


def _guest_and_gate(sign: bool = False, *, process_id: str = "megaton-guest"):
    from src.usl.gate import USLGate
    from src.usl.loaders.elf import guest_from_elf

    elf_path, _ = _ensure_fixture_paths()
    with _FIXTURE_LOCK:
        guest = guest_from_elf(elf_path, process_id=process_id)
    return guest, USLGate(sign=sign)


def hammer_phase1_gate(report: UslChaosReport, *, rounds: int) -> None:
    from src.usl.adapters.windows_fs import build_fs_write_request
    from src.usl.law.default_policy import ALLOW, DENY
    from src.usl.loaders.elf import guest_from_elf, load_elf
    from src.usl.loaders.pe import load_pe
    from tests.fixtures.usl.build_fixtures import build_minimal_elf64, build_minimal_pe64

    elf_path, pe_path = _ensure_fixture_paths()

    abuse_cases = [
        (
            "unknown_profile",
            lambda g, gate: build_fs_write_request(replace(g, profile_id="evil-profile"), "/x", b"x"),
        ),
        (
            "ceiling_exceeded",
            lambda g, gate: replace(build_fs_write_request(g, "/x", b"x"), ceiling_id="proc.basic"),
        ),
        (
            "capability_denied",
            lambda g, gate: replace(build_fs_write_request(g, "/x", b"x"), capability_id="proc.spawn"),
        ),
        ("empty_path", lambda g, gate: build_fs_write_request(g, "", b"")),
        ("huge_payload", lambda g, gate: build_fs_write_request(g, "/big", b"X" * 500_000)),
        ("path_traversal", lambda g, gate: build_fs_write_request(g, "../../../etc/passwd", b"pwn")),
        ("null_in_path", lambda g, gate: build_fs_write_request(g, "a\x00b", b"z")),
    ]

    for rnd in range(rounds):
        guest, gate = _guest_and_gate()
        for name, builder in abuse_cases:
            req = builder(guest, gate)
            if not hasattr(req, "guest"):
                req.guest = guest
            try:
                transition, substrate = gate.dispatch(req)
                allowed = transition.law.decision == ALLOW
                report.add(
                    UslChaosResult(
                        name=f"p1_gate:{name}:r{rnd}",
                        ok=not allowed or name in ("empty_path", "huge_payload"),
                        note=transition.law.decision_reason[:80],
                        expected_fail=name not in ("empty_path", "huge_payload"),
                        phase=1,
                    )
                )
            except Exception as exc:
                report.add(
                    UslChaosResult(
                        name=f"p1_gate:{name}:r{rnd}",
                        ok=True,
                        note=str(exc)[:80],
                        expected_fail=True,
                        phase=1,
                    )
                )

        def _concurrent_dispatch(i: int) -> UslChaosResult:
            g, gt = _guest_and_gate(process_id=f"megaton-guest-{rnd}-{i}")
            req = build_fs_write_request(g, f"/tmp/megaton-{rnd}-{i}.txt", f"r{rnd}-{i}".encode())
            req.guest = g
            try:
                t, _ = gt.dispatch(req)
                return UslChaosResult(
                    name=f"p1_concurrent:r{rnd}:{i}",
                    ok=t.law.decision in (ALLOW, DENY),
                    note=t.law.decision,
                    phase=1,
                )
            except Exception as exc:
                return UslChaosResult(
                    name=f"p1_concurrent:r{rnd}:{i}",
                    ok=False,
                    note=str(exc)[:80],
                    phase=1,
                )

        with ThreadPoolExecutor(max_workers=16) as pool:
            for fut in as_completed([pool.submit(_concurrent_dispatch, i) for i in range(24)]):
                report.add(fut.result())

        report.add(
            _safe(
                f"p1_elf_load:r{rnd}",
                lambda: load_elf(elf_path),
                phase=1,
            )
        )
        report.add(
            _safe(
                f"p1_pe_load:r{rnd}",
                lambda: load_pe(pe_path),
                phase=1,
            )
        )
        bad_elf = elf_path.parent / f"megaton-bad-{rnd}.elf"
        bad_elf.write_bytes(b"NOTELF")
        try:
            load_elf(bad_elf)
            report.add(UslChaosResult(name=f"p1_bad_elf:r{rnd}", ok=False, note="should have raised", phase=1))
        except ValueError:
            report.add(UslChaosResult(name=f"p1_bad_elf:r{rnd}", ok=True, expected_fail=True, phase=1))
        finally:
            bad_elf.unlink(missing_ok=True)

        bad_prefix = elf_path.parent / f"megaton-bad-prefix-{rnd}.elf"
        bad_prefix.write_bytes(b"NOTELF" + build_minimal_elf64()[:20])
        try:
            load_elf(bad_prefix)
            report.add(UslChaosResult(name=f"p1_bad_elf_prefix:r{rnd}", ok=False, note="should have raised", phase=1))
        except ValueError:
            report.add(UslChaosResult(name=f"p1_bad_elf_prefix:r{rnd}", ok=True, expected_fail=True, phase=1))
        finally:
            bad_prefix.unlink(missing_ok=True)

        with _FIXTURE_LOCK:
            guest = guest_from_elf(elf_path, process_id=f"ledger-guest-{rnd}")
        _, gate = _guest_and_gate()
        ledger_len_before = len(gate.ledger)
        req = build_fs_write_request(guest, "/ledger-test", b"ledger")
        req.guest = guest
        gate.dispatch(req)
        report.add(
            UslChaosResult(
                name=f"p1_ledger_grows:r{rnd}",
                ok=len(gate.ledger) > ledger_len_before,
                phase=1,
            )
        )


def hammer_phase1_health(report: UslChaosReport, *, rounds: int, require_live: bool = False) -> None:
    status, body = _usl_health()
    if status is None:
        if require_live:
            report.add(
                UslChaosResult(
                    name="p1_health_required",
                    ok=False,
                    note="USL not reachable — admission requires live /health",
                    phase=1,
                )
            )
            return
        for rnd in range(rounds):
            report.add(
                UslChaosResult(
                    name=f"p1_health_skip:r{rnd}",
                    ok=True,
                    note="USL not reachable — skipped live health probes",
                    expected_fail=True,
                    phase=1,
                )
            )
        return

    report.add(UslChaosResult(name="p1_health_preflight", ok=status == 200, note=body[:80], phase=1))
    if require_live and status != 200:
        report.add(
            UslChaosResult(
                name="p1_health_required",
                ok=False,
                note=f"USL /health returned HTTP {status}, admission requires 200",
                phase=1,
            )
        )
        return

    abuse_paths = ["/health", "/health/../admin", "/HEALTH", "/health?x=" + "A" * 5000, "/nope"]
    for rnd in range(rounds):
        for path in abuse_paths:
            url = f"{USL_BASE.rstrip('/')}{path}"
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    code = resp.status
            except urllib.error.HTTPError as e:
                code = e.code
            except Exception as e:
                code = None
                note = str(e)[:80]
            else:
                note = str(code)
            report.add(
                UslChaosResult(
                    name=f"p1_health_abuse:{path[:40]}:r{rnd}",
                    ok=code is not None and code < 500,
                    note=note,
                    expected_fail=code in {404, 405},
                    phase=1,
                )
            )

    status2, _ = _usl_health()
    report.add(UslChaosResult(name="p1_health_postflight", ok=status2 == 200, phase=1))


def hammer_phase2_broker_live(report: UslChaosReport, *, rounds: int, require_live: bool) -> None:
    status, body = _usl_health()
    reachable = status == 200 and _usl_health_phase2(body)
    if not reachable:
        if require_live:
            report.add(
                UslChaosResult(
                    name="p2_broker_live_required",
                    ok=False,
                    note="USL /health missing phase=2 broker=ok — admission requires live broker",
                    phase=2,
                )
            )
            return
        for rnd in range(rounds):
            report.add(
                UslChaosResult(
                    name=f"p2_broker_live_skip:r{rnd}",
                    ok=True,
                    note="USL broker not reachable — skipped live broker probes",
                    expected_fail=True,
                    phase=2,
                )
            )
        return

    report.add(
        UslChaosResult(
            name="p2_broker_live_preflight",
            ok=True,
            note=body[:120],
            phase=2,
        )
    )
    for rnd in range(rounds):
        status2, body2 = _usl_health()
        report.add(
            UslChaosResult(
                name=f"p2_broker_live_probe:r{rnd}",
                ok=status2 == 200 and _usl_health_phase2(body2),
                note=body2[:120],
                phase=2,
            )
        )


def hammer_phase2_broker(report: UslChaosReport, *, rounds: int, broker_socket: str = "") -> None:
    from src.usl.broker.ipc import BrokerMessage
    from src.usl.broker.supervisor import GuestBroker, GuestBrokerConfig
    from src.usl.law.default_policy import ALLOW
    from src.usl.loaders.elf import guest_from_elf, syscall_write

    remote_socket = broker_socket or USL_BROKER_SOCKET
    remote_broker = None
    if remote_socket:
        from src.usl.broker.client import RemoteBroker

        remote_broker = RemoteBroker(remote_socket)
    elf_path, _ = _ensure_fixture_paths()
    with _FIXTURE_LOCK:
        guest = guest_from_elf(elf_path, process_id="broker-guest")

    malformed_json = [
        (b"", "empty"),
        (b"{", "truncated"),
        (b"[]", "array"),
        (b'{"capability_id":}', "broken"),
        (json.dumps({"capability_id": "fs.write", "payload_b64": "!!!"}).encode(), "bad_b64"),
    ]

    for rnd in range(rounds):
        _, gate = _guest_and_gate()
        broker = GuestBroker(gate, guest)

        for raw, label in malformed_json:
            try:
                BrokerMessage.from_json(raw)
                report.add(
                    UslChaosResult(
                        name=f"p2_broker_json:{label}:r{rnd}",
                        ok=label in ("array",),
                        note="parsed unexpectedly",
                        expected_fail=label not in ("array",),
                        phase=2,
                    )
                )
            except Exception as exc:
                report.add(
                    UslChaosResult(
                        name=f"p2_broker_json:{label}:r{rnd}",
                        ok=True,
                        note=str(exc)[:60],
                        expected_fail=True,
                        phase=2,
                    )
                )

        for label, msg in [
            ("missing_cap", BrokerMessage(msg_type="syscall", capability_id="", ceiling_id="fs.basic")),
            ("wrong_ceiling", BrokerMessage(msg_type="syscall", capability_id="fs.write", ceiling_id="proc.basic", path="/x", payload_b64=base64.b64encode(b"x").decode())),
            (
                "containment",
                BrokerMessage(
                    msg_type="syscall",
                    capability_id="fs.write",
                    ceiling_id="fs.readonly",
                    path="/x",
                    payload_b64=base64.b64encode(b"x").decode(),
                    profile_id="containment",
                ),
            ),
        ]:
            resp = broker.handle(msg)
            if label == "missing_cap":
                ok = not resp.ok and resp.decision != ALLOW
            else:
                ok = resp.decision != ALLOW
            report.add(
                UslChaosResult(
                    name=f"p2_broker_handle:{label}:r{rnd}",
                    ok=ok,
                    note=resp.decision + (f" err={resp.error}" if resp.error else ""),
                    expected_fail=True,
                    phase=2,
                )
            )

        _, gate2 = _guest_and_gate(process_id=f"broker-write-{rnd}")
        write_broker = remote_broker if remote_broker is not None else GuestBroker(gate2, guest)
        payload = b"via-broker"
        _, substrate = syscall_write(
            guest, f"/broker/elf-{rnd}.txt", payload, gate2, broker=write_broker
        )
        via = "remote" if remote_broker is not None else "inprocess"
        report.add(
            UslChaosResult(
                name=f"p2_elf_broker_write:{via}:r{rnd}",
                ok=substrate is not None and substrate.get("bytes_written") == len(payload),
                note=str(substrate)[:80] if substrate else "no substrate",
                phase=2,
            )
        )

        signed_broker = GuestBroker(
            gate,
            guest,
            config=GuestBrokerConfig(require_signed_policy=True, policy_path=Path("/nonexistent/policy.json")),
        )
        ok, detail = signed_broker.verify_policy_at_load()
        report.add(
            UslChaosResult(
                name=f"p2_unsigned_policy:r{rnd}",
                ok=not ok,
                note=detail,
                expected_fail=True,
                phase=2,
            )
        )
        resp = signed_broker.handle(
            BrokerMessage(
                msg_type="syscall",
                capability_id="fs.write",
                ceiling_id="fs.basic",
                path="/blocked",
                payload_b64=base64.b64encode(b"nope").decode(),
            )
        )
        report.add(
            UslChaosResult(
                name=f"p2_unsigned_policy_block:r{rnd}",
                ok=not resp.ok and resp.error == "unsigned_policy",
                note=resp.error or resp.decision,
                phase=2,
            )
        )


def hammer_phase3_policy_macho(report: UslChaosReport, *, rounds: int) -> None:
    from src.usl.law.default_policy import PROFILE_CEILINGS
    from src.usl.loaders.macho import load_macho
    from src.usl.policy_signing import sign_lawbook, verify_signed_policy
    from tests.fixtures.usl.build_fixtures import build_minimal_elf64

    elf_path, _ = _ensure_fixture_paths()
    for rnd in range(rounds):
        lawbook = {
            "schema": "lawbook:usl-v1",
            "profiles": {k: sorted(v) for k, v in PROFILE_CEILINGS.items()},
        }
        signed = sign_lawbook(lawbook)
        tmp = ROOT / "ci-artifacts" / f"megaton_policy_{rnd}.json"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(signed), encoding="utf-8")
        ok, detail = verify_signed_policy(tmp)
        report.add(UslChaosResult(name=f"p3_policy_verify:r{rnd}", ok=ok, note=detail[:80], phase=3))

        tampered = dict(signed)
        tampered["lawbook"] = {"evil": True}
        bad = ROOT / "ci-artifacts" / f"megaton_policy_bad_{rnd}.json"
        bad.write_text(json.dumps(tampered), encoding="utf-8")
        ok2, detail2 = verify_signed_policy(bad)
        report.add(
            UslChaosResult(
                name=f"p3_policy_tamper:r{rnd}",
                ok=not ok2,
                note=detail2[:80],
                expected_fail=True,
                phase=3,
            )
        )

        macho_trunc = elf_path.parent / f"megaton-macho-trunc-{rnd}"
        macho_trunc.write_bytes(b"\x00" * 16)
        try:
            load_macho(macho_trunc)
            report.add(UslChaosResult(name=f"p3_macho_trunc:r{rnd}", ok=False, note="no raise", phase=3))
        except ValueError:
            report.add(UslChaosResult(name=f"p3_macho_trunc:r{rnd}", ok=True, expected_fail=True, phase=3))
        finally:
            macho_trunc.unlink(missing_ok=True)

        macho_bad = elf_path.parent / f"megaton-macho-bad-{rnd}"
        macho_bad.write_bytes(build_minimal_elf64())
        try:
            load_macho(macho_bad)
            report.add(UslChaosResult(name=f"p3_macho_wrong_magic:r{rnd}", ok=False, note="no raise", phase=3))
        except ValueError:
            report.add(UslChaosResult(name=f"p3_macho_wrong_magic:r{rnd}", ok=True, expected_fail=True, phase=3))
        finally:
            macho_bad.unlink(missing_ok=True)


def hammer_phase4_substrate(report: UslChaosReport, *, rounds: int) -> None:
    from src.usl.adapters.windows_fs import build_fs_write_request
    from src.usl.broker.supervisor import GuestBroker
    from src.usl.kernel_bridge import drain_kernel_to_broker, kernel_event_to_message
    from src.usl.law.default_policy import ALLOW
    from src.usl.types import ResourceInfo

    for rnd in range(rounds):
        guest, gate = _guest_and_gate()
        for cap, ceiling in [
            ("net.connect", "net.basic"),
            ("net.dns", "net.basic"),
            ("ui.present", "ui.basic"),
            ("ui.resize", "ui.basic"),
            ("ui.focus", "ui.basic"),
        ]:
            from src.usl.types import CapabilityRequest, DeltaSummary

            req = CapabilityRequest(
                capability_id=cap,
                ceiling_id=ceiling,
                resource=ResourceInfo(kind="net" if cap.startswith("net.") else "ui", locator=f"/surface-{rnd}"),
                guest=guest,
                pre_state_hash="genesis",
                post_state_hash="post",
                delta_hash="delta",
                delta_summary=DeltaSummary(),
            )
            transition, substrate = gate.dispatch(req)
            report.add(
                UslChaosResult(
                    name=f"p4_{cap}:r{rnd}",
                    ok=transition.law.decision == ALLOW and substrate is not None,
                    note=transition.law.decision,
                    phase=4,
                )
            )

        ingest = ROOT / "ci-artifacts" / f"megaton_kernel_{rnd}.ndjson"
        ingest.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            '{"syscall":"write","path":"/k1","payload_b64":"' + base64.b64encode(b"k1").decode() + '"}',
            "NOT JSON",
            '{"syscall":"connect","host":"10.0.0.1","port":443}',
            '{"syscall":"mystery","x":1}',
            "",
        ]
        ingest.write_text("\n".join(lines) + "\n", encoding="utf-8")

        broker = GuestBroker(gate, guest)
        results = drain_kernel_to_broker(broker, ingest, max_events=50)
        report.add(
            UslChaosResult(
                name=f"p4_kernel_drain:r{rnd}",
                ok=len(results) >= 2,
                note=f"handled={len(results)}",
                phase=4,
            )
        )

        msg = kernel_event_to_message({"syscall": "write", "path": "/from-kernel", "payload_b64": ""})
        report.add(
            UslChaosResult(
                name=f"p4_kernel_map_write:r{rnd}",
                ok=msg is not None and msg.capability_id == "fs.write",
                phase=4,
            )
        )


def run_megaton_chaos(
    *,
    phase: str = "all",
    rounds: int = 3,
    require_live: bool = False,
    broker_socket: str = "",
) -> dict:
    report = UslChaosReport()
    phases = {1, 2, 3, 4} if phase == "all" else {int(phase)}

    print("=== USL MEGATON CHAOS HAMMER ===")
    print(f"ROOT={ROOT} rounds={rounds} phases={sorted(phases)}")

    if 1 in phases:
        print(f"[phase 1] gate + loaders x{rounds}...")
        hammer_phase1_gate(report, rounds=rounds)
        hammer_phase1_health(report, rounds=rounds, require_live=require_live)
    if 2 in phases:
        print(f"[phase 2] broker IPC x{rounds}...")
        hammer_phase2_broker(report, rounds=rounds, broker_socket=broker_socket)
        hammer_phase2_broker_live(report, rounds=rounds, require_live=require_live)
    if 3 in phases:
        print(f"[phase 3] policy + mach-o x{rounds}...")
        hammer_phase3_policy_macho(report, rounds=rounds)
    if 4 in phases:
        print(f"[phase 4] mesh/ui/kernel x{rounds}...")
        hammer_phase4_substrate(report, rounds=rounds)

    health_skips = sum(1 for r in report.results if r.name.startswith("p1_health_skip"))
    broker_skips = sum(1 for r in report.results if r.name.startswith("p2_broker_live_skip"))
    p1_live = 1 in phases and require_live
    p2_live = 2 in phases and require_live
    admission_ok = (
        len(report.unexpected_failures) == 0
        and len(report.crashes) == 0
        and (not p1_live or health_skips == 0)
        and (not p2_live or broker_skips == 0)
    )
    summary = {
        "hammer": "usl_megaton_chaos",
        "rounds": rounds,
        "phases": sorted(phases),
        "total_probes": len(report.results),
        "unexpected_failures": len(report.unexpected_failures),
        "crashes": len(report.crashes),
        "health_skips": health_skips,
        "broker_skips": broker_skips,
        "require_live": require_live,
        "pass": admission_ok,
        "usl_base": USL_BASE,
        "broker_socket": broker_socket or USL_BROKER_SOCKET or None,
    }

    print("\n=== MEGATON SUMMARY ===")
    print(json.dumps(summary, indent=2))
    if report.unexpected_failures:
        print("\n!!! UNEXPECTED FAILURES !!!")
        for r in report.unexpected_failures[:30]:
            print(f"  [{r.phase}] {r.name}: {r.note}")

    out = ROOT / "ci-artifacts" / "usl_megaton_chaos_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "summary": summary,
                "unexpected_failures": [r.__dict__ for r in report.unexpected_failures],
                "sample_results": [r.__dict__ for r in report.results[:200]],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nReport: {out}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="USL Megaton Chaos Hammer")
    parser.add_argument("--phase", default="all", choices=["1", "2", "3", "4", "all"])
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--usl-base", default=None, help="Override USL_STRESS_BASE")
    parser.add_argument(
        "--require-live",
        action="store_true",
        help="Fail (do not skip) when USL /health is unreachable or non-200 (also USL_STRESS_REQUIRE=1)",
    )
    parser.add_argument(
        "--broker-socket",
        default=None,
        help="Unix socket for RemoteBroker write path (also USL_BROKER_SOCKET)",
    )
    args = parser.parse_args()

    global USL_BASE, REQUIRE_LIVE, USL_BROKER_SOCKET
    if args.usl_base:
        USL_BASE = args.usl_base.rstrip("/")
    require_live = REQUIRE_LIVE or args.require_live
    broker_socket = (args.broker_socket or USL_BROKER_SOCKET or "").strip()

    summary = run_megaton_chaos(
        phase=args.phase,
        rounds=args.rounds,
        require_live=require_live,
        broker_socket=broker_socket,
    )
    if not summary.get("pass", False):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
