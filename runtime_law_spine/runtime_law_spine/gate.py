"""Runtime Law Spine gate — fail-closed substrate seal check."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import ClassVar

from src.ucr.corridor_loader import BootResult
from src.ucr.trust_root import trust_root_to_receipt_dict

from runtime_law_spine.runtime_law_spine.boot import run_measured_boot


def _strict_mode() -> bool:
    return os.environ.get("RLS_STRICT", "true").lower() not in {"0", "false", "no"}


@dataclass
class RuntimeLawSpineGate:
  """Singleton gate: measured boot must succeed before AAIS / operator kernel serves."""

  _instance: ClassVar["RuntimeLawSpineGate | None"] = None

  sealed: bool
  degraded: bool
  substrate_ok: bool
  halt_reason: str
  trust_root_receipt: dict[str, str] | None

  @classmethod
  def instance(cls) -> "RuntimeLawSpineGate":
    if cls._instance is None:
      cls._instance = cls._uninitialized()
    return cls._instance

  @classmethod
  def _uninitialized(cls) -> "RuntimeLawSpineGate":
    return cls(
        sealed=False,
        degraded=True,
        substrate_ok=False,
        halt_reason="RLS gate not initialized",
        trust_root_receipt=None,
    )

  @classmethod
  def reset_for_tests(cls) -> None:
    cls._instance = None

  @classmethod
  def require_sealed(cls) -> "RuntimeLawSpineGate":
    gate = cls.instance()
    if gate.sealed and gate.substrate_ok:
      return gate
    if _strict_mode():
      raise RuntimeError(f"RLS boot failed: {gate.halt_reason}")
    gate.degraded = True
    gate.substrate_ok = False
    return gate

  @classmethod
  def run_boot(cls) -> "RuntimeLawSpineGate":
    result = run_measured_boot()
    if result.boot_result == BootResult.OK and result.trust_root is not None:
      receipt = trust_root_to_receipt_dict(result.trust_root)
      cls._instance = cls(
          sealed=True,
          degraded=False,
          substrate_ok=True,
          halt_reason="",
          trust_root_receipt=receipt,
      )
    else:
      detail = result.detail or "measured boot failed"
      cls._instance = cls(
          sealed=False,
          degraded=True,
          substrate_ok=False,
          halt_reason=detail,
          trust_root_receipt=None,
      )
    return cls.instance()
