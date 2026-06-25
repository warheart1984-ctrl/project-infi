# Story Forge / Movie Renderer — Redundant Pipeline Stub (Stage 1)

**Engineering class:** `RedundantStage` in `src/story_forge/redundant_pipeline.py`  
**Mythic label:** Story Forge three-layer pipeline

## Layers (RLS-01)

1. **Primary** — full scene graph + render manifest export (not implemented).
2. **Fallback** — text/storyboard-only export (stub).
3. **Safe mode** — metadata-only JSON with `safe_mode: true`.

## Stage 1 deliverables

- Dataclass `RedundantStage` with `primary_path`, `fallback_path`, `safe_mode_path`.
- No-op `export_primary`, `export_fallback`, `export_safe_mode`.
- Existing lane organs (`story_forge_lane_organ`, `movie_renderer_lane_organ`) remain until importer map marks them `status-only` or `dead`.

## Out of scope

- Blender / Three.js CI
- Asset bundling
- darz-kernel integration
