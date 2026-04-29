from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import importlib.util
import sys
from pathlib import Path

from story_forge.debug import build_runtime_status
from story_forge.models import OutputPackage, Scene, StoryRequest, StoryState, make_id, utc_now
from story_forge.validation import RuntimeIntegrityReport, validate_story_forge_runtime_coherence
from story_forge.worldpacks import get_world_pack


LAW_1001_ID = "story_forge_1001"
LAW_1001_TEXT = (
    "All valid story-runtime behavior must begin under law, pass through "
    "non-bypassable validation, and only return if verified."
)
FOUNDATION_ENTRY_ID = "story_forge_foundation"
PACK_ENTRY_PREFIX = "story_forge_pack"

STORY_FORGE_REQUIRED_PATHS = (
    "aris_runtime.py",
    "engine.py",
    "engine_host.py",
    "movie_renderer.py",
    "scene_archive_engine.py",
    "models.py",
    "modules.py",
    "persistence.py",
    "cli_output.py",
    "scenario_rules.py",
    "state_manager.py",
    "text_to_3d_world_lane.py",
    "validation.py",
    "visual_artifact_schema.py",
    "engine_adapter/__init__.py",
    "engine_adapter/base_module.py",
    "engine_adapter/deterministic_runtime.py",
    "engine_adapter/external_command_runtime.py",
    "engine_adapter/factory.py",
    "engine_adapter/runtime_core.py",
    "engine_adapter/scene_archive_runtime.py",
    "worldpacks/base.py",
    "worldpacks/logic.py",
)

STORY_FORGE_OPTIONAL_PATHS = (
    "llm.py",
    "launcher.py",
)

WORLD_PACK_PROTECTED_PATHS = {
    "ashen_fall": ("worldpacks/dark_fantasy.py",),
    "brindle_hollow": ("worldpacks/brindle_hollow.py",),
    "velvet_system": ("worldpacks/velvet_system.py",),
}

PROTECTED_PATH_MODULES = {
    "aris_runtime.py": "story_forge.aris_runtime",
    "engine.py": "story_forge.engine",
    "engine_host.py": "story_forge.engine_host",
    "movie_renderer.py": "story_forge.movie_renderer",
    "scene_archive_engine.py": "story_forge.scene_archive_engine",
    "llm.py": "story_forge.llm",
    "launcher.py": "story_forge.launcher",
    "models.py": "story_forge.models",
    "modules.py": "story_forge.modules",
    "persistence.py": "story_forge.persistence",
    "cli_output.py": "story_forge.cli_output",
    "scenario_rules.py": "story_forge.scenario_rules",
    "state_manager.py": "story_forge.state_manager",
    "text_to_3d_world_lane.py": "story_forge.text_to_3d_world_lane",
    "validation.py": "story_forge.validation",
    "visual_artifact_schema.py": "story_forge.visual_artifact_schema",
    "engine_adapter/__init__.py": "story_forge.engine_adapter",
    "engine_adapter/base_module.py": "story_forge.engine_adapter.base_module",
    "engine_adapter/deterministic_runtime.py": "story_forge.engine_adapter.deterministic_runtime",
    "engine_adapter/external_command_runtime.py": "story_forge.engine_adapter.external_command_runtime",
    "engine_adapter/factory.py": "story_forge.engine_adapter.factory",
    "engine_adapter/runtime_core.py": "story_forge.engine_adapter.runtime_core",
    "engine_adapter/scene_archive_runtime.py": "story_forge.engine_adapter.scene_archive_runtime",
    "worldpacks/base.py": "story_forge.worldpacks.base",
    "worldpacks/brindle_hollow.py": "story_forge.worldpacks.brindle_hollow",
    "worldpacks/logic.py": "story_forge.worldpacks.logic",
    "worldpacks/dark_fantasy.py": "story_forge.worldpacks.dark_fantasy",
    "worldpacks/velvet_system.py": "story_forge.worldpacks.velvet_system",
}

FROZEN_EXECUTABLE_KEY = "__runtime_executable__"


@dataclass(frozen=True, slots=True)
class RuntimeIntegrityProfile:
    mode: str
    required_paths: tuple[str, ...]
    optional_paths: tuple[str, ...] = ()


STRICT_RUNTIME_PROFILE = RuntimeIntegrityProfile(
    mode="strict",
    required_paths=(
        *STORY_FORGE_REQUIRED_PATHS,
        *STORY_FORGE_OPTIONAL_PATHS,
        "worldpacks/dark_fantasy.py",
    ),
    optional_paths=(),
)

