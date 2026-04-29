from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

from story_forge.engine_adapter import (
    AAISEngineModule,
    DEFAULT_ENGINE_PROVIDER,
    create_engine_module,
)


LANE_ID = "lane.text_to_3d_world"
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "i",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}
_LOCATION_HINTS = (
    "altar",
    "archive",
    "bridge",
    "cathedral",
    "chamber",
    "court",
    "garden",
    "gate",
    "hall",
    "keep",
    "moor",
    "road",
    "room",
    "street",
    "tower",
)


def _stable_hash(payload: object) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def _lane_runtime_root() -> Path:
    return Path(__file__).resolve().parents[2] / ".runtime" / "text_to_3d_world"


def _slug(value: str) -> str:
    lowered = str(value or "").strip().lower()
    token = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    return token or "scene"


def _keyword_tokens(text: str, *, limit: int = 8) -> list[str]:
    tokens = re.findall(r"[a-z0-9']+", text.lower())
    ordered: list[str] = []
    for token in tokens:
        if len(token) < 3 or token in _STOP_WORDS:
            continue
        if token not in ordered:
            ordered.append(token)
        if len(ordered) >= limit:
            break
    return ordered


def _deterministic_world_id(session_id: str, text: str) -> str:
    signature = _stable_hash({"session_id": session_id, "text": text})
    return f"world_{signature[:12]}"


def _mood_from_text(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("attack", "blood", "thorn", "break", "kill")):
        return "ominous"
    if any(word in lowered for word in ("walk", "travel", "road", "journey", "cross")):
        return "restless"
    if any(word in lowered for word in ("discover", "secret", "archive", "ledger", "learn")):
        return "curious"
    if any(word in lowered for word in ("moon", "whisper", "velvet", "scar", "altar")):
        return "eerie"
    return "steady"


def _theme_from_text(keywords: list[str]) -> str:
    keyword_set = set(keywords)
    if keyword_set & {"altar", "blood", "moon", "thorn", "velvet", "scar"}:
        return "gothic_ritual"
    if keyword_set & {"archive", "ledger", "secret", "memory", "cathedral"}:
        return "forbidden_archive"
    if keyword_set & {"garden", "moor", "bridge", "road", "tower"}:
        return "haunted_wilds"
    return "mythic_threshold"


def _primary_location(keywords: list[str]) -> str:
    for keyword in keywords:
        if keyword in _LOCATION_HINTS:
            return keyword
    return keywords[0] if keywords else "threshold"


def _deep_copy_json(value: Any) -> Any:
    return json.loads(json.dumps(value))


class TextTo3DWorldLaneError(ValueError):
    pass


@dataclass(slots=True)
class TextTo3DInput:
    lane: str
    text: str
    session_id: str
    world_id: str | None = None
    prior_state: dict[str, Any] | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> TextTo3DInput:
        if not isinstance(payload, dict):
            raise TextTo3DWorldLaneError("Text-to-3D input payload must be a dictionary.")
        lane = str(payload.get("lane", "")).strip()
        if lane != LANE_ID:
            raise TextTo3DWorldLaneError(f"lane must be '{LANE_ID}'.")
        text = str(payload.get("text", "")).strip()
        if not text:
            raise TextTo3DWorldLaneError("text is required.")
        session_id = str(payload.get("sessionId", "")).strip()
        if not session_id:
            raise TextTo3DWorldLaneError("sessionId is required.")
        world_id = payload.get("worldId")
        if world_id is not None:
            world_id = str(world_id).strip() or None
        prior_state = payload.get("priorState")
        if prior_state is not None and not isinstance(prior_state, dict):
            raise TextTo3DWorldLaneError("priorState must be an object when provided.")
        return cls(
            lane=lane,
            text=text,
            session_id=session_id,
            world_id=world_id,
            prior_state=deepcopy(prior_state) if isinstance(prior_state, dict) else None,
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "lane": self.lane,
            "text": self.text,
            "sessionId": self.session_id,
            "worldId": self.world_id,
            "priorState": deepcopy(self.prior_state),
        }


