from __future__ import annotations

from copy import deepcopy

from story_forge.models import BoardInstallRecord, StoryState, utc_now
from story_forge.worldpacks import get_board_manifest, get_world_pack_manifest


def install_board(state: StoryState, pack_id: str) -> BoardInstallRecord:
    manifest = get_world_pack_manifest(pack_id)
    board_manifest = get_board_manifest(f"board.{pack_id}")
    if manifest is None or board_manifest is None:
        raise ValueError(f"World pack '{pack_id}' is not registered for board installation.")

    existing = state.installed_boards.get(board_manifest.board_id)
    if existing is not None:
        _ensure_installed_board_id(state, existing.board_id)
        return existing

    record = BoardInstallRecord(
        board_id=board_manifest.board_id,
        pack_id=pack_id,
        title=manifest.title,
        category=manifest.category,
        required_modules=list(board_manifest.required_modules),
        optional_modules=list(board_manifest.optional_modules),
    )
    state.installed_boards[record.board_id] = record
    _ensure_installed_board_id(state, record.board_id)
    state.board_runtime.install_log.append(
        f"{utc_now()} install {record.board_id} modules={','.join(record.required_modules)}"
    )
    state.updated_at = utc_now()
    return record


def mount_board(state: StoryState, pack_id: str) -> BoardInstallRecord:
    record = install_board(state, pack_id)
    previous_active = state.board_runtime.active_board_id
    state.board_runtime.mounted_board_id = record.board_id
    state.board_runtime.active_board_id = record.board_id
    if previous_active and previous_active != record.board_id:
        state.board_runtime.swap_count += 1
        state.board_runtime.install_log.append(
            f"{utc_now()} swap {previous_active} -> {record.board_id}"
        )
    else:
        state.board_runtime.install_log.append(f"{utc_now()} mount {record.board_id}")
    state.updated_at = utc_now()
    return record


def inherit_installed_boards(source_state: StoryState, target_state: StoryState) -> None:
    target_state.installed_boards = deepcopy(source_state.installed_boards)
    target_state.board_runtime.installed_board_ids = list(
        source_state.board_runtime.installed_board_ids
    )
    target_state.board_runtime.install_log = list(source_state.board_runtime.install_log)
    target_state.board_runtime.swap_count = source_state.board_runtime.swap_count


def clear_board_mount(state: StoryState) -> None:
    state.board_runtime.mounted_board_id = None
    state.board_runtime.active_board_id = None
    state.updated_at = utc_now()


def _ensure_installed_board_id(state: StoryState, board_id: str) -> None:
    if board_id not in state.board_runtime.installed_board_ids:
        state.board_runtime.installed_board_ids.append(board_id)