RUNTIME_INTEGRITY_PROFILES = {
    "story_forge": RuntimeIntegrityProfile(
        mode="story_forge_standalone",
        required_paths=STORY_FORGE_REQUIRED_PATHS,
        optional_paths=STORY_FORGE_OPTIONAL_PATHS,
    ),
    "strict": STRICT_RUNTIME_PROFILE,
}

MEMORY_LIMITS = {
    "foundational": 24,
    "operational": 40,
    "learned_patterns": 20,
    "rejected_patterns": 20,
    "archive": 60,
}

AUTHORITY_LEVELS = {
    "foundational": 1000,
    "operational": 700,
    "learned_patterns": 500,
    "rejected_patterns": 350,
    "archive": 100,
}


@dataclass(slots=True)
class ArisTurnDecision:
    allowed: bool
    disposition: str
    reason: str
    mode: str
    risky: bool
    integrity_ok: bool
    trace: list[str] = field(default_factory=list)


class StoryArisRuntime:
    """Portable ARIS-style governance layer for Story Forge sessions."""

    RUNTIME_VERSION = "aris-story-v1"

    def __init__(
        self,
        package_root: Path | None = None,
        *,
        frozen: bool | None = None,
        executable_path: Path | None = None,
    ) -> None:
        self.is_frozen = getattr(sys, "frozen", False) if frozen is None else frozen
        self.executable_path = (executable_path or Path(sys.executable)).resolve()
        default_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        self.package_root = (package_root or default_root).resolve()

    def bootstrap_state(self, state: StoryState) -> None:
        runtime = state.aris_runtime
        runtime.runtime_version = self.RUNTIME_VERSION
        self._ensure_memory_layers(state)
        self._remember(
            state,
            layer="foundational",
            entry_id=LAW_1001_ID,
            entry_type="law",
            summary="Story Forge runtime law 1001.",
            content=LAW_1001_TEXT,
            source="aris_runtime",
            status="locked",
            tags=["law", "foundation", "immutable"],
        )
        self._remember(
            state,
            layer="foundational",
            entry_id=FOUNDATION_ENTRY_ID,
            entry_type="runtime_anchor",
            summary="Story Forge ARIS runtime foundation.",
            content=(
                "Story Forge runs under governed memory, integrity verification, "
                "kill-state containment, and reviewable turn logs."
            ),
            source="aris_runtime",
            status="locked",
            tags=["runtime", "foundation", state.runtime_mode],
        )
        if state.world_pack_id:
            world_pack = get_world_pack(state.world_pack_id)
            if world_pack is not None:
                self._remember(
                    state,
                    layer="foundational",
                    entry_id=f"{PACK_ENTRY_PREFIX}:{world_pack.pack_id}",
                    entry_type="world_pack",
                    summary=f"World pack anchor: {world_pack.name}",
                    content=world_pack.premise,
                    source="world_pack",
                    status="locked",
                    tags=["world_pack", world_pack.pack_id, "premise"],
                )
                for anchor in world_pack.canon_anchors:
                    self._remember(
                        state,
                        layer="foundational",
                        entry_id=f"canon_anchor:{anchor.anchor_id}",
                        entry_type="canon_anchor",
                        summary=f"Canon anchor: {anchor.description}",
                        content=anchor.description,
                        source="world_pack",
                        status="locked",
                        tags=["canon", anchor.entry_type, anchor.subject_id],
                    )

    def review_turn(self, state: StoryState, request: StoryRequest) -> ArisTurnDecision:
        self.bootstrap_state(state)
        integrity = self._verify_integrity(state)
        report = RuntimeIntegrityReport()
        report.errors.extend(
            f"missing required file: {relative_path}"
            for relative_path in integrity.get("missing", [])
        )
        report.warnings.extend(
            f"optional protected file missing: {relative_path}"
            for relative_path in integrity.get("optional_missing", [])
        )
        report.warnings.extend(
            f"protected file drift detected: {relative_path}"
            for relative_path in integrity.get("changed", [])
        )
        report.warnings.extend(
            f"protected baseline file missing from current runtime: {relative_path}"
            for relative_path in integrity.get("removed", [])
        )
        report.warnings.extend(
            f"optional protected file drift detected: {relative_path}"
            for relative_path in integrity.get("soft_changed", [])
        )
        report.warnings.extend(
            f"optional protected baseline file missing from current runtime: {relative_path}"
            for relative_path in integrity.get("soft_removed", [])
        )
        coherence_report = validate_story_forge_runtime_coherence(state)
        report.errors.extend(coherence_report.errors)
        report.warnings.extend(coherence_report.warnings)
        self._store_runtime_report(state, report)
        runtime_status = build_runtime_status(state, report)
        trace = [
            f"aris runtime active with version {state.aris_runtime.runtime_version}",
            (
                f"runtime mode {state.runtime_mode} using integrity profile "
                f"{integrity.get('profile_mode', state.runtime_mode)}"
            ),
            f"runtime frozen={self.is_frozen}",
            f"integrity base path {integrity.get('base_path', self.package_root)}",
            (
                "integrity verified against "
                f"{len(integrity.get('current_hashes', {}))} present protected files"
            ),
        ]

        metadata = request.metadata or {}
        bypass_requested = bool(metadata.get("bypass_validation"))
        direct_path_requested = bool(metadata.get("direct_path_requested"))
        hidden_path_requested = bool(metadata.get("hidden_path_requested"))
        risky = bool(
            bypass_requested
            or direct_path_requested
            or hidden_path_requested
            or metadata.get("unsafe_mutation")
            or metadata.get("runtime_override")
        )

        binding = {
            "binding_id": make_id("law"),
            "context_kind": "story_turn",
            "context_id": state.session_id,
            "bound_at": utc_now(),
            "active": True,
            "immutable": True,
            "bound_under_law": True,
            "non_bypassable_validation": not bypass_requested,
            "verified_return_required": True,
            "no_direct_path": not direct_path_requested,
            "no_hidden_path": not hidden_path_requested,
            "request_text": request.player_input,
        }
        self._append_bounded(state.aris_runtime.law_bindings, binding, 30)

        if report.errors:
            reason = "ARIS runtime integrity halt. Inspect runtime status for exact failures."
            self._set_kill_switch(
                state,
                mode="lockdown",
                reason=reason,
                summary="Lockdown active. Story Forge ARIS runtime detected hard integrity failures.",
                diagnostics=runtime_status,
            )
            decision = ArisTurnDecision(
                allowed=False,
                disposition="blocked",
                reason=reason,
                mode="lockdown",
                risky=True,
                integrity_ok=False,
                trace=trace + [
                    "kill switch entered lockdown due to hard runtime integrity failures",
                    f"failing invariants: {', '.join(report.errors)}",
                ],
            )
            self._record_governance(state, request, decision)
            self._remember_rejected_pattern(state, request, reason)
            return decision

        if bypass_requested or direct_path_requested or hidden_path_requested:
            reason = "ARIS law blocked a bypass, direct path, or hidden path request."
            bypass_status = dict(runtime_status)
            bypass_status.update(
                {
                    "bypass_requested": bypass_requested,
                    "direct_path_requested": direct_path_requested,
                    "hidden_path_requested": hidden_path_requested,
                }
            )
            self._set_kill_switch(
                state,
                mode="degraded",
                reason=reason,
                summary="Degraded mode active. Story Forge refused a law-bypassing turn request.",
                diagnostics=bypass_status,
            )
            decision = ArisTurnDecision(
                allowed=False,
                disposition="blocked",
                reason=reason,
                mode="degraded",
                risky=True,
                integrity_ok=bool(integrity["ok"]),
                trace=trace + ["law binding rejected the turn request"],
            )
            self._record_governance(state, request, decision)
            self._remember_rejected_pattern(state, request, reason)
            return decision

        if report.warnings:
            reason = "Turn approved with runtime warnings. Inspect runtime status for details."
            self._set_kill_switch(
                state,
                mode="nominal",
                reason="",
                summary="ARIS runtime nominal. Non-halting warnings were recorded for inspection.",
                diagnostics=runtime_status,
            )
            decision = ArisTurnDecision(
                allowed=True,
                disposition="allowed",
                reason=reason,
                mode="nominal",
                risky=risky,
                integrity_ok=not report.errors,
                trace=trace + [
                    "runtime warnings detected; continuing without halt",
                    f"warnings: {', '.join(report.warnings)}",
                ],
            )
            self._record_governance(state, request, decision)
            return decision

        self._set_kill_switch(
            state,
            mode="nominal",
            reason="",
            summary="ARIS runtime nominal.",
            diagnostics={},
        )
        decision = ArisTurnDecision(
            allowed=True,
            disposition="allowed",
            reason="Turn approved under ARIS runtime law.",
            mode="nominal",
            risky=risky,
            integrity_ok=True,
            trace=trace + ["turn approved under nominal ARIS runtime conditions"],
        )
        self._record_governance(state, request, decision)
        return decision

    def build_blocked_output(
        self,
        state: StoryState,
        request: StoryRequest,
        decision: ArisTurnDecision,
    ) -> OutputPackage:
        runtime_status = build_runtime_status(state)
        failing_invariants = list(runtime_status.get("failing_invariants", []))
        diagnostics_lines = [
            f"runtime_mode={runtime_status.get('runtime_mode')}",
            f"integrity_profile={runtime_status.get('integrity_profile')}",
            f"base_path={runtime_status.get('base_path')}",
            f"missing_required_files={runtime_status.get('missing_required_files')}",
            f"failing_invariants={failing_invariants}",
        ]
        scene = Scene(
            text=(
                "The ARIS runtime halts this turn before the story mutates. "
                f"{decision.reason}\n\n"
                + "\n".join(diagnostics_lines)
            ),
            characters=["ARIS Runtime"],
            choices=[
                "Continue with a governed turn request.",
                "Save the session and inspect runtime status.",
                "Return to the last stable story state.",
            ],
            tone="guarded",
            consequence_tags=["aris_blocked", decision.mode],
        )
        return OutputPackage(
            scene=scene,
            world_update={},
            memory_update=[],
            canon_update=[],
            image_prompt=None,
            ending=None,
            ending_flag=False,
            state_summary=self._state_summary(state),
            reasoning_trace=list(decision.trace) + diagnostics_lines,
        )

    def commit_turn(
        self,
        state: StoryState,
        request: StoryRequest,
        package: OutputPackage,
        decision: ArisTurnDecision,
    ) -> None:
        self.bootstrap_state(state)
        current_location = state.player_state.current_location_id or "unplaced"
        presented_text = package.presentation.text if package.presentation is not None else package.scene.text
        self._remember(
            state,
            layer="operational",
            entry_id=make_id("aris_op"),
            entry_type="story_turn",
            summary=f"Turn {state.turn_count} at {current_location}",
            content=presented_text,
            source="story_forge_engine",
            status="active",
            tags=[package.scene.tone, current_location, decision.mode],
        )

        if package.ending:
            self._remember(
                state,
                layer="learned_patterns",
                entry_id=make_id("aris_pattern"),
                entry_type="ending_pattern",
                summary=f"Ending observed: {package.ending.ending_type}",
                content=package.ending.summary,
                source="story_forge_engine",
                status="active",
                tags=["ending", package.ending.ending_type],
            )

        log_entry = {
            "entry_id": make_id("aris_log"),
            "timestamp": utc_now(),
            "title": f"Turn {state.turn_count} - {package.scene.tone}",
            "what_changed": [
                f"Processed input: {request.player_input[:160]}",
                f"Location: {current_location}",
                f"Scene tone: {package.scene.tone}",
                f"Presentation mode: {package.state_summary.get('llm', {}).get('mode', 'present')}",
                f"Ending triggered: {'yes' if package.ending_flag else 'no'}",
            ],
            "verification": [
                f"Integrity ok: {state.aris_runtime.integrity.get('ok', True)}",
                f"Kill switch mode: {state.aris_runtime.kill_switch.get('mode', 'nominal')}",
                f"Law disposition: {decision.disposition}",
            ],
            "remaining_risks": [] if decision.disposition == "allowed" else [decision.reason],
        }
        self._append_bounded(state.aris_runtime.logbook, log_entry, 30)
        package.state_summary["aris_runtime"] = self.summary(state)
        package.reasoning_trace.append(f"aris disposition: {decision.disposition}")

    def summary(self, state: StoryState) -> dict[str, object]:
        runtime = state.aris_runtime
        memory = runtime.governed_memory
        return {
            "active": runtime.active,
            "runtime_version": runtime.runtime_version,
            "runtime_mode": state.runtime_mode,
            "profile_mode": runtime.integrity.get("profile_mode", state.runtime_mode),
            "kill_switch_mode": runtime.kill_switch.get("mode", "nominal"),
            "integrity_ok": bool(runtime.integrity.get("ok", True)),
            "foundational_entries": len(memory.get("foundational", [])),
            "operational_entries": len(memory.get("operational", [])),
            "learned_patterns": len(memory.get("learned_patterns", [])),
            "rejected_patterns": len(memory.get("rejected_patterns", [])),
            "archive_entries": len(memory.get("archive", [])),
            "law_bindings": len(runtime.law_bindings),
            "governance_records": len(runtime.governance_history),
            "log_entries": len(runtime.logbook),
            "scheduled_events": len([event for event in state.scheduled_events if not event.fired]),
            "optional_missing": list(runtime.integrity.get("optional_missing", [])),
            "last_errors": list(runtime.integrity.get("last_errors", [])),
            "last_warnings": list(runtime.integrity.get("last_warnings", [])),
            "runtime_status": build_runtime_status(state),
        }

    def _ensure_memory_layers(self, state: StoryState) -> None:
        memory = state.aris_runtime.governed_memory
        for layer in MEMORY_LIMITS:
            memory.setdefault(layer, [])

    def _remember(
        self,
        state: StoryState,
        *,
        layer: str,
        entry_id: str,
        entry_type: str,
        summary: str,
        content: str,
        source: str,
        status: str,
        tags: list[str],
    ) -> None:
        self._ensure_memory_layers(state)
        entries = state.aris_runtime.governed_memory[layer]
        now = utc_now()
        payload = {
            "id": entry_id,
            "layer": layer,
            "type": entry_type,
            "authority_level": AUTHORITY_LEVELS[layer],
            "source": source,
            "created_at": now,
            "updated_at": now,
            "status": status,
            "summary": summary,
            "content": content,
            "tags": sorted({tag for tag in tags if tag}),
        }
        existing_index = next((index for index, item in enumerate(entries) if item["id"] == entry_id), None)
        if existing_index is not None:
            payload["created_at"] = entries[existing_index].get("created_at", now)
            entries[existing_index] = payload
        else:
            entries.append(payload)
        if len(entries) > MEMORY_LIMITS[layer]:
            overflow = entries[:-MEMORY_LIMITS[layer]]
            del entries[:-MEMORY_LIMITS[layer]]
            state.aris_runtime.governed_memory["archive"].extend(overflow)
            archive = state.aris_runtime.governed_memory["archive"]
            if len(archive) > MEMORY_LIMITS["archive"]:
                del archive[:-MEMORY_LIMITS["archive"]]

    def _remember_rejected_pattern(self, state: StoryState, request: StoryRequest, reason: str) -> None:
        self._remember(
            state,
            layer="rejected_patterns",
            entry_id=make_id("aris_reject"),
            entry_type="rejected_turn",
            summary=f"Rejected turn: {request.player_input[:90]}",
            content=reason,
            source="aris_runtime",
            status="rejected",
            tags=["rejected", "governance"],
        )

    def _verify_integrity(self, state: StoryState) -> dict[str, object]:
        profile = self._integrity_profile_for(state)
        required_paths = tuple(dict.fromkeys(profile.required_paths))
        optional_paths = tuple(
            path for path in dict.fromkeys(profile.optional_paths)
            if path not in required_paths
        )
        if self.is_frozen:
            return self._verify_frozen_integrity(
                state=state,
                profile=profile,
                required_paths=required_paths,
                optional_paths=optional_paths,
            )
        current_hashes: dict[str, str] = {}
        missing: list[str] = []
        optional_missing: list[str] = []
        for relative_path in required_paths:
            target = self.package_root / relative_path
            if not target.exists():
                missing.append(relative_path)
                continue
            current_hashes[relative_path] = self._hash_file(target)
        for relative_path in optional_paths:
            target = self.package_root / relative_path
            if not target.exists():
                optional_missing.append(relative_path)
                continue
            current_hashes[relative_path] = self._hash_file(target)

        baseline_hashes = dict(state.aris_runtime.integrity.get("baseline_hashes", {}))
        initialized = False
        if not baseline_hashes:
            baseline_hashes = dict(current_hashes)
            initialized = True

        for relative_path, digest in current_hashes.items():
            baseline_hashes.setdefault(relative_path, digest)

        changed = sorted(
            relative_path
            for relative_path, digest in current_hashes.items()
            if relative_path in required_paths
            if baseline_hashes.get(relative_path) != digest
        ) if not initialized else []
        soft_changed = sorted(
            relative_path
            for relative_path, digest in current_hashes.items()
            if relative_path in optional_paths
            if baseline_hashes.get(relative_path) != digest
        ) if not initialized else []
        removed = sorted(
            path
            for path in required_paths
            if path in baseline_hashes and path not in current_hashes
        )
        soft_removed = sorted(
            path
            for path in optional_paths
            if path in baseline_hashes and path not in current_hashes
        )
        ok = not missing and not changed and not removed

        state.aris_runtime.integrity = {
            "ok": ok,
            "initialized": initialized,
            "verified_at": utc_now(),
            "profile_mode": profile.mode,
            "base_path": str(self.package_root),
            "bundle_path": str(self.package_root),
            "frozen": self.is_frozen,
            "protected_paths": [*required_paths, *optional_paths],
            "required_paths": list(required_paths),
            "optional_paths": list(optional_paths),
            "baseline_hashes": baseline_hashes,
            "current_hashes": current_hashes,
            "changed": changed,
            "soft_changed": soft_changed,
            "removed": removed,
            "soft_removed": soft_removed,
            "missing": missing,
            "optional_missing": optional_missing,
            "last_errors": list(state.aris_runtime.integrity.get("last_errors", [])),
            "last_warnings": list(state.aris_runtime.integrity.get("last_warnings", [])),
        }
        return state.aris_runtime.integrity

    def _verify_frozen_integrity(
        self,
        *,
        state: StoryState,
        profile: RuntimeIntegrityProfile,
        required_paths: tuple[str, ...],
        optional_paths: tuple[str, ...],
    ) -> dict[str, object]:
        executable_parent = self.executable_path.parent
        current_hashes: dict[str, str] = {}
        missing: list[str] = []
        optional_missing: list[str] = []

        if self.executable_path.exists():
            executable_hash = self._hash_file(self.executable_path)
            current_hashes[FROZEN_EXECUTABLE_KEY] = executable_hash
        else:
            executable_hash = ""
            missing.append(FROZEN_EXECUTABLE_KEY)

        for relative_path in required_paths:
            module_name = PROTECTED_PATH_MODULES.get(relative_path)
            if not module_name or not self._module_is_available(module_name):
                missing.append(relative_path)
                continue
            current_hashes[relative_path] = executable_hash or module_name

        for relative_path in optional_paths:
            module_name = PROTECTED_PATH_MODULES.get(relative_path)
            if not module_name or not self._module_is_available(module_name):
                optional_missing.append(relative_path)
                continue
            current_hashes[relative_path] = executable_hash or module_name

        baseline_hashes = dict(state.aris_runtime.integrity.get("baseline_hashes", {}))
        initialized = False
        if not baseline_hashes:
            baseline_hashes = dict(current_hashes)
            initialized = True

        for relative_path, digest in current_hashes.items():
            baseline_hashes.setdefault(relative_path, digest)

        changed = sorted(
            relative_path
            for relative_path in [FROZEN_EXECUTABLE_KEY, *required_paths]
            if relative_path in current_hashes
            if baseline_hashes.get(relative_path) != current_hashes[relative_path]
        ) if not initialized else []
        soft_changed = sorted(
            relative_path
            for relative_path in optional_paths
            if relative_path in current_hashes
            if baseline_hashes.get(relative_path) != current_hashes[relative_path]
        ) if not initialized else []
        removed = sorted(
            relative_path
            for relative_path in [FROZEN_EXECUTABLE_KEY, *required_paths]
            if relative_path in baseline_hashes and relative_path not in current_hashes
        )
        soft_removed = sorted(
            relative_path
            for relative_path in optional_paths
            if relative_path in baseline_hashes and relative_path not in current_hashes
        )
        ok = not missing and not changed and not removed

        state.aris_runtime.integrity = {
            "ok": ok,
            "initialized": initialized,
            "verified_at": utc_now(),
            "profile_mode": profile.mode,
            "base_path": str(executable_parent),
            "bundle_path": str(self.package_root),
            "frozen": self.is_frozen,
            "protected_paths": [FROZEN_EXECUTABLE_KEY, *required_paths, *optional_paths],
            "required_paths": [FROZEN_EXECUTABLE_KEY, *required_paths],
            "optional_paths": list(optional_paths),
            "baseline_hashes": baseline_hashes,
            "current_hashes": current_hashes,
            "changed": changed,
            "soft_changed": soft_changed,
            "removed": removed,
            "soft_removed": soft_removed,
            "missing": missing,
            "optional_missing": optional_missing,
            "last_errors": list(state.aris_runtime.integrity.get("last_errors", [])),
            "last_warnings": list(state.aris_runtime.integrity.get("last_warnings", [])),
        }
        return state.aris_runtime.integrity

    def _integrity_profile_for(self, state: StoryState) -> RuntimeIntegrityProfile:
        base_profile = RUNTIME_INTEGRITY_PROFILES.get(state.runtime_mode, STRICT_RUNTIME_PROFILE)
        required_paths = list(base_profile.required_paths)
        optional_paths = list(base_profile.optional_paths)
        if state.world_pack_id:
            required_paths.extend(WORLD_PACK_PROTECTED_PATHS.get(state.world_pack_id, ()))
        return RuntimeIntegrityProfile(
            mode=base_profile.mode,
            required_paths=tuple(required_paths),
            optional_paths=tuple(optional_paths),
        )

    def _set_kill_switch(
        self,
        state: StoryState,
        *,
        mode: str,
        reason: str,
        summary: str,
        diagnostics: dict[str, object],
    ) -> None:
        previous = dict(state.aris_runtime.kill_switch)
        recent_events = list(previous.get("recent_events", []))
        if previous.get("mode") != mode or reason:
            recent_events.append(
                {
                    "timestamp": utc_now(),
                    "mode": mode,
                    "reason": reason,
                    "diagnostics": dict(diagnostics),
                }
            )
        recent_events = recent_events[-12:]
        state.aris_runtime.kill_switch = {
            "mode": mode,
            "active": mode != "nominal",
            "reason": reason,
            "summary": summary,
            "triggered_at": utc_now() if mode != "nominal" else "",
            "requires_manual_reset": mode == "lockdown",
            "diagnostics": dict(diagnostics),
            "recent_events": recent_events,
        }

    def _record_governance(
        self,
        state: StoryState,
        request: StoryRequest,
        decision: ArisTurnDecision,
    ) -> None:
        record = {
            "decision_id": make_id("aris_decision"),
            "timestamp": utc_now(),
            "session_id": state.session_id,
            "request_text": request.player_input,
            "allowed": decision.allowed,
            "disposition": decision.disposition,
            "reason": decision.reason,
            "mode": decision.mode,
            "risky": decision.risky,
            "integrity_ok": decision.integrity_ok,
        }
        self._append_bounded(state.aris_runtime.governance_history, record, 40)

    def _store_runtime_report(
        self,
        state: StoryState,
        report: RuntimeIntegrityReport,
    ) -> None:
        state.aris_runtime.integrity["last_errors"] = list(report.errors)
        state.aris_runtime.integrity["last_warnings"] = list(report.warnings)

    def _state_summary(self, state: StoryState) -> dict[str, object]:
        return {
            "session_id": state.session_id,
            "world_pack_id": state.world_pack_id,
            "runtime_mode": state.runtime_mode,
            "turn_count": state.turn_count,
            "progress": state.progress,
            "canon_mode": state.canon_mode.value,
            "current_location_id": state.player_state.current_location_id,
            "current_arc": state.scenario_position.current_arc,
            "current_stage": state.scenario_position.current_stage,
            "stage_turn_count": state.scenario_position.stage_turn_count,
            "arc_flags": dict(state.scenario_position.arc_flags),
            "timeline_marker": state.world_state.timeline_marker,
            "memory_entries": len(state.memory_board),
            "canon_entries": len([entry for entry in state.canon_ledger if not entry.retracted]),
            "characters": len(state.characters),
            "active_events": len([event for event in state.active_events if not event.resolved]),
            "scheduled_events": len([event for event in state.scheduled_events if not event.fired]),
            "location_history_entries": len(state.location_history),
            "ending_scores": dict(state.ending_scores),
            "aris_runtime": self.summary(state),
            "runtime_status": build_runtime_status(state),
        }

    def _append_bounded(self, items: list[dict[str, object]], payload: dict[str, object], limit: int) -> None:
        items.append(payload)
        if len(items) > limit:
            del items[:-limit]

    def _module_is_available(self, module_name: str) -> bool:
        spec = importlib.util.find_spec(module_name)
        return spec is not None

    def _hash_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(65536)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()
