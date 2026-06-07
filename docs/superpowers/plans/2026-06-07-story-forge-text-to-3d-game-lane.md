# Story Forge Text-to-3D Game Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Story Forge's third lane into a deterministic text-to-3D game pipeline that emits structured world/game specs and a browser-playable artifact.

**Architecture:** Add focused deterministic pipeline helpers under `external/story_forge/src/story_forge/`, then wire the existing AAIS organ route in `src/capabilities/story_forge_organs.py` to call it. Keep the capability bridge and status API as the entry points, and make `game_front_door_organ` delegate into the lane rather than duplicating world-building logic.

**Tech Stack:** Python 3, pytest, JSON world-pack artifacts, static HTML/JavaScript playable export using browser-native Three.js CDN import.

---

## File Structure

- Create `tests/test_story_forge_text_to_3d_game_pipeline.py`: focused tests for prompt parsing, world spec, gameplay spec, scene manifest, playable export, and deterministic world packs.
- Create `external/story_forge/src/story_forge/text_to_3d_game_pipeline.py`: deterministic prompt-to-world-pack pipeline.
- Modify `src/capabilities/story_forge_organs.py`: route `execute_text_to_3d_world_lane_route()` and `execute_game_front_door_admit()` through the new pipeline.
- Modify `src/text_to_3d_world_lane_organ.py`: report configured/live status when executable lane and execution proof exist.
- Modify `tests/test_text_to_3d_world_lane_organ.py`: assert the live/configured status and successful execution route.
- Modify `tests/test_game_front_door_organ.py`: assert front door can route game creation into the lane.
- Add or update `docs/proof/storyforge/TEXT_TO_3D_WORLD_LANE_ORGAN_EXECUTION_V1_PROOF.md`: execution proof marker used by status.

## Task 1: Deterministic Pipeline Core

**Files:**
- Create: `tests/test_story_forge_text_to_3d_game_pipeline.py`
- Create: `external/story_forge/src/story_forge/text_to_3d_game_pipeline.py`

- [ ] **Step 1: Write failing deterministic pipeline tests**

Add tests that describe the desired API:

```python
from __future__ import annotations

import json

from story_forge.text_to_3d_game_pipeline import build_text_to_3d_world_pack


def test_build_world_pack_is_deterministic(tmp_path):
    first = build_text_to_3d_world_pack(
        prompt="Build a moonlit archive game where the player finds three keys.",
        seed="fixed-seed",
        session_id="session-a",
        output_root=tmp_path,
    )
    second = build_text_to_3d_world_pack(
        prompt="Build a moonlit archive game where the player finds three keys.",
        seed="fixed-seed",
        session_id="session-a",
        output_root=tmp_path,
    )

    assert first["ok"] is True
    assert first["world_id"] == second["world_id"]
    assert first["world_spec"] == second["world_spec"]
    assert first["scene_manifest"] == second["scene_manifest"]
    assert first["playable_manifest"]["entrypoint"] == "index.html"


def test_world_pack_contains_engine_neutral_specs_and_playable(tmp_path):
    result = build_text_to_3d_world_pack(
        prompt="Create a desert tower platform game with a relic and a hazard.",
        seed="tower-seed",
        session_id="session-b",
        output_root=tmp_path,
    )

    world_pack = result["world_pack_path"]
    assert (world_pack / "world.spec.json").is_file()
    assert (world_pack / "gameplay.spec.json").is_file()
    assert (world_pack / "scene.manifest.json").is_file()
    assert (world_pack / "playable_manifest.json").is_file()
    assert (world_pack / "lane_receipt.json").is_file()
    assert (world_pack / "index.html").is_file()

    world_spec = json.loads((world_pack / "world.spec.json").read_text(encoding="utf-8"))
    assert world_spec["schema_version"] == "story_forge.game_world.v1"
    assert world_spec["engine_targets"] == ["threejs_static", "engine_neutral_json"]
    assert world_spec["player"]["kind"] == "explorer"
    assert world_spec["objectives"]


def test_empty_prompt_is_blocked(tmp_path):
    result = build_text_to_3d_world_pack(
        prompt="   ",
        seed="empty",
        session_id="session-c",
        output_root=tmp_path,
    )

    assert result["ok"] is False
    assert result["claim_label"] == "blocked"
    assert "prompt required" in result["message"]
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m pytest tests/test_story_forge_text_to_3d_game_pipeline.py -q`

Expected: FAIL during import because `story_forge.text_to_3d_game_pipeline` does not exist.

- [ ] **Step 3: Implement the deterministic pipeline module**

Create `external/story_forge/src/story_forge/text_to_3d_game_pipeline.py` with:

