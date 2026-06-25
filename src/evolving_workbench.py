"""Modular workbench adapted from the evolving_ai app shell."""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
import ast
from dataclasses import dataclass
from datetime import datetime
from src.datetime_compat import UTC
import json
import os
from pathlib import Path
import re
import threading
try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib
from typing import Any
from uuid import uuid4

PRIMARY_PROJECT_ENV = "AAIS_PRIMARY_PROJECT"
APPROVAL_AUDIT_FILENAME = "evolving-approval-audit.json"
MAX_SYMBOL_RESULTS = 40
MAX_REPO_MAP_NODES = 18

IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    ".runtime",
    ".local",
    ".pytest_cache",
    ".vercel",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    "_archives",
}

CODE_EXTENSIONS = {
    ".c",
    ".cpp",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".mjs",
    ".py",
    ".rs",
    ".ts",
    ".tsx",
}

SCRIPT_EXTENSIONS = {".js", ".jsx", ".mjs", ".ts", ".tsx"}
IMPORT_PATH_RE = re.compile(
    r"""(?x)
    (?:import\s+(?:.+?\s+from\s+)?|export\s+.+?\s+from\s+|require\s*\()\s*
    ["'](?P<path>[^"']+)["']
    """
)
JS_SYMBOL_PATTERNS = [
    ("class", re.compile(r"^\s*export\s+class\s+([A-Za-z_][A-Za-z0-9_]*)")),
    ("class", re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)")),
    ("function", re.compile(r"^\s*export\s+async\s+function\s+([A-Za-z_][A-Za-z0-9_]*)")),
    ("function", re.compile(r"^\s*export\s+function\s+([A-Za-z_][A-Za-z0-9_]*)")),
    ("function", re.compile(r"^\s*async\s+function\s+([A-Za-z_][A-Za-z0-9_]*)")),
    ("function", re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_]*)")),
    ("variable", re.compile(r"^\s*export\s+const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=")),
    ("variable", re.compile(r"^\s*const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=")),
]
WORD_RE = re.compile(r"[A-Za-z0-9_./-]+")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_posix_path(raw: str | Path | None) -> str:
    if raw is None:
        return ""
    return str(raw).replace("\\", "/").strip("/")


def _tokenize(text: str | None) -> list[str]:
    normalized = str(text or "").lower()
    return [token for token in WORD_RE.findall(normalized) if len(token) > 1]


def _unique_preserving_order(values: list[str], *, limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
        if limit is not None and len(ordered) >= limit:
            break
    return ordered


def _clip_text(text: str | None, *, limit: int = 180) -> str:
    value = str(text or "").strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)].rstrip() + "..."


def _extract_line_range(content: str, start_line: int, end_line: int) -> str:
    lines = content.splitlines()
    if not lines:
        return ""
    bounded_start = max(1, start_line)
    bounded_end = max(bounded_start, min(end_line, len(lines)))
    return "\n".join(lines[bounded_start - 1 : bounded_end])


def _is_test_path(path: str) -> bool:
    normalized = path.lower()
    name = Path(normalized).name
    return (
        "/tests/" in normalized
        or name.startswith("test_")
        or ".spec." in name
        or ".test." in name
        or name.endswith("_test.py")
    )


def _guess_test_files(path: str, files: list[str]) -> list[str]:
    normalized = _normalize_posix_path(path)
    if not normalized:
        return []
    path_obj = Path(normalized)
    stem = path_obj.stem
    suffix = path_obj.suffix
    parent = _normalize_posix_path(path_obj.parent)
    candidates: list[str] = []
    if suffix == ".py":
        candidates.extend(
            [
                _normalize_posix_path(path_obj.with_name(f"test_{stem}.py")),
                _normalize_posix_path(path_obj.with_name(f"{stem}_test.py")),
            ]
        )
        parts = path_obj.parts
        if len(parts) >= 2:
            project_root = parts[0]
            candidates.extend(
                [
                    f"{project_root}/tests/test_{stem}.py",
                    f"{project_root}/tests/{stem}_test.py",
                ]
            )
    elif suffix in SCRIPT_EXTENSIONS:
        base = _normalize_posix_path(path_obj.with_suffix(""))
        candidates.extend(
            [
                f"{base}.test{suffix}",
                f"{base}.spec{suffix}",
                _normalize_posix_path(Path(parent) / "__tests__" / f"{stem}.test{suffix}"),
            ]
        )
    visible = set(files)
    return [candidate for candidate in _unique_preserving_order(candidates) if candidate in visible]


