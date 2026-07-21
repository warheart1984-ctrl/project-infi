from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence
from xml.etree import ElementTree as ET


def _asset_root() -> Path:
    return Path(__file__).resolve().parents[1] / "sovereign"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _normalize_selection(selected: Any) -> tuple[str, ...]:
    if selected is None:
        return ("selected",)
    if isinstance(selected, str):
        return (selected,)
    if isinstance(selected, Sequence):
        items = [str(item) for item in selected if str(item)]
        return tuple(items) or ("selected",)
    return (str(selected),)


DEFAULT_RESONANCE: dict[str, dict[str, Any]] = {
    "continuity": {"symbol": "⧖", "constant": 1.618, "description": "Temporal continuity"},
    "lineage": {"symbol": "∴", "constant": 3.141, "description": "Causal ancestry"},
    "replay": {"symbol": "⟳", "constant": 2.718, "description": "Deterministic replay"},
    "federation": {"symbol": "⚛", "constant": 7.777, "description": "Harmonic alignment"},
    "accountability": {"symbol": "⚖", "constant": 9.999, "description": "Traceable action"},
    "advisory": {"symbol": "✶", "constant": 4.444, "description": "Evidence-bound counsel"},
}

COMMAND_MANIFEST: tuple[dict[str, Any], ...] = (
    {
        "id": "promotion.approve_selected",
        "title": "Approve Selected Promotion",
        "shortcut": "Ctrl+Shift+P",
        "handler": "PromotionConsole.approve_selected",
    },
    {
        "id": "lineage.trace",
        "title": "Trace Lineage",
        "shortcut": "Ctrl+Shift+L",
        "handler": "LineageLogger.trace",
    },
    {
        "id": "replay.verify",
        "title": "Verify Replay",
        "shortcut": "Ctrl+Shift+R",
        "handler": "ReplayVerifier.validate",
    },
)


