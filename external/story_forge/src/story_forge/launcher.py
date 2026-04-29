from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from story_forge.app_paths import app_root, user_data_root
from story_forge.engine_adapter import DEFAULT_ENGINE_PROVIDER, available_engine_providers
from story_forge.engine import StoryForgeEngine
from story_forge.engine_host import main as engine_host_main
from story_forge.scene_archive_engine import main as scene_archive_engine_main
from story_forge.render_staging import default_movie_staging_root, run_movie_staging_janitor
from story_forge.llm import StoryForgeLlmRuntime
from story_forge.models import StoryRequest
from story_forge.packaged_admission import (
    verify_packaged_admission,
    verify_packaged_smoke_token,
)
from story_forge.runtime import ConsoleRuntime, render_output
from story_forge.worldpacks import get_world_pack, list_world_packs


DEFAULT_WORLD_PACK = "velvet_system"
LAUNCHER_SETTINGS_FILE = "launcher_settings.json"
PACK_LIST_COMMANDS = {"/packs", "/world-packs"}
SWITCH_PACK_COMMANDS = {"/switch", "/switch-pack"}
SET_DEFAULT_PACK_COMMANDS = {"/set-default-pack", "/default-pack"}
CURRENT_PACK_COMMANDS = {"/current-pack", "/pack"}
LAUNCHER_HELP_COMMANDS = {"/launcher-help", "/help packs"}
LLM_STATUS_COMMANDS = {"/llm-status"}
LLM_PROBE_COMMANDS = {"/probe-llm"}

PROMPT_EXAMPLES = {
    "charming_knife": [
        "misfile accession",
        "ghostline recording",
        "glass arrival",
        "rain and neon",
        "ash library",
        "keep the balance",
    ],
    "ashen_fall": [
        "crow omen",
        "ferry to thornmere",
        "oath to Edda",
        "ring the bell",
        "claim the crown",
    ],
    "brindle_hollow": [
        "notebook drawer",
        "walk out to main street",
        "diner june again",
        "orchard road",
        "acknowledge without intention",
    ],
    "velvet_system": [
        "ledger under glass",
        "knife district carriage",
        "silver thread oath",
        "ink chamber",
        "editorial needle",
    ],
}

def launcher_settings_path() -> Path:
    return user_data_root() / LAUNCHER_SETTINGS_FILE


def default_autosave_dir() -> Path:
    return app_root() / ".runtime" / "autosave"


def load_launcher_settings() -> dict[str, object]:
    path = launcher_settings_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def save_launcher_settings(settings: dict[str, object]) -> Path:
    path = launcher_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def get_preferred_world_pack() -> str | None:
    preferred_pack_id = str(load_launcher_settings().get("preferred_world_pack", "") or "").strip()
    if preferred_pack_id and get_world_pack(preferred_pack_id) is not None:
        return preferred_pack_id
    return None


def set_preferred_world_pack(pack_id: str) -> Path:
    settings = load_launcher_settings()
    settings["preferred_world_pack"] = pack_id
    return save_launcher_settings(settings)


def resolve_launch_world_pack(requested_pack_id: str | None) -> str:
    if requested_pack_id:
        if get_world_pack(requested_pack_id) is None:
            raise ValueError(f"World pack '{requested_pack_id}' was not found.")
        return requested_pack_id

    preferred_pack_id = get_preferred_world_pack()
    if preferred_pack_id is not None:
        return preferred_pack_id
    return DEFAULT_WORLD_PACK


def _pack_catalog() -> list[tuple[int, object]]:
    return list(enumerate(list_world_packs(), start=1))


def _resolve_world_pack_token(token: str | None) -> str | None:
    if token is None:
        return None
    normalized = token.strip()
    if not normalized:
        return None
    if normalized.isdigit():
        index = int(normalized)
        catalog = _pack_catalog()
        if 1 <= index <= len(catalog):
            return catalog[index - 1][1].pack_id
        return None
    world_pack = get_world_pack(normalized)
    if world_pack is None:
        return None
    return world_pack.pack_id


def _print_world_pack_list(*, current_pack_id: str | None = None, preferred_pack_id: str | None = None) -> None:
    print("Available world packs:")
    for index, world_pack in _pack_catalog():
        markers: list[str] = []
        if world_pack.pack_id == current_pack_id:
            markers.append("current")
        if world_pack.pack_id == preferred_pack_id:
            markers.append("startup")
        marker_text = f" [{' / '.join(markers)}]" if markers else ""
        print(f"{index}. {world_pack.pack_id}{marker_text}")
        print(f"   {world_pack.name}")
        print(f"   Tone: {world_pack.tone}")


