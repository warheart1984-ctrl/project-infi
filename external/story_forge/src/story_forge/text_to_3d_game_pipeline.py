"""Deterministic text-to-3D game world pack pipeline for Story Forge."""

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
    if token_set & {"keys", "relic", "archive", "find", "finds"}:
        return "artifact_hunt"
    if token_set & {"hazard", "maze", "escape"}:
        return "survival_exploration"
    return "mythic_exploration"


def build_game_world_spec(prompt: str, *, seed: str, session_id: str) -> dict[str, Any]:
    clean_prompt = " ".join(str(prompt or "").split())
    tokens = _tokens(clean_prompt)
    world_id = _world_id(clean_prompt, seed, session_id)
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
        "genre": _genre(tokens),
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
        "asset_placeholders": [
            {"id": entity["id"], "primitive": "box" if entity["kind"] == "hazard" else "sphere"}
            for entity in entities
        ],
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
        "geometry": [
            {"id": zone["id"], "kind": "platform", "position": zone["position"], "size": zone["size"]}
            for zone in world_spec["zones"]
        ],
        "entities": world_spec["entities"],
        "spawn": world_spec["spawn_points"][0],
        "lights": [
            {"kind": "hemisphere", "intensity": 0.9},
            {"kind": "directional", "intensity": 0.7, "position": [5, 10, 5]},
        ],
        "materials": {"platform": "#36505c", "collectible": "#e5c84c", "hazard": "#b43f4f", "player": "#42a5f5"},
        "gameplay": gameplay_spec["rules"],
    }


def _html(world_spec: dict[str, Any], gameplay_spec: dict[str, Any], scene_manifest: dict[str, Any]) -> str:
    payload = json.dumps({"world": world_spec, "gameplay": gameplay_spec, "scene": scene_manifest}, sort_keys=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{world_spec['title']}</title>
  <style>
    html, body {{ margin: 0; height: 100%; overflow: hidden; background: #101418; color: #f5f7fa; font-family: system-ui, sans-serif; }}
    #hud {{ position: fixed; left: 16px; top: 16px; padding: 10px 12px; background: rgba(10,14,18,.78); border: 1px solid rgba(255,255,255,.16); border-radius: 8px; }}
  </style>
</head>
<body>
  <div id="hud"><strong>{world_spec['title']}</strong><div id="status">Loading...</div></div>
  <script type="application/json" id="world-data">{payload}</script>
  <script type="module">
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