@dataclass(slots=True)
class TextTo3DState:
    scene_spec: dict[str, Any] = field(default_factory=dict)
    layout_graph: dict[str, Any] = field(default_factory=dict)
    asset_spec_list: list[dict[str, Any]] = field(default_factory=list)
    geometry_registry: dict[str, Any] = field(default_factory=dict)
    render_style: dict[str, Any] = field(default_factory=dict)
    scene_graph_handle: str | None = None
    game_systems: dict[str, Any] = field(default_factory=dict)
    game_state: dict[str, Any] = field(
        default_factory=lambda: {
            "status": "INIT",
            "meters": {},
            "narrativeScore": 0,
            "tick": 0,
            "transitions": [],
        }
    )
    event_records: list[dict[str, Any]] = field(default_factory=list)
    next_text: str | None = None

    def to_prior_state(self) -> dict[str, Any]:
        return {
            "sceneSpec": _deep_copy_json(self.scene_spec),
            "layoutGraph": _deep_copy_json(self.layout_graph),
            "assetSpecList": _deep_copy_json(self.asset_spec_list),
            "geometryRegistry": _deep_copy_json(self.geometry_registry),
            "renderStyle": _deep_copy_json(self.render_style),
            "sceneGraphHandle": self.scene_graph_handle,
            "gameSystems": _deep_copy_json(self.game_systems),
            "gameState": _deep_copy_json(self.game_state),
            "eventRecords": _deep_copy_json(self.event_records),
            "nextText": self.next_text,
        }


@dataclass(slots=True)
class TextTo3DOutput:
    lane: str
    session_id: str
    world_id: str
    scene_spec: dict[str, Any]
    scene_graph_handle: str
    game_state: dict[str, Any]
    event_records: list[dict[str, Any]]
    next_text: str | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> TextTo3DOutput:
        if not isinstance(payload, dict):
            raise TextTo3DWorldLaneError("Text-to-3D output payload must be a dictionary.")
        lane = str(payload.get("lane", "")).strip()
        if lane != LANE_ID:
            raise TextTo3DWorldLaneError(f"lane must be '{LANE_ID}'.")
        session_id = str(payload.get("sessionId", "")).strip()
        if not session_id:
            raise TextTo3DWorldLaneError("sessionId is required.")
        world_id = str(payload.get("worldId", "")).strip()
        if not world_id:
            raise TextTo3DWorldLaneError("worldId is required.")
        scene_spec = payload.get("sceneSpec")
        if not isinstance(scene_spec, dict):
            raise TextTo3DWorldLaneError("sceneSpec must be an object.")
        _validate_scene_spec(scene_spec)
        scene_graph_handle = str(payload.get("sceneGraphHandle", "")).strip()
        if not scene_graph_handle:
            raise TextTo3DWorldLaneError("sceneGraphHandle is required.")
        game_state = payload.get("gameState")
        if not isinstance(game_state, dict):
            raise TextTo3DWorldLaneError("gameState must be an object.")
        event_records = payload.get("eventRecords", [])
        if not isinstance(event_records, list):
            raise TextTo3DWorldLaneError("eventRecords must be a list.")
        next_text = payload.get("nextText")
        if next_text is not None and not isinstance(next_text, str):
            raise TextTo3DWorldLaneError("nextText must be a string when provided.")
        return cls(
            lane=lane,
            session_id=session_id,
            world_id=world_id,
            scene_spec=_deep_copy_json(scene_spec),
            scene_graph_handle=scene_graph_handle,
            game_state=_deep_copy_json(game_state),
            event_records=_deep_copy_json(event_records),
            next_text=next_text.strip() if isinstance(next_text, str) and next_text.strip() else None,
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "lane": self.lane,
            "sessionId": self.session_id,
            "worldId": self.world_id,
            "sceneSpec": _deep_copy_json(self.scene_spec),
            "sceneGraphHandle": self.scene_graph_handle,
            "gameState": _deep_copy_json(self.game_state),
            "eventRecords": _deep_copy_json(self.event_records),
            "nextText": self.next_text,
        }