def _print_pack_commands() -> None:
    print("Launcher pack controls:")
    print("  /packs                 List installed world packs.")
    print("  /switch                Choose a world pack and start a clean session.")
    print("  /switch <id|number>    Start a clean session in a specific world pack.")
    print("  /set-default-pack      Save the current pack as your startup default.")
    print("  /set-default-pack <id> Save a specific world pack as your startup default.")
    print("  /current-pack          Show the active and startup world packs.")
    print("  /llm-status            Show live translation provider status for this launcher session.")
    print("  /probe-llm             Probe the configured live translation provider now.")
    print("Pipeline shell:")
    print('  /pipeline <target> "<title>" :: <raw source text>')
    print('  /ingest-file <target> "<title>" "<path-to-source>"')


def _print_llm_status(llm_runtime: StoryForgeLlmRuntime | None) -> None:
    if llm_runtime is None or not llm_runtime.requested:
        print("LLM translation status: deterministic only.")
        print("Restart with --llm to enable bounded live translation.")
        return

    config_source = llm_runtime.config_source or "none"
    if llm_runtime.translation_provider is None:
        print("LLM translation status: stability fallback.")
        print(f"Config source: {config_source}")
        print("Provider: none")
        print("Reason: no complete provider configuration was found.")
        return

    print("LLM translation status: bounded live extraction ready.")
    print(f"Config source: {config_source}")
    print(f"Provider: {llm_runtime.translation_provider.provider_name}")


def _print_llm_probe_result(report: dict[str, object]) -> None:
    print("LLM translation probe:")
    print(f"  ok: {report.get('ok', False)}")
    print(f"  configured: {report.get('configured', False)}")
    print(f"  provider: {report.get('provider', 'none')}")
    print(f"  config source: {report.get('config_source', 'none')}")
    print(f"  mode: {report.get('mode', 'translation_only')}")
    print(f"  approved: {report.get('approved', False)}")
    print(f"  degraded: {report.get('degraded', False)}")
    if "total_scenes" in report:
        print(f"  total scenes: {report.get('total_scenes')}")
    audit = report.get("audit", [])
    if audit:
        print("  audit:")
        for item in audit:
            print(f"    - {item}")


def _prompt_world_pack_selection(
    runtime: ConsoleRuntime,
    *,
    current_pack_id: str | None,
    preferred_pack_id: str | None,
) -> str | None:
    _print_world_pack_list(current_pack_id=current_pack_id, preferred_pack_id=preferred_pack_id)
    print("Enter a pack number or id. Type 'cancel' to keep the current session.")
    while True:
        choice = runtime.capture_input()
        if choice.lower() in {"cancel", "quit", "exit"}:
            print("Pack selection cancelled.")
            return None
        resolved = _resolve_world_pack_token(choice)
        if resolved is not None:
            return resolved
        print("Unknown pack selection. Enter a valid number or pack id, or type 'cancel'.")