```python
from __future__ import annotations

import json
import re
from hashlib import sha256
from pathlib import Path
from typing import Any


LANE_ID = "lane.text_to_3d_world"
WORLD_SCHEMA_VERSION = "story_forge.game_world.v1"
GAMEPLAY_SCHEMA_VERSION = "story_forge.gameplay.v1"
SCENE_SCHEMA_VERSION = "story_forge.scene_manifest.v1"


def _stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return token or "world"


def _tokens(prompt: str) -> list[str]:
    stop = {"the", "and", "with", "where", "that", "into", "from", "create", "build", "game"}
    found: list[str] = []
    for token in re.findall(r"[a-z0-9]+", prompt.lower()):
        if len(token) < 3 or token in stop:
            continue
        if token not in found:
            found.append(token)
    return found[:12]


def _world_id(prompt: str, seed: str, session_id: str) -> str:
    return "world_" + _stable_hash({"prompt": prompt, "seed": seed, "session_id": session_id})[:12]


def _title(tokens: list[str], world_id: str) -> str:
    if tokens:
        return " ".join(tokens[:4]).title()
    return world_id.replace("_", " ").title()


def _genre(tokens: list[str]) -> str:
    token_set = set(tokens)
    if token_set & {"platform", "jump", "tower"}:
        return "exploration_platformer"
    if token_set & {"keys", "relic", "archive", "find"}:
        return "artifact_hunt"
    if token_set & {"hazard", "maze", "escape"}:
        return "survival_exploration"
    return "mythic_exploration"


def build_game_world_spec(prompt: str, *, seed: str, session_id: str) -> dict[str, Any]:
    clean_prompt = " ".join(str(prompt or "").split())
    tokens = _tokens(clean_prompt)
    world_id = _world_id(clean_prompt, seed, session_id)
    genre = _genre(tokens)
    objective_count = 3 if any(token in {"three", "keys"} for token in tokens) else 1
    objective_item = "key" if "keys" in tokens else ("relic" if "relic" in tokens else "sigil")
    hazards = ["falling_shadow"] if "hazard" in tokens else []
    zones = [
        {"id": "zone-start", "label": "Start", "position": [0, 0, 0], "size": [8, 1, 8]},
        {"id": "zone-goal", "label": "Goal", "position": [12, 0, -8], "size": [8, 1, 8]},
    ]
    entities = [
        {
            "id": f"{objective_item}-{index + 1}",
            "kind": "collectible",
            "label": f"{objective_item.title()} {index + 1}",
            "position": [4 + index * 3, 1, -2 - index * 2],
        }
        for index in range(objective_count)
    ]
    if hazards:
        entities.append({"id": "hazard-1", "kind": "hazard", "label": "Falling Shadow", "position": [8, 1, -5]})
    return {
        "schema_version": WORLD_SCHEMA_VERSION,
        "world_id": world_id,
        "seed": seed,
        "title": _title(tokens, world_id),
        "source_prompt": clean_prompt,
        "genre": genre,
        "camera": {"mode": "third_person_follow", "distance": 7, "height": 5},
        "player": {"kind": "explorer", "spawn": "spawn-player", "speed": 5},
        "controls": {"move": "WASD", "look": "mouse", "interact": "E", "reset": "R"},
        "objectives": [{"id": "collect-main", "verb": "collect", "target_kind": "collectible", "count": objective_count}],
        "win_conditions": [{"kind": "collected_count", "target_kind": "collectible", "count": objective_count}],
        "loss_conditions": [{"kind": "touch_hazard", "target_kind": "hazard"}] if hazards else [],
        "zones": zones,
        "spawn_points": [{"id": "spawn-player", "position": [0, 1, 0], "rotation": [0, 0, 0]}],
        "entities": entities,
        "interactions": [{"kind": "collect", "source": "player", "target_kind": "collectible"}],
        "hazards": hazards,
        "lighting": {"preset": "moonlit" if "moonlit" in tokens else "clear_key"},
        "asset_placeholders": [{"id": entity["id"], "primitive": "box" if entity["kind"] == "hazard" else "sphere"} for entity in entities],
        "engine_targets": ["threejs_static", "engine_neutral_json"],
    }


def build_gameplay_spec(world_spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": GAMEPLAY_SCHEMA_VERSION,
        "world_id": world_spec["world_id"],
        "movement": {"type": "ground_plane", "speed": world_spec["player"]["speed"]},
        "camera": world_spec["camera"],
        "rules": {
            "collect_radius": 1.25,
            "hazard_radius": 1.4,
            "score_per_collectible": 10,
            "win_conditions": world_spec["win_conditions"],
            "loss_conditions": world_spec["loss_conditions"],
        },
        "ui": {"objective_label": "Collect the required objects", "show_counter": True},
    }


def build_scene_manifest(world_spec: dict[str, Any], gameplay_spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCENE_SCHEMA_VERSION,
        "world_id": world_spec["world_id"],
        "geometry": [{"id": zone["id"], "kind": "platform", "position": zone["position"], "size": zone["size"]} for zone in world_spec["zones"]],
        "entities": world_spec["entities"],
        "spawn": world_spec["spawn_points"][0],
        "lights": [{"kind": "hemisphere", "intensity": 0.9}, {"kind": "directional", "intensity": 0.7, "position": [5, 10, 5]}],
        "materials": {"platform": "#36505c", "collectible": "#e5c84c", "hazard": "#b43f4f", "player": "#42a5f5"},
        "gameplay": gameplay_spec["rules"],
    }


def _html(world_spec: dict[str, Any], gameplay_spec: dict[str, Any], scene_manifest: dict[str, Any]) -> str:
    payload = json.dumps({"world": world_spec, "gameplay": gameplay_spec, "scene": scene_manifest}, sort_keys=True)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{world_spec['title']}</title>
  <style>
    html, body {{ margin: 0; height: 100%; overflow: hidden; background: #101418; color: #f5f7fa; font-family: system-ui, sans-serif; }}
    #hud {{ position: fixed; left: 16px; top: 16px; padding: 10px 12px; background: rgba(10,14,18,.78); border: 1px solid rgba(255,255,255,.16); border-radius: 8px; }}
  </style>
</head>
<body>
  <div id=\"hud\"><strong>{world_spec['title']}</strong><div id=\"status\">Loading...</div></div>
  <script type=\"application/json\" id=\"world-data\">{payload}</script>
  <script type=\"module\">
    import * as THREE from 'https://unpkg.com/three@0.165.0/build/three.module.js';
    const data = JSON.parse(document.getElementById('world-data').textContent);
    const status = document.getElementById('status');
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x101418);
    const camera = new THREE.PerspectiveCamera(70, innerWidth / innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({{ antialias: true }});
    renderer.setSize(innerWidth, innerHeight);
    document.body.appendChild(renderer.domElement);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x223344, 0.9));
    const sun = new THREE.DirectionalLight(0xffffff, 0.7);
    sun.position.set(5, 10, 5);
    scene.add(sun);
    const mats = data.scene.materials;
    for (const platform of data.scene.geometry) {{
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(platform.size[0], platform.size[1], platform.size[2]), new THREE.MeshStandardMaterial({{ color: mats.platform }}));
      mesh.position.set(...platform.position);
      scene.add(mesh);
    }}
    const player = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1.6, 0.8), new THREE.MeshStandardMaterial({{ color: mats.player }}));
    player.position.set(...data.scene.spawn.position);
    scene.add(player);
    const objects = [];
    for (const entity of data.scene.entities) {{
      const color = entity.kind === 'hazard' ? mats.hazard : mats.collectible;
      const geo = entity.kind === 'hazard' ? new THREE.BoxGeometry(1, 1, 1) : new THREE.SphereGeometry(0.45, 24, 16);
      const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({{ color }}));
      mesh.position.set(...entity.position);
      mesh.userData = entity;
      scene.add(mesh);
      objects.push(mesh);
    }}
    const keys = new Set();
    addEventListener('keydown', event => keys.add(event.key.toLowerCase()));
    addEventListener('keyup', event => keys.delete(event.key.toLowerCase()));
    addEventListener('resize', () => {{ camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); }});
    let collected = 0;
    let ended = false;
    function dist(a, b) {{ return a.position.distanceTo(b.position); }}
    function loop() {{
      requestAnimationFrame(loop);
      if (!ended) {{
        const speed = 0.08;
        if (keys.has('w')) player.position.z -= speed;
        if (keys.has('s')) player.position.z += speed;
        if (keys.has('a')) player.position.x -= speed;
        if (keys.has('d')) player.position.x += speed;
        if (keys.has('r')) location.reload();
        for (const mesh of objects) {{
          if (!mesh.visible) continue;
          if (mesh.userData.kind === 'collectible' && dist(player, mesh) < data.gameplay.rules.collect_radius) {{
            mesh.visible = false;
            collected += 1;
          }}
          if (mesh.userData.kind === 'hazard' && dist(player, mesh) < data.gameplay.rules.hazard_radius) {{
            ended = true;
            status.textContent = 'Reset with R. The hazard caught you.';
          }}
        }}
        const needed = data.world.objectives[0].count;
        if (!ended && collected >= needed) {{
          ended = true;
          status.textContent = 'Complete. Reset with R.';
        }} else if (!ended) {{
          status.textContent = `Collected ${{collected}} / ${{needed}}`;
        }}
      }}
      camera.position.set(player.position.x + 6, player.position.y + 5, player.position.z + 8);
      camera.lookAt(player.position);
      renderer.render(scene, camera);
    }}
    loop();
  </script>
</body>
</html>
"""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_text_to_3d_world_pack(
    *,
    prompt: str,
    seed: str | None = None,
    session_id: str | None = None,
    output_root: str | Path,
    export_playable: bool = True,
) -> dict[str, Any]:
    clean_prompt = " ".join(str(prompt or "").split())
    if not clean_prompt:
        return {"ok": False, "claim_label": "blocked", "message": "prompt required"}
    clean_seed = str(seed or "story-forge-default-seed").strip() or "story-forge-default-seed"
    clean_session = str(session_id or "story-forge-session").strip() or "story-forge-session"
    world_spec = build_game_world_spec(clean_prompt, seed=clean_seed, session_id=clean_session)
    gameplay_spec = build_gameplay_spec(world_spec)
    scene_manifest = build_scene_manifest(world_spec, gameplay_spec)
    world_pack_path = Path(output_root) / world_spec["world_id"]
    world_pack_path.mkdir(parents=True, exist_ok=True)
    playable_manifest = {
        "schema_version": "story_forge.playable_manifest.v1",
        "world_id": world_spec["world_id"],
        "entrypoint": "index.html" if export_playable else None,
        "renderer": "threejs_static",
        "deterministic": True,
    }
    receipt = {
        "lane_id": LANE_ID,
        "world_id": world_spec["world_id"],
        "seed": clean_seed,
        "session_id": clean_session,
        "artifact_count": 6 if export_playable else 5,
        "claim_label": "asserted",
    }
    _write_json(world_pack_path / "world.spec.json", world_spec)
    _write_json(world_pack_path / "gameplay.spec.json", gameplay_spec)
    _write_json(world_pack_path / "scene.manifest.json", scene_manifest)
    _write_json(world_pack_path / "playable_manifest.json", playable_manifest)
    _write_json(world_pack_path / "lane_receipt.json", receipt)
    if export_playable:
        (world_pack_path / "index.html").write_text(_html(world_spec, gameplay_spec, scene_manifest), encoding="utf-8")
    return {
        "ok": True,
        "claim_label": "asserted",
        "lane_id": LANE_ID,
        "world_id": world_spec["world_id"],
        "world_spec": world_spec,
        "gameplay_spec": gameplay_spec,
        "scene_manifest": scene_manifest,
        "playable_manifest": playable_manifest,
        "receipt": receipt,
        "world_pack_path": world_pack_path,
        "message": "world pack generated",
    }
```

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m pytest tests/test_story_forge_text_to_3d_game_pipeline.py -q`

Expected: PASS.

## Task 2: Wire The AAIS Lane Route

**Files:**
- Modify: `src/capabilities/story_forge_organs.py`
- Modify: `tests/test_text_to_3d_world_lane_organ.py`

- [ ] **Step 1: Write failing route tests**

Append to `tests/test_text_to_3d_world_lane_organ.py`:

```python
from src.text_to_3d_world_lane_organ import execute_text_to_3d_world_lane_route