@dataclass(slots=True)
class TextTo3DHistoryEntry:
    request_text: str
    updated_at: str
    output: TextTo3DOutput

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> TextTo3DHistoryEntry:
        if not isinstance(payload, dict):
            raise TextTo3DWorldLaneError("Text-to-3D history entry must be an object.")
        request_text = str(payload.get("requestText", "")).strip()
        if not request_text:
            raise TextTo3DWorldLaneError("history entry requestText is required.")
        updated_at = str(payload.get("updatedAt", "")).strip()
        if not updated_at:
            raise TextTo3DWorldLaneError("history entry updatedAt is required.")
        output = TextTo3DOutput.from_payload(payload.get("output"))
        return cls(
            request_text=request_text,
            updated_at=updated_at,
            output=output,
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "requestText": self.request_text,
            "updatedAt": self.updated_at,
            "output": self.output.to_payload(),
        }


class DeterministicSemanticParser:
    def semantic_parse(self, text: str, *, session_id: str, world_id: str) -> dict[str, Any]:
        keywords = _keyword_tokens(text)
        mood = _mood_from_text(text)
        theme = _theme_from_text(keywords)
        location_anchor = _primary_location(keywords)
        focal_objects = keywords[1:4] if len(keywords) > 1 else ["monolith", "path", "echo"]
        return {
            "sourceText": text.strip(),
            "sessionId": session_id,
            "worldId": world_id,
            "theme": theme,
            "mood": mood,
            "keywords": keywords,
            "locationAnchor": location_anchor,
            "focalObjects": focal_objects,
            "gameplayHooks": {
                "interaction": "inspect" if mood in {"curious", "eerie"} else "advance",
                "traversal": any(word in text.lower() for word in ("walk", "travel", "cross", "road", "bridge")),
                "hazard": mood == "ominous",
            },
            "seedSignature": _stable_hash({"text": text.strip(), "session_id": session_id, "world_id": world_id}),
        }


class DeterministicNarrativeContinuator:
    def narrative_continue(
        self,
        text: str,
        event_records: list[dict[str, Any]],
        game_state: dict[str, Any],
    ) -> str | None:
        if not event_records:
            return None
        lead_event = event_records[-1]
        location = str(game_state.get("sceneGraphHandle", "the scene"))
        score = int(game_state.get("narrativeScore", 0) or 0)
        event_type = str(lead_event.get("type", "runtime_transition")).replace("_", " ")
        return (
            f"After the {event_type}, the world steadies around {location} "
            f"with narrative pressure holding at {score}."
        )


@dataclass(slots=True)
class NarrativeLogStore:
    root_dir: str | Path | None = None

    def __post_init__(self) -> None:
        self.root_dir = Path(self.root_dir) if self.root_dir is not None else (_lane_runtime_root() / "logs")
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def narrative_log(
        self,
        session_id: str,
        world_id: str,
        event_records: list[dict[str, Any]],
    ) -> Path:
        session_dir = Path(self.root_dir) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        target = session_dir / f"{world_id}.jsonl"
        with target.open("a", encoding="utf-8") as handle:
            for event in event_records:
                handle.write(json.dumps(event, sort_keys=True))
                handle.write("\n")
        return target