def _handle_launcher_command(
    engine: StoryForgeEngine,
    runtime: ConsoleRuntime,
    state,
    player_input: str,
    llm_runtime: StoryForgeLlmRuntime | None,
) -> tuple[object, bool]:
    normalized = player_input.strip()
    lowered = normalized.lower()
    preferred_pack_id = get_preferred_world_pack()

    if lowered in PACK_LIST_COMMANDS:
        _print_world_pack_list(current_pack_id=state.world_pack_id, preferred_pack_id=preferred_pack_id)
        return state, True

    if lowered in CURRENT_PACK_COMMANDS:
        print(f"Current world pack: {state.world_pack_id or 'none'}")
        print(f"Startup world pack: {preferred_pack_id or DEFAULT_WORLD_PACK}")
        return state, True

    if lowered in LLM_STATUS_COMMANDS:
        _print_llm_status(llm_runtime)
        return state, True

    if lowered in LLM_PROBE_COMMANDS:
        if llm_runtime is None or not llm_runtime.requested:
            print("LLM translation is not enabled for this launcher session.")
            print("Restart with --llm or run StoryForge.exe --probe-llm.")
            return state, True
        _print_llm_probe_result(llm_runtime.probe_translation_provider())
        return state, True

    if lowered in LAUNCHER_HELP_COMMANDS:
        _print_pack_commands()
        return state, True

    if any(lowered == command or lowered.startswith(f"{command} ") for command in SWITCH_PACK_COMMANDS):
        _, _, remainder = normalized.partition(" ")
        target_pack_id = _resolve_world_pack_token(remainder) if remainder.strip() else None
        if target_pack_id is None:
            target_pack_id = _prompt_world_pack_selection(
                runtime,
                current_pack_id=state.world_pack_id,
                preferred_pack_id=preferred_pack_id,
            )
        if target_pack_id is None:
            return state, True

        new_state = engine.swap_world_pack(
            state.session_id,
            target_pack_id,
        )
        print(f"Started a clean session in '{target_pack_id}'.")
        _print_banner(new_state, llm_runtime)
        return new_state, True

    if any(lowered == command or lowered.startswith(f"{command} ") for command in SET_DEFAULT_PACK_COMMANDS):
        _, _, remainder = normalized.partition(" ")
        if remainder.strip():
            target_pack_id = _resolve_world_pack_token(remainder)
            if target_pack_id is None:
                print(f"Unknown world pack '{remainder.strip()}'. Type '/packs' to see installed packs.")
                return state, True
        else:
            target_pack_id = state.world_pack_id or DEFAULT_WORLD_PACK

        saved_path = set_preferred_world_pack(target_pack_id)
        print(f"Startup world pack set to '{target_pack_id}'.")
        print(f"Saved launcher settings to {saved_path}.")
        return state, True

    return state, False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch Story Forge.")
    parser.add_argument("--world-pack", default=None, help="World pack id to start.")
    parser.add_argument(
        "--list-world-packs",
        action="store_true",
        help="List installed world packs and exit.",
    )
    parser.add_argument(
        "--choose-world-pack",
        action="store_true",
        help="Open an interactive world-pack picker before boot.",
    )
    parser.add_argument("--player-id", default="demo-player", help="Player id for the session.")
    parser.add_argument("--session-id", default=None, help="Optional session id to reuse.")
    parser.add_argument("--load", type=Path, default=None, help="Load a saved JSON session.")
    parser.add_argument("--save-on-exit", type=Path, default=None, help="Write the session to JSON on exit.")
    parser.add_argument(
        "--autosave-dir",
        type=Path,
        default=default_autosave_dir(),
        help="Autosave directory for turn-by-turn saves.",
    )
    parser.add_argument("--no-aris", action="store_true", help="Disable the ARIS runtime layer.")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable bounded LLM translation for /pipeline commands if environment variables are configured.",
    )
    parser.add_argument(
        "--probe-llm",
        action="store_true",
        help="Probe the configured live translation provider and exit.",
    )
    parser.add_argument(
        "--text-to-3d-provider",
        default=DEFAULT_ENGINE_PROVIDER,
        choices=available_engine_providers(),
        help="Engine provider used by the /3d lane.",
    )
    parser.add_argument(
        "--text-to-3d-runtime-dir",
        type=Path,
        default=None,
        help="Optional runtime root directory for the /3d engine provider.",
    )
    parser.add_argument(
        "--text-to-3d-command",
        default=None,
        help="External command used when --text-to-3d-provider external_command.",
    )
    parser.add_argument(
        "--text-to-3d-command-workdir",
        type=Path,
        default=None,
        help="Optional working directory for the external /3d engine command.",
    )
    parser.add_argument(
        "--text-to-3d-timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds for external /3d engine commands.",
    )
    return parser


def _enforce_packaged_admission(argv: list[str]) -> tuple[list[str], int | None]:
    if not getattr(sys, "frozen", False):
        return argv, None

    executable_path = Path(sys.executable).resolve()
    if argv and argv[0] == "--completion-audit-smoke":
        if len(argv) < 2:
            print("Packaged audit smoke token was not provided.")
            return [], 2
        ok, message = verify_packaged_smoke_token(executable_path, argv[1])
        if not ok:
            print(message)
            return [], 2
        return argv[2:], None

    ok, message = verify_packaged_admission(executable_path)
    if ok:
        return argv, None

    print(message)
    print("Run the packaged completion audit flow before launching this executable.")
    return [], 2