def test_execute_route_blocks_without_operator_ack(tmp_path):
    result = execute_text_to_3d_world_lane_route(
        {"prompt": "make a small 3d relic game", "seed": "s1"},
        root=tmp_path,
    )

    assert result["ok"] is False
    assert result["claim_label"] == "blocked"
    assert "operator_ack" in result["message"]


def test_execute_route_generates_world_pack(tmp_path):
    result = execute_text_to_3d_world_lane_route(
        {
            "prompt": "make a moonlit 3d archive game with keys",
            "seed": "s1",
            "session_id": "session-route",
            "operator_ack": True,
        },
        root=tmp_path,
    )

    assert result["ok"] is True
    assert result["route_status"] == "configured"
    assert result["aais_live_lane"] is True
    assert result["proposal_only"] is False
    assert result["world_spec_ref"].endswith("world.spec.json")
    assert result["playable_ref"].endswith("index.html")
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m pytest tests/test_text_to_3d_world_lane_organ.py -q`

Expected: FAIL because the current route does not enforce operator gating or generate artifact refs.

- [ ] **Step 3: Implement route wiring**

Replace `execute_text_to_3d_world_lane_route()` in `src/capabilities/story_forge_organs.py` with a gated call to `build_text_to_3d_world_pack()`. Use `.runtime/story_forge/text_to_3d_world` under the supplied repo root as the output root. Return structured block responses for missing `prompt` and missing `operator_ack`.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m pytest tests/test_text_to_3d_world_lane_organ.py tests/test_story_forge_text_to_3d_game_pipeline.py -q`