@dataclass
class HarmonicEngine:
    resonance_path: Path = field(default_factory=lambda: _asset_root() / "resonance" / "resonance.json")
    constants: dict[str, float] = field(init=False)
    resonance_table: dict[str, dict[str, Any]] = field(init=False)

    def __post_init__(self) -> None:
        self.resonance_path = Path(self.resonance_path)
        self.resonance_table = self._load_constants()
        self.constants = {name: float(entry["constant"]) for name, entry in self.resonance_table.items()}

    def _load_constants(self) -> dict[str, dict[str, Any]]:
        if not self.resonance_path.exists():
            return dict(DEFAULT_RESONANCE)
        raw = json.loads(self.resonance_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return dict(DEFAULT_RESONANCE)
        loaded: dict[str, dict[str, Any]] = {}
        for key, value in raw.items():
            if not isinstance(value, dict):
                continue
            loaded[str(key)] = {
                "symbol": str(value.get("symbol", "")),
                "constant": float(value.get("constant", 0.0)),
                "description": str(value.get("description", "")),
            }
        return loaded or dict(DEFAULT_RESONANCE)

    def get_resonance(self, invariant: str) -> float:
        return self.constants.get(invariant, 0.0)

    def pulse_frequency(self, invariant: str) -> float:
        return round(self.get_resonance(invariant) * 10.0, 3)


@dataclass
class LineageLogger:
    events: list[dict[str, Any]] = field(default_factory=list)

    def _find_event(self, command_id: str | None) -> dict[str, Any] | None:
        if not command_id:
            return None
        for event in reversed(self.events):
            if event["id"] == command_id or event["command_id"] == command_id:
                return event
        return None

    def record(self, command_id: str, parent_id: str | None, replay_token: str) -> dict[str, Any]:
        parent = self._find_event(parent_id)
        chain_id = parent["chain_id"] if parent is not None else command_id
        event = {
            "id": f"lineage_{len(self.events) + 1:04d}",
            "chain_id": chain_id,
            "command_id": command_id,
            "parent_id": parent_id,
            "replay_token": replay_token,
            "sequence": len(self.events),
        }
        self.events.append(event)
        return dict(event)

    def trace(self, chain_id: str) -> list[dict[str, Any]]:
        return [dict(event) for event in self.events if event["chain_id"] == chain_id or event["command_id"] == chain_id]

    def latest_chain_id(self) -> str | None:
        if not self.events:
            return None
        return str(self.events[-1]["chain_id"])


@dataclass
class ReplayVerifier:
    def _normalize_chain(self, chain: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        return [{key: event[key] for key in sorted(event.keys())} for event in chain]

    def _hash_chain(self, chain: Sequence[Mapping[str, Any]]) -> str:
        return _sha256(self._normalize_chain(chain))

    def validate(self, chain: Sequence[Mapping[str, Any]], expected_state: Any) -> dict[str, Any]:
        normalized_chain = self._normalize_chain(chain)
        replay_hash = _sha256(normalized_chain)
        expected_hash = _sha256(expected_state)
        matches = replay_hash == expected_hash
        return {
            "matches": matches,
            "replay_hash": replay_hash,
            "expected_hash": expected_hash,
            "event_count": len(normalized_chain),
            "chain": normalized_chain,
            "expected_state": expected_state,
        }

    def audit(self, chain: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        normalized_chain = self._normalize_chain(chain)
        replay_hash = self._hash_chain(chain)
        return {
            "report_id": f"rr_{replay_hash[:12]}",
            "replay_hash": replay_hash,
            "event_count": len(normalized_chain),
            "command_ids": [str(event.get("command_id", "")) for event in normalized_chain],
            "chain": normalized_chain,
        }


@dataclass
class FederationSynchronizer:
    host: str = "localhost"
    port: int = 8765
    epoch: int = 0
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    lineage_chain: list[dict[str, Any]] = field(default_factory=list)

    def register(
        self,
        node_id: str,
        *,
        epoch: int | None = None,
        status: str = "online",
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        node_state = {
            "node_id": node_id,
            "epoch": self.epoch if epoch is None else int(epoch),
            "status": status,
            "metadata": dict(metadata or {}),
        }
        self.nodes[node_id] = node_state
        return dict(node_state)

    def sync(self, epoch: int) -> dict[str, Any]:
        self.epoch = int(epoch)
        self.register("local", epoch=self.epoch, status="online", metadata={"role": "prime-architect"})
        return {
            "epoch": self.epoch,
            "nodes": tuple(sorted(self.nodes)),
            "lineage": tuple(self.lineage_chain[-10:]),
        }

    def verify(self, node_id: str) -> bool:
        node = self.nodes.get(node_id)
        return bool(node and node.get("status") == "online" and int(node.get("epoch", -1)) == self.epoch)


@dataclass
class MandalaVisualizer:
    resonance_path: Path = field(default_factory=lambda: _asset_root() / "resonance" / "resonance.json")
    glyph_dir: Path = field(default_factory=lambda: _asset_root() / "glyphs")
    engine: HarmonicEngine = field(init=False)
    color_grammar: dict[str, tuple[str, str]] = field(
        default_factory=lambda: {
            "continuity": ("#00ffff", "#0088ff"),
            "lineage": ("#ff00ff", "#ff66cc"),
            "replay": ("#00ff66", "#00cc44"),
            "federation": ("#ffd700", "#ff9900"),
            "accountability": ("#ffffff", "#cccccc"),
            "advisory": ("#9933ff", "#6600cc"),
        }
    )

    def __post_init__(self) -> None:
        self.resonance_path = Path(self.resonance_path)
        self.glyph_dir = Path(self.glyph_dir)
        self.engine = HarmonicEngine(self.resonance_path)

    def pulse(self, frequency: float) -> float:
        return round((math.sin(frequency) + 1.0) / 2.0, 3)

    def _load_glyph(self, invariant: str) -> ET.ElementTree:
        glyph_path = self.glyph_dir / f"glyph-{invariant}-neon.svg"
        if not glyph_path.exists():
            raise FileNotFoundError(f"Glyph not found for {invariant}: {glyph_path}")
        return ET.parse(glyph_path)

    def _apply_color(self, svg_tree: ET.ElementTree, invariant: str, intensity: float) -> ET.ElementTree:
        if invariant not in self.color_grammar:
            raise KeyError(f"Unknown invariant: {invariant}")
        primary, secondary = self.color_grammar[invariant]
        glow_level = max(1.0, round(1.0 + intensity * 3.0, 3))
        root = svg_tree.getroot()
        root.set("data-invariant", invariant)
        root.set("data-intensity", f"{intensity:.3f}")
        for elem in root.iter():
            local_name = elem.tag.rsplit("}", 1)[-1]
            if local_name == "circle":
                elem.set("stroke", primary)
            elif local_name == "text":
                elem.set("fill", secondary)
            elif local_name == "feGaussianBlur":
                elem.set("stdDeviation", f"{glow_level:.3f}")
        return svg_tree

    def render(self, state: str | Mapping[str, Any]) -> str:
        if isinstance(state, Mapping):
            invariant = str(state.get("invariant", "continuity"))
            intensity = state.get("intensity")
        else:
            invariant = str(state)
            intensity = None

        frequency = self.engine.pulse_frequency(invariant)
        if intensity is None:
            intensity = self.pulse(frequency)
        tree = self._load_glyph(invariant)
        rendered = self._apply_color(tree, invariant, float(intensity))
        return ET.tostring(rendered.getroot(), encoding="unicode")


@dataclass
class AdvisoryInterpreter:
    def interpret(self, replay_report: Mapping[str, Any], lineage_trace: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        command_ids = [str(event.get("command_id", "")) for event in lineage_trace]
        matches = bool(replay_report.get("matches", False))
        reasoning = (
            "Replay and lineage agree, so the promotion remains evidence-bound."
            if matches
            else "Replay and lineage diverge, so the command should be reviewed before approval."
        )
        return {
            "verdict": "approved" if matches else "review",
            "reasoning": reasoning,
            "command_ids": command_ids,
            "evidence": {
                "event_count": len(lineage_trace),
                "replay_hash": replay_report.get("replay_hash"),
                "expected_hash": replay_report.get("expected_hash"),
            },
        }


@dataclass
class PromotionConsole:
    lineage: LineageLogger
    replay: ReplayVerifier
    federation: FederationSynchronizer
    visualizer: MandalaVisualizer
    advisory: AdvisoryInterpreter

    def approve_selected(self, selected: Any = None, parent_id: str | None = None) -> dict[str, Any]:
        selected_items = _normalize_selection(selected)
        replay_token = _sha256(
            {
                "command": "promotion.approve_selected",
                "selected": selected_items,
            }
        )
        event = self.lineage.record("promotion.approve_selected", parent_id, replay_token)
        self.federation.lineage_chain.append(dict(event))
        trace = self.lineage.trace(event["chain_id"])
        expected_state = trace
        replay_report = self.replay.validate(trace, expected_state)
        advisory = self.advisory.interpret(replay_report, trace)
        event["status"] = advisory["verdict"]
        event["status_tags"] = ["approved"] if advisory["verdict"] == "approved" else ["review"]
        preview = self.visualizer.render({"invariant": "continuity", "intensity": 0.5})
        return {
            "status": advisory["verdict"],
            "selected": selected_items,
            "event": event,
            "trace": trace,
            "replay": replay_report,
            "advisory": advisory,
            "preview": preview,
        }


@dataclass
class PrimeArchitectRuntime:
    engine: HarmonicEngine = field(default_factory=HarmonicEngine)
    lineage: LineageLogger = field(default_factory=LineageLogger)
    replay: ReplayVerifier = field(default_factory=ReplayVerifier)
    federation: FederationSynchronizer = field(default_factory=FederationSynchronizer)
    visualizer: MandalaVisualizer = field(default_factory=MandalaVisualizer)
    advisory: AdvisoryInterpreter = field(default_factory=AdvisoryInterpreter)
    command_manifest: tuple[dict[str, Any], ...] = COMMAND_MANIFEST
    promotion: PromotionConsole = field(init=False)

    def __post_init__(self) -> None:
        self.promotion = PromotionConsole(
            lineage=self.lineage,
            replay=self.replay,
            federation=self.federation,
            visualizer=self.visualizer,
            advisory=self.advisory,
        )
        self.federation.sync(1)

    def approve_selected(self, selected: Any = None, parent_id: str | None = None) -> dict[str, Any]:
        return self.promotion.approve_selected(selected=selected, parent_id=parent_id)

    def trace_lineage(self, chain_id: str | None = None) -> list[dict[str, Any]]:
        target = chain_id or self.lineage.latest_chain_id() or "promotion.approve_selected"
        return self.lineage.trace(target)

    def verify_replay(self, chain_id: str | None = None) -> dict[str, Any]:
        trace = self.trace_lineage(chain_id)
        return self.replay.audit(trace)

    def chain_history(self) -> list[dict[str, Any]]:
        history: list[dict[str, Any]] = []
        seen: dict[str, dict[str, Any]] = {}
        latest_chain_id = self.lineage.latest_chain_id()
        for event in self.lineage.events:
            chain_id = str(event.get("chain_id", ""))
            if not chain_id:
                continue
            entry = seen.get(chain_id)
            if entry is None:
                entry = {
                    "chain_id": chain_id,
                    "event_count": 0,
                    "last_command_id": "",
                    "last_sequence": -1,
                    "status": "stale",
                    "status_tags": [],
                }
                seen[chain_id] = entry
                history.append(entry)
            entry["event_count"] += 1
            entry["last_command_id"] = str(event.get("command_id", ""))
            entry["last_sequence"] = int(event.get("sequence", -1))
            status = str(event.get("status", "")).strip().lower()
            if status:
                entry["status"] = status
                tags = event.get("status_tags", [])
                entry["status_tags"] = [str(tag) for tag in tags if str(tag)]
            if chain_id == latest_chain_id:
                entry["status"] = "latest"
                entry["status_tags"] = ["latest"] + [
                    tag for tag in entry["status_tags"] if tag != "latest"
                ]
            elif entry["status"] == "stale" and entry["event_count"] > 0:
                entry["status_tags"] = ["stale"]
        return history

    def summary_lines(self) -> list[str]:
        return [
            f"architect.resonance_constants={len(self.engine.constants)}",
            f"architect.glyphs={len(self.glyph_dir_entries())}",
            f"architect.epoch={self.federation.epoch}",
        ]

    def glyph_dir_entries(self) -> tuple[str, ...]:
        if not self.visualizer.glyph_dir.exists():
            return tuple()
        return tuple(sorted(path.name for path in self.visualizer.glyph_dir.glob("glyph-*-neon.svg")))


def build_prime_architect_runtime() -> PrimeArchitectRuntime:
    return PrimeArchitectRuntime()