def main(argv: list[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    argv, admission_error = _enforce_packaged_admission(argv)
    if admission_error is not None:
        return admission_error
    if argv and argv[0] == "--engine-host":
        return engine_host_main(argv[1:])
    if argv and argv[0] == "--scene-archive-engine":
        return scene_archive_engine_main(argv[1:])

    args = build_parser().parse_args(argv)
    llm_runtime = StoryForgeLlmRuntime.from_env(enabled=args.llm or args.probe_llm)
    if args.probe_llm:
        report = (
            llm_runtime.probe_translation_provider()
            if llm_runtime is not None
            else {
                "ok": False,
                "configured": False,
                "provider": "none",
                "config_source": "none",
                "mode": "translation_only",
                "approved": False,
                "degraded": False,
                "audit": ["LLM translation probing is disabled."],
            }
        )
        _print_llm_probe_result(report)
        return 0 if report.get("ok") else 1

    run_movie_staging_janitor(default_movie_staging_root())
    engine = StoryForgeEngine(
        autosave_dir=args.autosave_dir,
        enable_aris_runtime=not args.no_aris,
        llm_runtime=llm_runtime,
        text_to_3d_engine_provider=args.text_to_3d_provider,
        text_to_3d_runtime_root=args.text_to_3d_runtime_dir,
        text_to_3d_engine_command=args.text_to_3d_command,
        text_to_3d_engine_command_workdir=args.text_to_3d_command_workdir,
        text_to_3d_engine_timeout_seconds=args.text_to_3d_timeout,
    )
    runtime = ConsoleRuntime()
    preferred_pack_id = get_preferred_world_pack()
    requested_world_pack = resolve_launch_world_pack(args.world_pack)

    if args.list_world_packs:
        _print_world_pack_list(
            current_pack_id=requested_world_pack,
            preferred_pack_id=preferred_pack_id,
        )
        return 0

    if args.load is not None:
        state = engine.load_session(args.load)
    else:
        if args.choose_world_pack:
            chosen_world_pack = _prompt_world_pack_selection(
                runtime,
                current_pack_id=requested_world_pack,
                preferred_pack_id=preferred_pack_id,
            )
            if chosen_world_pack is not None:
                requested_world_pack = chosen_world_pack
        state = engine.start_world_pack_session(
            player_id=args.player_id,
            world_pack_id=requested_world_pack,
            session_id=args.session_id,
        )

    _print_banner(state, llm_runtime)

    while True:
        player_input = runtime.capture_input()
        if player_input.lower() in {"quit", "exit"}:
            break
        state, handled = _handle_launcher_command(engine, runtime, state, player_input, llm_runtime)
        if handled:
            continue
        package = engine.process_turn(
            StoryRequest(
                player_id=state.player_id,
                session_id=state.session_id,
                player_input=player_input,
            )
        )
        render_output(runtime, package)
        llm_summary = package.state_summary.get("llm", {})
        if llm_summary.get("mode") == "degraded":
            print("[presentation fallback] Deterministic scene used after bounded LLM validation.")

    if args.save_on_exit is not None:
        target = engine.save_session(state.session_id, args.save_on_exit)
        print(f"Session saved to {target}")
    return 0


def _print_banner(state, llm_runtime: StoryForgeLlmRuntime | None) -> None:
    pack_label = state.world_pack_id or "custom"
    print(f"Story Forge standalone launcher: {pack_label}")
    print("Type 'quit' to exit.")
    print("Type '/packs' to list world packs, '/switch' to change packs, or '/set-default-pack' to save your startup pack.")
    print("Type '/llm-status' to inspect translation-provider state or '/probe-llm' to verify a live call.")
    examples = PROMPT_EXAMPLES.get(state.world_pack_id or "", PROMPT_EXAMPLES[DEFAULT_WORLD_PACK])
    print("Try prompts like: " + ", ".join(f"'{example}'" for example in examples) + ".")
    print("Type '/3d <scene prompt>' to route a turn through the text-to-3d world lane.")
    print("After a /3d run, type '/movie' to export the captured session as a movie package.")
    print('Type \'/pipeline game "Demo" :: source text\' or \'/ingest-file movie "Demo" "<path>"\' to run the frontend pipeline shell.')
    print(f"Starting location: {state.player_state.current_location_id}")
    print("Narration mode: deterministic present.")
    if llm_runtime is None or not llm_runtime.requested:
        print("Pipeline translation: deterministic only.")
    elif llm_runtime.translation_provider is None:
        print("Pipeline translation: stability fallback (LLM requested, but environment is not configured).")
    else:
        print("Pipeline translation: bounded live extraction ready.")


if __name__ == "__main__":
    raise SystemExit(main())