Expected: PASS.

## Task 3: Front Door Delegation And Live Status

**Files:**
- Modify: `src/capabilities/story_forge_organs.py`
- Modify: `src/text_to_3d_world_lane_organ.py`
- Modify: `tests/test_game_front_door_organ.py`
- Modify: `tests/test_text_to_3d_world_lane_organ.py`
- Create/modify: `docs/proof/storyforge/TEXT_TO_3D_WORLD_LANE_ORGAN_EXECUTION_V1_PROOF.md`

- [ ] **Step 1: Write failing front-door and status tests**

Add this to `tests/test_game_front_door_organ.py`:

```python
from src.game_front_door_organ import execute_game_front_door_admit


def test_game_front_door_routes_prompt_to_text_to_3d_lane(tmp_path):
    result = execute_game_front_door_admit(
        {
            "session_id": "game-session",
            "operator_ack": True,
            "prompt": "create a tower game with a relic",
            "seed": "front-door-seed",
        },
        root=tmp_path,
    )

    assert result["ok"] is True
    assert result["front_door_active"] is True
    assert result["lane_result"]["organ"] == "text_to_3d_world_lane_organ"
    assert result["lane_result"]["world_pack_ref"]
```

Update `tests/test_text_to_3d_world_lane_organ.py::test_build_status`:

