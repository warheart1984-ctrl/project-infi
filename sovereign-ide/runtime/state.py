from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SurfaceDefinition:
    key: str
    title: str
    subtitle: str
    backend: str
    frontend: str
    route: str
    tone: str
    focus_label: str


SURFACE_DEFINITIONS: tuple[SurfaceDefinition, ...] = (
    SurfaceDefinition(
        key="timeline",
        title="Temporal Replay Timeline",
        subtitle="Epoch playback",
        backend="Sovereign Ledger Explorer v2",
        frontend="TimelineCanvas, EventNodes, ContinuitySyncIndicator",
        route="GET /api/timeline?epoch=<int>",
        tone="cyan",
        focus_label="Focus timeline",
    ),
    SurfaceDefinition(
        key="shader",
        title="Quantum Glyph Shader Engine",
        subtitle="Harmonic visual grammar",
        backend="Harmonic Engine constants",
        frontend="DynamicPulse, RotationalHarmony, GLSL shader layer",
        route="POST /api/shader/update",
        tone="violet",
        focus_label="Focus shader",
    ),
    SurfaceDefinition(
        key="monitor",
        title="Federated AI Organism Monitor",
        subtitle="Node vitality",
        backend="Telemetry Analyzer + AAES-OS node metrics",
        frontend="MetricsPanel, Chart.js graphs, organism map",
        route="GET /api/organism/state",
        tone="emerald",
        focus_label="Focus monitor",
    ),
    SurfaceDefinition(
        key="consensus",
        title="Governance Consensus Map",
        subtitle="Promotion quorum",
        backend="Promotion v2.0 Protocol",
        frontend="Radial consensus graph and filter panel",
        route="GET /api/consensus/votes",
        tone="amber",
        focus_label="Focus consensus",
    ),
    SurfaceDefinition(
        key="ledger",
        title="Sovereign Ledger Explorer v2",
        subtitle="Immutable proof blocks",
        backend="Proof Block Generator + Ledger Controller",
        frontend="3D blockchain viewer and proof overlays",
        route="GET /api/ledger/blocks",
        tone="rose",
        focus_label="Focus ledger",
    ),
    SurfaceDefinition(
        key="mandala",
        title="Neural Mandala Composer",
        subtitle="Resonance synthesis",
        backend="Harmonic Engine pulse data",
        frontend="WebAudio + shader-driven mandala",
        route="POST /api/audio/pulse",
        tone="gold",
        focus_label="Focus mandala",
    ),
    SurfaceDefinition(
        key="ulx",
        title="ULX Workbench",
        subtitle="Compile, run, trace",
        backend="ULX core + governance bridge",
        frontend="ULX command cards and trace ledger",
        route="POST /api/ulx/compile",
        tone="cyan",
        focus_label="Focus ULX",
    ),
)


@dataclass
class SovereignRuntimeContext:
    codex: Any
    federation: Any
    architect: Any = None
    cep: Any = None
    cep_client: Any = None
    agent_loop: Any = None
    temporal_api: Any = None
    surface_definitions: tuple[SurfaceDefinition, ...] = field(
        default_factory=lambda: SURFACE_DEFINITIONS
    )
    launcher_command: str = "sovereign-ide"
    app_name: str = "Sovereign IDE"

    def get(self, name: str, default: Any = None) -> Any:
        return getattr(self, name, default)

    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)

    def summary_lines(self) -> list[str]:
        codex_base = getattr(self.codex, "base", None)
        constitution_loaded = bool(getattr(self.codex, "constitution", {}))
        federation_bootstrapped = bool(getattr(self.federation, "bootstrapped", False))
        architect = getattr(self, "architect", None)
        architect_loaded = architect is not None
        architect_commands = len(getattr(architect, "command_manifest", ())) if architect_loaded else 0
        architect_summary = list(getattr(architect, "summary_lines", lambda: [])()) if architect_loaded else []
        cep = getattr(self, "cep", None)
        cep_client = getattr(self, "cep_client", None)
        agent_loop = getattr(self, "agent_loop", None)
        temporal_api = getattr(self, "temporal_api", None)
        return [
            f"codex.base={codex_base}",
            f"codex.constitution_loaded={constitution_loaded}",
            f"codex.prime_architect_loaded={bool(getattr(self.codex, 'specs', {}).get('prime_architect', {}))}",
            f"federation.bootstrapped={federation_bootstrapped}",
            f"architect.loaded={architect_loaded}",
            f"architect.commands={architect_commands}",
            f"cep.loaded={cep is not None}",
            f"cep.pending_proposals={len(getattr(cep, 'pending_proposals', [])) if cep is not None else 0}",
            f"cep.client_loaded={cep_client is not None}",
            f"agent_loop.loaded={agent_loop is not None}",
            f"agent_loop.agents={len(getattr(agent_loop, 'agents', [])) if agent_loop is not None else 0}",
            f"temporal.loaded={temporal_api is not None}",
            *architect_summary,
            f"surfaces={len(self.surface_definitions)}",
            f"launcher={self.launcher_command}",
        ]

    def surface_keys(self) -> tuple[str, ...]:
        return tuple(surface.key for surface in self.surface_definitions)

    def surface_by_key(self, key: str) -> SurfaceDefinition | None:
        for surface in self.surface_definitions:
            if surface.key == key:
                return surface
        return None