def filter_prior_state(prior_state: dict[str, Any] | None) -> TextTo3DState:
    allowed = prior_state if isinstance(prior_state, dict) else {}

    game_state_raw = allowed.get("gameState", {})
    if not isinstance(game_state_raw, dict):
        game_state_raw = {}
    game_state = {
        "status": str(game_state_raw.get("status", "INIT") or "INIT"),
        "meters": dict(game_state_raw.get("meters", {})) if isinstance(game_state_raw.get("meters", {}), dict) else {},
        "narrativeScore": int(game_state_raw.get("narrativeScore", 0) or 0),
        "tick": int(game_state_raw.get("tick", 0) or 0),
        "transitions": list(game_state_raw.get("transitions", [])) if isinstance(game_state_raw.get("transitions", []), list) else [],
    }

    return TextTo3DState(
        scene_spec=deepcopy(allowed.get("sceneSpec", {})) if isinstance(allowed.get("sceneSpec", {}), dict) else {},
        layout_graph=deepcopy(allowed.get("layoutGraph", {})) if isinstance(allowed.get("layoutGraph", {}), dict) else {},
        asset_spec_list=deepcopy(allowed.get("assetSpecList", [])) if isinstance(allowed.get("assetSpecList", []), list) else [],
        geometry_registry=deepcopy(allowed.get("geometryRegistry", {})) if isinstance(allowed.get("geometryRegistry", {}), dict) else {},
        render_style=deepcopy(allowed.get("renderStyle", {})) if isinstance(allowed.get("renderStyle", {}), dict) else {},
        scene_graph_handle=(str(allowed.get("sceneGraphHandle")).strip() if allowed.get("sceneGraphHandle") else None),
        game_systems=deepcopy(allowed.get("gameSystems", {})) if isinstance(allowed.get("gameSystems", {}), dict) else {},
        game_state=game_state,
        event_records=[],
        next_text=(str(allowed.get("nextText")).strip() if allowed.get("nextText") else None),
    )


def _validate_scene_spec(scene_spec: dict[str, Any]) -> None:
    summary = str(scene_spec.get("summary", "")).strip()
    if not summary:
        raise TextTo3DWorldLaneError("sceneSpec.summary is required.")
    theme = str(scene_spec.get("theme", "")).strip()
    if not theme:
        raise TextTo3DWorldLaneError("sceneSpec.theme is required.")
    mood = str(scene_spec.get("mood", "")).strip()
    if not mood:
        raise TextTo3DWorldLaneError("sceneSpec.mood is required.")
    location_anchor = scene_spec.get("locationAnchor")
    if not isinstance(location_anchor, dict):
        raise TextTo3DWorldLaneError("sceneSpec.locationAnchor must be an object.")
    location_id = str(location_anchor.get("id", "")).strip()
    location_label = str(location_anchor.get("label", "")).strip()
    if not location_id or not location_label:
        raise TextTo3DWorldLaneError("sceneSpec.locationAnchor requires id and label.")
    focal_objects = scene_spec.get("focalObjects", [])
    if not isinstance(focal_objects, list):
        raise TextTo3DWorldLaneError("sceneSpec.focalObjects must be a list.")