```python
def test_build_status():
    status = build_text_to_3d_world_lane_status()
    assert status["text_to_3d_world_lane_organ_version"] == "text_to_3d_world_lane_organ.v1"
    assert status["lane_id"] == "lane.text_to_3d_world"
    assert status["read_only"] is True
    assert status["route_status"] == "configured"
    assert status["aais_live_lane"] is True
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m pytest tests/test_game_front_door_organ.py tests/test_text_to_3d_world_lane_organ.py -q`

Expected: FAIL because front door does not delegate prompt execution and status still reports not configured.

- [ ] **Step 3: Implement front-door delegation and status**

In `execute_game_front_door_admit()`, after existing session/operator checks, if `prompt` is present call `execute_text_to_3d_world_lane_route()` with the same `session_id`, `prompt`, `seed`, and `operator_ack`. Include that result as `lane_result` and mark `proposal_only` false only when the lane result succeeds.

In `build_text_to_3d_world_lane_status()`, check for `external/story_forge/src/story_forge/text_to_3d_game_pipeline.py` and `docs/proof/storyforge/TEXT_TO_3D_WORLD_LANE_ORGAN_EXECUTION_V1_PROOF.md`. When both exist, return `route_status: configured`, `aais_live_lane: true`, and `proposal_only: false`.

Create proof doc with a concise claim and verification commands.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m pytest tests/test_game_front_door_organ.py tests/test_text_to_3d_world_lane_organ.py tests/test_story_forge_text_to_3d_game_pipeline.py -q`

Expected: PASS.

## Task 4: Focused Regression And Commit

**Files:**
- All files above.

- [ ] **Step 1: Run focused Story Forge regression**

Run:

```bash
python -m pytest tests/test_story_forge_text_to_3d_game_pipeline.py tests/test_text_to_3d_world_lane_organ.py tests/test_game_front_door_organ.py tests/test_story_forge_launcher_organ.py tests/test_text_game_to_video_organ.py -q
```

Expected: PASS.

- [ ] **Step 2: Inspect diff**

Run: `git diff --stat`

Expected: only Story Forge text-to-3D game lane files, tests, and proof docs changed.

- [ ] **Step 3: Commit**

Run:

```bash
git add external/story_forge/src/story_forge/text_to_3d_game_pipeline.py src/capabilities/story_forge_organs.py src/text_to_3d_world_lane_organ.py tests/test_story_forge_text_to_3d_game_pipeline.py tests/test_text_to_3d_world_lane_organ.py tests/test_game_front_door_organ.py docs/proof/storyforge/TEXT_TO_3D_WORLD_LANE_ORGAN_EXECUTION_V1_PROOF.md docs/superpowers/plans/2026-06-07-story-forge-text-to-3d-game-lane.md
git commit -m "Build Story Forge text-to-3D game lane"
```

Expected: commit succeeds on branch `codex/story-forge-text-to-3d-game-lane`.
