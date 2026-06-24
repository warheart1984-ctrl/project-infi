"""VR-style steward console mockup — holographic continuity dashboard."""

from __future__ import annotations

from textwrap import dedent


def render_steward_console(
    *,
    gravity_channel: str = "active",
    sensor_fidelity: float = 0.98,
    expectations: dict[str, float] | None = None,
    observed: float = 0.3,
    crr_count: int = 3,
    k_infinity: str = "PASS",
) -> str:
    """
    Render the Continuity Steward Console as ASCII for terminal or VR HUD preview.

    Defaults mirror Mission #005 multi-steward falling-object scenario.
    """
    expectations = expectations or {
        "steward_llm": 1.0,
        "steward_human": 0.8,
        "steward_agent": 1.2,
    }

    delta_lines = []
    for steward, predicted in expectations.items():
        delta_lines.append(f"    • {steward}: {abs(predicted - observed):.1f}")

    steward_lines = [f"      ├─ {name}" for name in expectations]
    if steward_lines:
        steward_lines[-1] = steward_lines[-1].replace("├─", "└─", 1)
    steward_tree = "\n".join(steward_lines)

    return dedent(
        f"""
        ============================================================
                         CONTINUITY STEWARD CONSOLE v1
        ============================================================

        [ REALITY INTERFACE ]  (live feed)
          • Gravity channel: {gravity_channel}
          • Sensor fidelity: {sensor_fidelity:.2f}
          • Evidence packets: streaming...

        ------------------------------------------------------------

        [ EXPECTATION STREAM ]
          steward_llm → predicts: {expectations.get('steward_llm', 1.0):.1f}s
          steward_human → predicts: {expectations.get('steward_human', 0.8):.1f}s
          steward_agent → predicts: {expectations.get('steward_agent', 1.2):.1f}s

        ------------------------------------------------------------

        [ CONTRADICTION DETECTOR ]
          observed: {observed:.1f}s
          deltas:
        {chr(10).join(delta_lines)}

        ------------------------------------------------------------

        [ CE‑1 CORRECTION ENGINE ]
          • surprise magnitude: high
          • correction vectors: computed
          • CRR‑1 receipts: emitted ({crr_count})

        ------------------------------------------------------------

        [ CLG‑1 LINEAGE TREE ]
          o─ CalibrationEvent#101
        {steward_tree}

        ------------------------------------------------------------

        [ FUTURE STEWARD PROJECTION ]
          • lineage integrity: stable
          • continuity risk: low
          • K‑∞ compliance: {k_infinity}

        ============================================================
        """
    ).strip("\n")


__all__ = ["render_steward_console"]