@dataclass(slots=True)
class WorkspaceSymbolRecord:
    path: str
    name: str
    qualname: str
    kind: str
    line_start: int
    line_end: int
    signature: str
    content: str

    def payload(self, *, include_content: bool = False) -> dict[str, Any]:
        payload = {
            "path": self.path,
            "name": self.name,
            "qualname": self.qualname,
            "kind": self.kind,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "signature": self.signature,
        }
        if include_content:
            payload["content"] = self.content
        return payload


class EvolvingWorkspaceIntel:
    """Richer workspace inspection adapted from evolving_ai's workbench layer."""

    def __init__(self, workspace_root: str | Path | None = None):
        self.workspace_root = Path(workspace_root) if workspace_root else None

    def _resolve_workspace_root(self) -> Path:
        configured = os.getenv("AAIS_WORKSPACE_ROOT")
        if configured:
            return Path(configured).expanduser().resolve()
        if self.workspace_root is not None:
            return self.workspace_root.expanduser().resolve()
        return Path(__file__).resolve().parents[2]

    def _preferred_project_name(self) -> str:
        configured = str(os.getenv(PRIMARY_PROJECT_ENV, "")).strip()
        if configured:
            return configured
        try:
            workspace_root = self._resolve_workspace_root()
            if (workspace_root / "AAIS-main").is_dir():
                return "AAIS-main"
        except OSError:
            pass
        return Path(__file__).resolve().parents[1].name

    def _iter_visible_files(self) -> list[str]:
        root = self._resolve_workspace_root()
        visible: list[str] = []
        for current_root, dirs, files in os.walk(root):
            dirs[:] = [
                directory
                for directory in dirs
                if directory not in IGNORED_DIR_NAMES and not directory.startswith(".")
            ]
            for filename in files:
                path = Path(current_root) / filename
                relative = _normalize_posix_path(path.relative_to(root))
                if relative:
                    visible.append(relative)
        return sorted(visible)

    def _scope_prefix(self, files: list[str], path_prefix: str | None = None) -> str:
        requested = _normalize_posix_path(path_prefix)
        if requested:
            return requested
        preferred = self._preferred_project_name().lower()
        for path in files:
            project = path.split("/", 1)[0].lower()
            if project == preferred:
                return path.split("/", 1)[0]
        return ""

    def _scoped_files(
        self,
        *,
        files: list[str] | None = None,
        path_prefix: str | None = None,
        code_only: bool = False,
    ) -> tuple[list[str], str]:
        all_files = files or self._iter_visible_files()
        scope_prefix = self._scope_prefix(all_files, path_prefix)
        scoped = [
            path
            for path in all_files
            if not scope_prefix or path == scope_prefix or path.startswith(f"{scope_prefix}/")
        ]
        if code_only:
            scoped = [path for path in scoped if Path(path).suffix.lower() in CODE_EXTENSIONS]
        return scoped, scope_prefix

    def _read_text(self, relative_path: str) -> str | None:
        root = self._resolve_workspace_root()
        target = (root / relative_path).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            return None
        if not target.exists() or not target.is_file():
            return None
        try:
            return target.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None

    def _symbol_records(self, *, path_prefix: str | None = None) -> list[WorkspaceSymbolRecord]:
        files, _ = self._scoped_files(path_prefix=path_prefix, code_only=True)
        records: list[WorkspaceSymbolRecord] = []
        for relative_path in files:
            content = self._read_text(relative_path)
            if not content:
                continue
            suffix = Path(relative_path).suffix.lower()
            if suffix == ".py":
                records.extend(_extract_python_symbols(relative_path, content))
            elif suffix in SCRIPT_EXTENSIONS:
                records.extend(_extract_script_symbols(relative_path, content))
        return records

    def list_symbols(
        self,
        *,
        query: str | None = None,
        limit: int = 16,
        path_prefix: str | None = None,
    ) -> dict[str, Any]:
        normalized_query = " ".join(str(query or "").split()).lower()
        query_tokens = _tokenize(normalized_query)
        capped_limit = min(max(1, int(limit or 16)), MAX_SYMBOL_RESULTS)
        records = self._symbol_records(path_prefix=path_prefix)
        if query_tokens:
            ranked: list[tuple[int, int, int, int, WorkspaceSymbolRecord]] = []
            for record in records:
                haystack = " ".join(
                    [
                        record.name.lower(),
                        record.qualname.lower(),
                        record.signature.lower(),
                        record.path.lower(),
                        record.content.lower(),
                    ]
                )
                score = sum(token in haystack for token in query_tokens)
                if score <= 0:
                    continue
                exact_match = int(
                    normalized_query in {record.name.lower(), record.qualname.lower()}
                )
                implementation_bias = 0 if _is_test_path(record.path) else 1
                ranked.append(
                    (
                        score,
                        exact_match,
                        implementation_bias,
                        -len(record.qualname),
                        record,
                    )
                )
            ranked.sort(
                key=lambda item: (
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                    item[4].path,
                ),
                reverse=True,
            )
            records = [record for *_, record in ranked]
        return _wrap_ul_payload({
            "ok": True,
            "query": normalized_query,
            "path_prefix": self._scope_prefix(self._iter_visible_files(), path_prefix),
            "limit": capped_limit,
            "symbol_count": len(records[:capped_limit]),
            "symbols": [record.payload() for record in records[:capped_limit]],
        })

    def read_symbol(
        self,
        *,
        symbol: str,
        path: str | None = None,
        path_prefix: str | None = None,
    ) -> dict[str, Any]:
        normalized_symbol = " ".join(str(symbol or "").split()).lower()
        if not normalized_symbol:
            raise ValueError("`symbol` is required.")
        candidates = self._symbol_records(path_prefix=path_prefix)
        if path:
            normalized_path = _normalize_posix_path(path)
            candidates = [record for record in candidates if record.path == normalized_path]
        exact = [
            record
            for record in candidates
            if normalized_symbol in {record.name.lower(), record.qualname.lower()}
        ]
        record = None
        if exact:
            record = exact[0]
        elif candidates:
            ranked = sorted(
                candidates,
                key=lambda item: (
                    normalized_symbol in item.qualname.lower(),
                    normalized_symbol in item.name.lower(),
                    normalized_symbol in item.signature.lower(),
                    normalized_symbol in item.content.lower(),
                ),
                reverse=True,
            )
            record = ranked[0]
        if record is None or normalized_symbol not in (
            record.name.lower(),
            record.qualname.lower(),
            record.signature.lower(),
            record.content.lower(),
        ):
            raise FileNotFoundError(f"Symbol `{symbol}` was not found.")
        return _wrap_ul_payload({"ok": True, "symbol": record.payload(include_content=True)})

    def inspect_repo_map(
        self,
        *,
        goal: str | None = None,
        focus_path: str | None = None,
        symbol: str | None = None,
        limit: int = 12,
        path_prefix: str | None = None,
    ) -> dict[str, Any]:
        files, scope_prefix = self._scoped_files(path_prefix=path_prefix, code_only=True)
        file_set = set(files)
        contents: dict[str, str] = {}
        symbols_by_path: dict[str, list[WorkspaceSymbolRecord]] = {}
        outgoing: dict[str, set[str]] = {}
        incoming: dict[str, set[str]] = {}
        for relative_path in files:
            content = self._read_text(relative_path)
            if not content:
                continue
            contents[relative_path] = content
            suffix = Path(relative_path).suffix.lower()
            if suffix == ".py":
                symbols = _extract_python_symbols(relative_path, content)
                imports = _extract_python_import_targets(relative_path, content, file_set)
            else:
                symbols = _extract_script_symbols(relative_path, content)
                imports = _extract_script_import_targets(relative_path, content, file_set)
            symbols_by_path[relative_path] = symbols
            if not imports:
                continue
            outgoing[relative_path] = set(imports)
            for target in imports:
                incoming.setdefault(target, set()).add(relative_path)

        goal_tokens = _tokenize(goal)
        focus_paths: list[str] = []
        normalized_focus = _normalize_posix_path(focus_path)
        if normalized_focus in contents:
            focus_paths.append(normalized_focus)
        if symbol:
            try:
                symbol_payload = self.read_symbol(symbol=symbol, path_prefix=scope_prefix)
                symbol_path = str((symbol_payload.get("symbol") or {}).get("path") or "").strip()
                if symbol_path and symbol_path in contents:
                    focus_paths.append(symbol_path)
            except FileNotFoundError:
                pass
        if not focus_paths and goal_tokens:
            scored = sorted(
                contents,
                key=lambda path: (
                    sum(token in path.lower() for token in goal_tokens)
                    + sum(token in contents[path].lower() for token in goal_tokens),
                    path,
                ),
                reverse=True,
            )
            focus_paths.extend(scored[:2])
        if not focus_paths and contents:
            focus_paths.append(next(iter(sorted(contents))))

        focus_paths = _unique_preserving_order([path for path in focus_paths if path in contents], limit=3)
        related_paths: list[str] = []
        for path in focus_paths:
            related_paths.extend(sorted(outgoing.get(path, set())))
            related_paths.extend(sorted(incoming.get(path, set())))
        likely_test_files = _unique_preserving_order(
            [candidate for path in [*focus_paths, *related_paths] for candidate in _guess_test_files(path, files)],
            limit=6,
        )
        included_paths = _unique_preserving_order(
            [
                *focus_paths,
                *related_paths,
                *likely_test_files,
                *sorted(
                    contents,
                    key=lambda item: (
                        len(outgoing.get(item, set())) + len(incoming.get(item, set())) + len(symbols_by_path.get(item, [])),
                        item,
                    ),
                    reverse=True,
                ),
            ],
            limit=min(max(4, int(limit or 12)), MAX_REPO_MAP_NODES),
        )
        included_set = set(included_paths)
        nodes = [
            {
                "path": path,
                "language": Path(path).suffix.lower().lstrip("."),
                "symbol_count": len(symbols_by_path.get(path, [])),
                "import_count": len(outgoing.get(path, set())),
                "imported_by_count": len(incoming.get(path, set())),
                "is_test": _is_test_path(path),
            }
            for path in included_paths
        ]
        edges = [
            {"source": source, "target": target}
            for source in included_paths
            for target in sorted(outgoing.get(source, set()))
            if target in included_set
        ]
        summary_parts = []
        if focus_paths:
            summary_parts.append(f"Focus: {', '.join(focus_paths[:3])}.")
        if related_paths:
            summary_parts.append(f"Related: {', '.join(_unique_preserving_order(related_paths, limit=4))}.")
        if likely_test_files:
            summary_parts.append(f"Likely tests: {', '.join(likely_test_files[:3])}.")
        return _wrap_ul_payload({
            "ok": True,
            "scope_prefix": scope_prefix,
            "goal": " ".join(str(goal or "").split()),
            "focus_paths": focus_paths,
            "related_paths": _unique_preserving_order(related_paths, limit=8),
            "likely_test_files": likely_test_files,
            "summary": " ".join(summary_parts).strip(),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
        })

    def detect_project_profile(self, *, path_prefix: str | None = None) -> dict[str, Any]:
        files = self._iter_visible_files()
        scoped_files, scope_prefix = self._scoped_files(files=files, path_prefix=path_prefix)
        lower_files = {path.lower(): path for path in scoped_files}
        pyproject_path = lower_files.get(_normalize_posix_path(f"{scope_prefix}/pyproject.toml").lower()) or lower_files.get("pyproject.toml")
        requirements_path = lower_files.get(_normalize_posix_path(f"{scope_prefix}/requirements.txt").lower()) or lower_files.get("requirements.txt")
        package_json_path = lower_files.get(_normalize_posix_path(f"{scope_prefix}/package.json").lower()) or lower_files.get("package.json")
        pyproject_text = self._read_text(pyproject_path) if pyproject_path else None
        requirements_text = self._read_text(requirements_path) if requirements_path else None
        package_json_text = self._read_text(package_json_path) if package_json_path else None
        package_json = _parse_json(package_json_text)
        pyproject = _parse_toml(pyproject_text)

        languages: list[str] = []
        frameworks: list[str] = []
        package_managers: list[str] = []
        install_commands: list[str] = []
        test_commands: list[str] = []
        lint_commands: list[str] = []
        run_commands: list[str] = []
        entrypoints: list[str] = []
        signals: list[str] = []

        has_python = any(path.endswith(".py") for path in scoped_files) or bool(pyproject_text or requirements_text)
        has_node = any(Path(path).suffix.lower() in SCRIPT_EXTENSIONS for path in scoped_files) or bool(package_json)

        if has_python:
            languages.append("python")
            signals.append("Detected Python sources or packaging files.")
            if pyproject_text:
                package_managers.append("pyproject")
                install_commands.append("python -m pip install -e .")
            elif requirements_text:
                package_managers.append("pip")
                install_commands.append("python -m pip install -r requirements.txt")
            if "pytest" in (requirements_text or "").lower() or any("/tests/" in f"/{path.lower()}/" for path in scoped_files):
                test_commands.append("pytest -q")
            if "ruff" in (pyproject_text or "").lower():
                lint_commands.append("ruff check .")
            if "flask" in (requirements_text or "").lower() or "flask" in json.dumps(pyproject).lower():
                frameworks.append("flask")
            if any(path.endswith("src/api.py") for path in scoped_files):
                entrypoints.append(_first_matching(scoped_files, "src/api.py"))
                run_commands.append("python src/api.py")

        if has_node:
            languages.append("javascript")
            signals.append("Detected Node or frontend assets.")
            package_manager = _detect_node_package_manager(scoped_files)
            package_managers.append(package_manager)
            install_commands.append(_install_command_for_package_manager(package_manager))
            dependencies = _package_json_dependencies(package_json)
            scripts = (package_json or {}).get("scripts") or {}
            if "react" in dependencies:
                frameworks.append("react")
            if "vite" in dependencies or "vite.config.ts" in lower_files or "vite.config.js" in lower_files:
                frameworks.append("vite")
            if scripts.get("test"):
                test_commands.append(f"{package_manager} run test")
            if scripts.get("build"):
                run_commands.append(f"{package_manager} run build")
            if scripts.get("dev"):
                run_commands.append(f"{package_manager} run dev")
            if "frontend/package.json" in lower_files:
                entrypoints.append(lower_files["frontend/package.json"])

        return _wrap_ul_payload({
            "ok": True,
            "scope_prefix": scope_prefix,
            "languages": _unique_preserving_order(languages),
            "frameworks": _unique_preserving_order(frameworks),
            "package_managers": _unique_preserving_order(package_managers),
            "install_commands": _unique_preserving_order(install_commands),
            "test_commands": _unique_preserving_order(test_commands),
            "lint_commands": _unique_preserving_order(lint_commands),
            "run_commands": _unique_preserving_order(run_commands),
            "entrypoints": _unique_preserving_order(entrypoints),
            "signals": _unique_preserving_order(signals, limit=10),
            "file_count": len(scoped_files),
        })