class TextTo3DWorldLane:
    def __init__(
        self,
        *,
        semantic_parser: DeterministicSemanticParser | None = None,
        narrative_continuator: DeterministicNarrativeContinuator | None = None,
        engine_module: AAISEngineModule | None = None,
        engine_provider: str = DEFAULT_ENGINE_PROVIDER,
        engine_runtime_root: str | Path | None = None,
        engine_capture_root: str | Path | None = None,
        score_step_base: int = 6,
        engine_command: str | list[str] | None = None,
        engine_command_workdir: str | Path | None = None,
        engine_timeout_seconds: float = 30.0,
        narrative_log_store: NarrativeLogStore | None = None,
    ) -> None:
        self.semantic_parser = semantic_parser or DeterministicSemanticParser()
        self.narrative_continuator = narrative_continuator or DeterministicNarrativeContinuator()
        self._engine_module = engine_module
        self._engine_provider = engine_provider
        self._engine_runtime_root = engine_runtime_root
        self._engine_capture_root = engine_capture_root
        self._score_step_base = score_step_base
        self._engine_command = engine_command
        self._engine_command_workdir = engine_command_workdir
        self._engine_timeout_seconds = engine_timeout_seconds
        self.narrative_log_store = narrative_log_store or NarrativeLogStore()

    @property
    def engine_module(self) -> AAISEngineModule:
        if self._engine_module is None:
            self._engine_module = create_engine_module(
                self._engine_provider,
                runtime_root=self._engine_runtime_root,
                capture_root=self._engine_capture_root,
                score_step_base=self._score_step_base,
                command=self._engine_command,
                command_workdir=self._engine_command_workdir,
                timeout_seconds=self._engine_timeout_seconds,
            )
        return self._engine_module

    def run(self, lane_input: TextTo3DInput | dict[str, Any]) -> TextTo3DOutput:
        payload = lane_input if isinstance(lane_input, TextTo3DInput) else TextTo3DInput.from_payload(lane_input)
        world_id = payload.world_id or _deterministic_world_id(payload.session_id, payload.text)
        state = filter_prior_state(payload.prior_state)

        world_seed = self.semantic_parser.semantic_parse(
            payload.text,
            session_id=payload.session_id,
            world_id=world_id,
        )
        state.scene_spec = self._normalize_scene_spec(world_seed)
        state.layout_graph = self._derive_layout_graph(state.scene_spec)
        state.asset_spec_list = self._derive_asset_spec_list(state.layout_graph, state.scene_spec)
        state.geometry_registry = self._resolve_geometry(state.asset_spec_list, payload.session_id, world_id)
        state.render_style = self._derive_render_style(state.scene_spec)

        build_result = self.engine_module.scene_build(
            state.layout_graph,
            state.geometry_registry,
            state.render_style,
        )
        state.scene_graph_handle = self._require_ok(build_result, "scene_build")["sceneGraphHandle"]

        bind_result = self.engine_module.runtime_bind(
            state.scene_graph_handle,
            state.scene_spec.get("gameplayHooks", {}),
        )
        bind_data = self._require_ok(bind_result, "runtime_bind")
        state.game_systems = deepcopy(bind_data["systems"])
        pre_step_game_state = self._merge_game_state(bind_data["initialState"], state.game_state)

        step_result = self.engine_module.runtime_step(
            state.scene_graph_handle,
            state.game_systems,
            pre_step_game_state,
        )
        step_data = self._require_ok(step_result, "runtime_step")
        state.game_state = deepcopy(step_data["updatedGameState"])
        runtime_delta = deepcopy(step_data["runtimeDelta"])

        state.event_records = self._derive_event_records(
            prior_game_state=pre_step_game_state,
            updated_game_state=state.game_state,
            runtime_delta=runtime_delta,
            scene_graph_handle=state.scene_graph_handle,
        )

        for event in state.event_records:
            capture_result = self.engine_module.capture(state.scene_graph_handle, event)
            capture_data = self._require_ok(capture_result, "capture")
            event["observationalCapture"] = capture_data["artifactReference"]
            event["observational"] = bool(capture_data.get("observational", True))

        self.narrative_log_store.narrative_log(
            payload.session_id,
            world_id,
            state.event_records,
        )
        state.next_text = self.narrative_continuator.narrative_continue(
            payload.text,
            state.event_records,
            state.game_state,
        )

        return TextTo3DOutput(
            lane=LANE_ID,
            session_id=payload.session_id,
            world_id=world_id,
            scene_spec=deepcopy(state.scene_spec),
            scene_graph_handle=state.scene_graph_handle,
            game_state=deepcopy(state.game_state),
            event_records=deepcopy(state.event_records),
            next_text=state.next_text,
        )

    def run_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.run(payload).to_payload()

    def _normalize_scene_spec(self, world_seed: dict[str, Any]) -> dict[str, Any]:
        keywords = list(world_seed.get("keywords", []))
        focal_objects = list(world_seed.get("focalObjects", []))
        location_anchor = str(world_seed.get("locationAnchor", "threshold") or "threshold")
        scene_id = f"{world_seed['worldId']}:scene"
        return {
            "sceneId": scene_id,
            "worldId": world_seed["worldId"],
            "sessionId": world_seed["sessionId"],
            "summary": world_seed["sourceText"],
            "theme": world_seed["theme"],
            "mood": world_seed["mood"],
            "keywords": keywords,
            "locationAnchor": {
                "id": _slug(location_anchor),
                "label": location_anchor.replace("_", " ").title(),
            },
            "focalObjects": [
                {
                    "id": _slug(item),
                    "label": item.replace("_", " ").title(),
                }
                for item in focal_objects
            ],
            "gameplayHooks": deepcopy(world_seed.get("gameplayHooks", {})),
            "seedSignature": world_seed["seedSignature"],
        }

    def _derive_layout_graph(self, scene_spec: dict[str, Any]) -> dict[str, Any]:
        location = scene_spec["locationAnchor"]
        nodes = [
            {
                "nodeId": f"zone:{location['id']}",
                "kind": "zone",
                "label": location["label"],
                "emotionalWeight": scene_spec["mood"],
            }
        ]
        edges: list[dict[str, Any]] = []
        for index, focal_object in enumerate(scene_spec.get("focalObjects", []), start=1):
            node_id = f"object:{focal_object['id']}"
            nodes.append(
                {
                    "nodeId": node_id,
                    "kind": "object",
                    "label": focal_object["label"],
                    "emotionalWeight": scene_spec["mood"],
                    "anchorIndex": index,
                }
            )
            edges.append(
                {
                    "from": f"zone:{location['id']}",
                    "to": node_id,
                    "relationship": "contains",
                }
            )
        return {
            "nodes": nodes,
            "edges": edges,
            "anchorNodeId": f"zone:{location['id']}",
        }

    def _derive_asset_spec_list(
        self,
        layout_graph: dict[str, Any],
        scene_spec: dict[str, Any],
    ) -> list[dict[str, Any]]:
        assets = [
            {
                "assetId": f"env_{scene_spec['locationAnchor']['id']}",
                "role": "environment",
                "theme": scene_spec["theme"],
            },
            {
                "assetId": f"light_{scene_spec['mood']}",
                "role": "lighting",
                "theme": scene_spec["mood"],
            },
        ]
        for node in layout_graph.get("nodes", []):
            if node.get("kind") != "object":
                continue
            assets.append(
                {
                    "assetId": f"prop_{_slug(node['label'])}",
                    "role": "prop",
                    "theme": scene_spec["theme"],
                }
            )
        return assets

    def _resolve_geometry(
        self,
        asset_spec_list: list[dict[str, Any]],
        session_id: str,
        world_id: str,
    ) -> dict[str, Any]:
        variants = ("monolith", "arch", "altar")
        registry: dict[str, Any] = {}
        for asset in asset_spec_list:
            asset_id = str(asset.get("assetId", "asset"))
            variant_index = int(_stable_hash({"session_id": session_id, "world_id": world_id, "asset_id": asset_id})[:8], 16) % len(variants)
            registry[asset_id] = {
                "geometryId": f"geo_{asset_id}",
                "variant": variants[variant_index],
                "seed": f"{world_id}:{session_id}:{asset_id}",
                "role": asset.get("role", "prop"),
            }
        return registry

    def _derive_render_style(self, scene_spec: dict[str, Any]) -> dict[str, Any]:
        mood = scene_spec["mood"]
        palette_lookup = {
            "ominous": ["charcoal", "oxblood", "ember"],
            "restless": ["slate", "silver", "wind-blue"],
            "curious": ["ink", "amber", "dust-gold"],
            "eerie": ["midnight", "violet-gray", "moon-silver"],
            "steady": ["stone", "linen", "moss"],
        }
        lighting_lookup = {
            "ominous": "hard-shadow",
            "restless": "directional-dusk",
            "curious": "study-lantern",
            "eerie": "moonlit-fog",
            "steady": "soft-overcast",
        }
        return {
            "palette": palette_lookup.get(mood, palette_lookup["steady"]),
            "lighting": lighting_lookup.get(mood, lighting_lookup["steady"]),
            "fogDensity": 0.24 if mood in {"ominous", "eerie"} else 0.1,
            "postFx": ["bloom_low", "grain_soft"],
        }

    def _merge_game_state(
        self,
        initial_state: dict[str, Any],
        prior_game_state: dict[str, Any],
    ) -> dict[str, Any]:
        merged = deepcopy(initial_state)
        merged["status"] = str(prior_game_state.get("status", merged.get("status", "INIT")) or merged.get("status", "INIT"))
        merged["narrativeScore"] = int(prior_game_state.get("narrativeScore", merged.get("narrativeScore", 0)) or 0)
        merged["tick"] = int(prior_game_state.get("tick", merged.get("tick", 0)) or 0)
        if isinstance(prior_game_state.get("meters"), dict):
            meters = deepcopy(merged.get("meters", {}))
            for key, value in prior_game_state["meters"].items():
                try:
                    meters[str(key)] = int(value)
                except (TypeError, ValueError):
                    continue
            merged["meters"] = meters
        if isinstance(prior_game_state.get("transitions"), list):
            merged["transitions"] = deepcopy(prior_game_state["transitions"][-12:])
        return merged

    def _derive_event_records(
        self,
        *,
        prior_game_state: dict[str, Any],
        updated_game_state: dict[str, Any],
        runtime_delta: dict[str, Any],
        scene_graph_handle: str,
    ) -> list[dict[str, Any]]:
        event_records: list[dict[str, Any]] = []
        transition_id = str(runtime_delta["transition_id"])
        state_delta = {
            "tick": {
                "from": int(prior_game_state.get("tick", 0) or 0),
                "to": int(updated_game_state.get("tick", 0) or 0),
            },
            "narrativeScore": {
                "from": int(prior_game_state.get("narrativeScore", 0) or 0),
                "to": int(updated_game_state.get("narrativeScore", 0) or 0),
            },
            "status": {
                "from": str(prior_game_state.get("status", "INIT") or "INIT"),
                "to": str(updated_game_state.get("status", "INIT") or "INIT"),
            },
        }
        transition_event_id = f"evt_{_stable_hash({'transition_id': transition_id, 'type': 'runtime_transition'})[:12]}"
        event_records.append(
            {
                "eventId": transition_event_id,
                "type": "runtime_transition",
                "sceneGraphHandle": scene_graph_handle,
                "transitionId": transition_id,
                "trigger": {
                    "kind": "runtime_step",
                    "transitionType": runtime_delta.get("transition_type", "single_tick"),
                },
                "stateDelta": state_delta,
                "runtimeDelta": deepcopy(runtime_delta),
            }
        )

        previous_score = state_delta["narrativeScore"]["from"]
        updated_score = state_delta["narrativeScore"]["to"]
        threshold_floor = (previous_score // 25) * 25
        threshold_ceiling = (updated_score // 25) * 25
        if threshold_ceiling > threshold_floor and threshold_ceiling > 0:
            threshold_event_id = f"evt_{_stable_hash({'transition_id': transition_id, 'type': 'score_threshold', 'threshold': threshold_ceiling})[:12]}"
            event_records.append(
                {
                    "eventId": threshold_event_id,
                    "type": "score_threshold",
                    "sceneGraphHandle": scene_graph_handle,
                    "transitionId": transition_id,
                    "trigger": {
                        "kind": "threshold_crossed",
                        "threshold": threshold_ceiling,
                    },
                    "stateDelta": state_delta,
                    "runtimeDelta": deepcopy(runtime_delta),
                }
            )
        return event_records

    def _require_ok(self, result: dict[str, Any], action: str) -> dict[str, Any]:
        if not isinstance(result, dict) or not result.get("ok"):
            message = result.get("message", f"{action} failed") if isinstance(result, dict) else f"{action} failed"
            raise TextTo3DWorldLaneError(str(message))
        data = result.get("data")
        if not isinstance(data, dict):
            raise TextTo3DWorldLaneError(f"{action} did not return a data object.")
        return data