class EvolvingApprovalAuditStore:
    """Durable approval/execution audit adapted from evolving_ai approval state."""

    def __init__(self, runtime_dir: str | Path | None = None):
        self.runtime_dir = Path(runtime_dir) if runtime_dir else None
        self._lock = threading.Lock()

    def configure_runtime_dir(self, runtime_dir: str | Path | None) -> None:
        self.runtime_dir = Path(runtime_dir) if runtime_dir else None

    def _resolve_path(self) -> Path:
        if self.runtime_dir is not None:
            runtime_root = self.runtime_dir.expanduser().resolve()
        else:
            runtime_root = Path(__file__).resolve().parents[1] / ".runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        return runtime_root / APPROVAL_AUDIT_FILENAME

    def _load_payload(self) -> dict[str, Any]:
        path = self._resolve_path()
        if not path.exists():
            return _wrap_ul_payload({"entries": [], "sessions": {}})
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return _wrap_ul_payload({"entries": [], "sessions": {}})
        if isinstance(payload, list):
            return _wrap_ul_payload({
                "entries": [entry for entry in payload if isinstance(entry, dict)],
                "sessions": {},
            })
        if not isinstance(payload, dict):
            return _wrap_ul_payload({"entries": [], "sessions": {}})
        entries = payload.get("entries")
        if not isinstance(entries, list):
            entries = []
        sessions = payload.get("sessions")
        if not isinstance(sessions, dict):
            sessions = {}
        normalized_sessions: dict[str, Any] = {}
        for session_id, snapshot in sessions.items():
            if not isinstance(snapshot, dict):
                continue
            normalized_sessions[str(session_id)] = {
                "pending_action": (
                    dict(snapshot.get("pending_action"))
                    if isinstance(snapshot.get("pending_action"), dict)
                    else None
                ),
                "action_lifecycle": (
                    dict(snapshot.get("action_lifecycle"))
                    if isinstance(snapshot.get("action_lifecycle"), dict)
                    else None
                ),
                "updated_at": str(snapshot.get("updated_at") or ""),
            }
        return _wrap_ul_payload({
            "entries": [entry for entry in entries if isinstance(entry, dict)],
            "sessions": normalized_sessions,
        })

    def _load_entries(self) -> list[dict[str, Any]]:
        return self._load_payload().get("entries", [])

    def _save_payload(self, payload: dict[str, Any]) -> None:
        path = self._resolve_path()
        path.write_text(
            json.dumps(
                {
                    "entries": list(payload.get("entries", []))[-2000:],
                    "sessions": dict(payload.get("sessions", {})),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def _save_entries(self, entries: list[dict[str, Any]]) -> None:
        payload = self._load_payload()
        payload["entries"] = entries
        self._save_payload(payload)

    def append(self, *, session_id: str, lifecycle: dict[str, Any]) -> dict[str, Any]:
        action_instance_id = str(lifecycle.get("action_instance_id") or "").strip()
        stage = str(lifecycle.get("stage") or "").strip()
        if not session_id or not action_instance_id or not stage:
            raise ValueError("Approval audit requires session_id, action_instance_id, and stage.")
        timestamp = str(lifecycle.get(f"{stage}_at") or lifecycle.get("updated_at") or _utc_now())
        entry = {
            "id": uuid4().hex,
            "session_id": session_id,
            "action_instance_id": action_instance_id,
            "action_id": lifecycle.get("action_id"),
            "action_label": lifecycle.get("action_label"),
            "stage": stage,
            "approval_state": lifecycle.get("approval_state"),
            "execution_state": lifecycle.get("execution_state"),
            "source": lifecycle.get("source"),
            "result_status": lifecycle.get("result_status"),
            "exit_code": lifecycle.get("exit_code"),
            "error": lifecycle.get("error"),
            "created_at": timestamp,
        }
        with self._lock:
            payload = self._load_payload()
            entries = payload.get("entries", [])
            if entries:
                latest = entries[-1]
                if (
                    latest.get("session_id") == session_id
                    and latest.get("action_instance_id") == action_instance_id
                    and latest.get("stage") == stage
                ):
                    return latest
            entries.append(entry)
            payload["entries"] = entries
            self._save_payload(payload)
        return entry

    def list(self, *, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        capped_limit = min(max(1, int(limit or 20)), 100)
        with self._lock:
            entries = self._load_payload().get("entries", [])
        filtered = [entry for entry in entries if entry.get("session_id") == session_id]
        filtered.sort(
            key=lambda item: (str(item.get("created_at") or ""), str(item.get("id") or "")),
            reverse=True,
        )
        return filtered[:capped_limit]

    def sync_current(
        self,
        *,
        session_id: str,
        pending_action: dict[str, Any] | None,
        action_lifecycle: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not session_id:
            return None
        snapshot = {
            "pending_action": dict(pending_action) if isinstance(pending_action, dict) else None,
            "action_lifecycle": dict(action_lifecycle) if isinstance(action_lifecycle, dict) else None,
            "updated_at": _utc_now(),
        }
        with self._lock:
            payload = self._load_payload()
            sessions = dict(payload.get("sessions") or {})
            if snapshot["pending_action"] is None and snapshot["action_lifecycle"] is None:
                sessions.pop(session_id, None)
                payload["sessions"] = sessions
                self._save_payload(payload)
                return None
            sessions[session_id] = snapshot
            payload["sessions"] = sessions
            self._save_payload(payload)
        return snapshot

    def get_current(self, *, session_id: str) -> dict[str, Any] | None:
        if not session_id:
            return None
        with self._lock:
            payload = self._load_payload()
        snapshot = (payload.get("sessions") or {}).get(session_id)
        if not isinstance(snapshot, dict):
            return None
        return dict(snapshot)


def _extract_python_symbols(path: str, content: str) -> list[WorkspaceSymbolRecord]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    records: list[WorkspaceSymbolRecord] = []
    lines = content.splitlines()

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.class_stack: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            qualname = ".".join([*self.class_stack, node.name])
            signature = lines[node.lineno - 1].strip() if 0 < node.lineno <= len(lines) else f"class {node.name}"
            records.append(
                WorkspaceSymbolRecord(
                    path=path,
                    name=node.name,
                    qualname=qualname,
                    kind="class",
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    signature=signature,
                    content=_extract_line_range(content, node.lineno, getattr(node, "end_lineno", node.lineno)),
                )
            )
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, *, async_kind: bool) -> None:
            qualname = ".".join([*self.class_stack, node.name]) if self.class_stack else node.name
            signature = lines[node.lineno - 1].strip() if 0 < node.lineno <= len(lines) else node.name
            kind = "method" if self.class_stack else ("async_function" if async_kind else "function")
            records.append(
                WorkspaceSymbolRecord(
                    path=path,
                    name=node.name,
                    qualname=qualname,
                    kind=kind,
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    signature=signature,
                    content=_extract_line_range(content, node.lineno, getattr(node, "end_lineno", node.lineno)),
                )
            )
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._visit_function(node, async_kind=False)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._visit_function(node, async_kind=True)

    Visitor().visit(tree)
    return records


def _extract_script_symbols(path: str, content: str) -> list[WorkspaceSymbolRecord]:
    records: list[WorkspaceSymbolRecord] = []
    for line_number, line in enumerate(content.splitlines(), 1):
        for kind, pattern in JS_SYMBOL_PATTERNS:
            match = pattern.match(line)
            if not match:
                continue
            name = match.group(1)
            records.append(
                WorkspaceSymbolRecord(
                    path=path,
                    name=name,
                    qualname=name,
                    kind=kind,
                    line_start=line_number,
                    line_end=line_number,
                    signature=line.strip(),
                    content=line.strip(),
                )
            )
            break
    return records


def _extract_python_import_targets(source_path: str, content: str, available_paths: set[str]) -> list[str]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    source_dir = Path(source_path).parent
    targets: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.extend(_resolve_python_module_candidates(alias.name, source_dir, available_paths, level=0))
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            targets.extend(
                _resolve_python_module_candidates(
                    module_name,
                    source_dir,
                    available_paths,
                    level=int(node.level or 0),
                )
            )
    return _unique_preserving_order(targets)


def _resolve_python_module_candidates(
    module_name: str,
    source_dir: Path,
    available_paths: set[str],
    *,
    level: int,
) -> list[str]:
    normalized = str(module_name or "").strip(".")
    base_dir = source_dir
    if level > 0:
        for _ in range(max(0, level - 1)):
            base_dir = base_dir.parent
    if normalized:
        relative = Path(*normalized.split("."))
        candidates = [
            _normalize_posix_path(base_dir / relative.with_suffix(".py")),
            _normalize_posix_path(base_dir / relative / "__init__.py"),
        ]
    else:
        candidates = [_normalize_posix_path(base_dir / "__init__.py")]
    if normalized and level == 0:
        project_root = Path(source_dir.parts[0]) if source_dir.parts else Path()
        candidates.extend(
            [
                _normalize_posix_path(Path(*normalized.split(".")).with_suffix(".py")),
                _normalize_posix_path(Path(*normalized.split(".")) / "__init__.py"),
                _normalize_posix_path(project_root / Path(*normalized.split(".")).with_suffix(".py")),
                _normalize_posix_path(project_root / Path(*normalized.split(".")) / "__init__.py"),
            ]
        )
    return [candidate for candidate in _unique_preserving_order(candidates) if candidate in available_paths]


def _extract_script_import_targets(source_path: str, content: str, available_paths: set[str]) -> list[str]:
    source_dir = Path(source_path).parent
    targets: list[str] = []
    for match in IMPORT_PATH_RE.finditer(content):
        raw = str(match.group("path") or "").strip()
        if not raw.startswith("."):
            continue
        targets.extend(_resolve_script_path_candidates(raw, source_dir, available_paths))
    return _unique_preserving_order(targets)


def _resolve_script_path_candidates(raw: str, source_dir: Path, available_paths: set[str]) -> list[str]:
    base = (source_dir / raw).as_posix()
    if raw.endswith(tuple(CODE_EXTENSIONS)):
        normalized = _normalize_posix_path(base)
        return [normalized] if normalized in available_paths else []
    candidates = []
    for suffix in sorted(SCRIPT_EXTENSIONS):
        candidates.append(_normalize_posix_path(f"{base}{suffix}"))
        candidates.append(_normalize_posix_path(f"{base}/index{suffix}"))
    return [candidate for candidate in _unique_preserving_order(candidates) if candidate in available_paths]


def _parse_json(content: str | None) -> dict[str, Any]:
    if not content:
        return _wrap_ul_payload({})
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return _wrap_ul_payload({})
    return payload if isinstance(payload, dict) else {}


def _parse_toml(content: str | None) -> dict[str, Any]:
    if not content:
        return _wrap_ul_payload({})
    try:
        payload = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        return _wrap_ul_payload({})
    return payload if isinstance(payload, dict) else {}


def _package_json_dependencies(payload: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        section = payload.get(key) or {}
        if isinstance(section, dict):
            names.update(str(name).lower() for name in section.keys())
    return names


def _detect_node_package_manager(files: list[str]) -> str:
    lower_files = {path.lower() for path in files}
    if any(path.endswith("pnpm-lock.yaml") for path in lower_files):
        return "pnpm"
    if any(path.endswith("yarn.lock") for path in lower_files):
        return "yarn"
    return "npm"


def _install_command_for_package_manager(package_manager: str) -> str:
    if package_manager == "pnpm":
        return "pnpm install"
    if package_manager == "yarn":
        return "yarn install"
    return "npm install"


def _first_matching(files: list[str], suffix: str) -> str:
    normalized_suffix = _normalize_posix_path(suffix).lower()
    for path in files:
        if path.lower().endswith(normalized_suffix):
            return path
    return suffix
