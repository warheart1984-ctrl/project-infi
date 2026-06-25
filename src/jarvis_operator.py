"""Persistent Jarvis memory and safe local workspace tools."""

# Mythic: Jarvis Operator Organ
# Engineering: JarvisOperatorEngine
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from src.datetime_compat import UTC
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
from typing import Any
import uuid

from src.jarvis_reasoning_protocol import build_otem_result, detect_otem, generate_otem_reason_only_answer_with_context
from src.jarvis_memory_board import (
    MemoryModule,
    build_default_memory_controller,
    build_memory_board_snapshot,
)
from src.logger import get_logger
from src.capability_service_bridge import CapabilityServiceBridge
from src.change_scope import ChangeScope
from src.evolve_client import evolve_client
from src.evolving_workbench import EvolvingApprovalAuditStore, EvolvingWorkspaceIntel
from src.forge_client import auto_approve_forge_result, forge_client
from src.forge_eval_client import forge_eval_client
from src.memory_smith import MemorySmith
from src.memory_board_enforcer import (
    MemoryBoardBypassError,
    MemoryBoardEnforcer,
    MemoryBoardEnforcerError,
)
from src.mystic_engine import extract_mystic_prompt, mystic_engine
from src.patchforge import PatchForge
from src.patch_apply_engine import PatchApplyEngine
from src.patch_execution_preview import PatchExecutionPreview
from src.patch_review_store import PatchReviewStore
from src.project_infi_law import ProjectInfiLaw
from src.forge_repo_governance import (
    build_forge_contractor_payload,
    build_forge_eval_payload,
    finalize_contractor_runtime_action,
    govern_evolution_job_payload,
    govern_patch_review_record,
    infer_forge_cisiv_stage as _infer_forge_cisiv_stage,
    infer_patch_review_cisiv_stage,
    wrap_contractor_governed_payload,
)
from src.provider_mind import ProviderMind
from src.run_ledger import RunLedger
from src.Spatial_reasoning import SpatialReasoningPlug
from src.otem_runtime import (
    OTEM_VERSION,
    build_otem_catalog_snapshot,
    build_tool_registry,
    classify_otem_operation,
    enrich_otem_result,
    get_frozen_otem_version,
    load_workflow_template_catalog,
)
from src.state_hygiene import (
    filter_operator_records,
    normalize_truth_scope,
    project_record,
    summarize_records,
)
from src.test_oracle import TestOracle
from src.v9_core import extract_v9_core_prompt, v9_core_engine
from src.v9_runtime import v9_runtime
from src.v10_core import extract_v10_core_prompt, v10_core_engine
from src.v10_runtime import v10_runtime

logger = get_logger(__name__)

MEMORY_PATH_ENV = "AAIS_JARVIS_MEMORY_PATH"
WORKSPACE_ROOT_ENV = "AAIS_WORKSPACE_ROOT"
PRIMARY_PROJECT_ENV = "AAIS_PRIMARY_PROJECT"
DEFAULT_MEMORY_FILENAME = "jarvis_memory.json"
MAX_FILE_BYTES = 256 * 1024
MAX_FILE_CHARS = 6000
MEMORY_REJECTION_REASONS = {
    "none",
    "canonical_protection",
    "truth_scope_violation",
    "state_class_mismatch",
    "inactive_memory",
    "conflict",
    "rejected",
    "no_action",
    "terminal_rejection",
}
MEMORY_REJECTION_NEXT_STEPS = {
    "use_session_scope",
    "request_operator_override",
    "submit_conflict_pair",
    "review_canonical_memory",
    "none",
    "no_next_step",
}
MEMORY_STORE_PREFIXES = (
    "remember that ",
    "remember ",
    "store this:",
    "store this ",
    "store memory:",
    "store memory ",
)


def _normalize_repo_path(value: str | None) -> str:
    return str(value or "").strip().replace("\\", "/").lstrip("./")


def _normalize_repo_path_list(items: list[str] | None) -> list[str]:
    return [
        _normalize_repo_path(item)
        for item in list(items or [])
        if _normalize_repo_path(item)
    ]


def _repo_path_matches_rule(path: str, rule: str) -> bool:
    normalized_path = _normalize_repo_path(path).lower()
    normalized_rule = _normalize_repo_path(rule).lower()
    if not normalized_path or not normalized_rule:
        return False
    if any(token in normalized_rule for token in "*?[]"):
        return fnmatch.fnmatch(normalized_path, normalized_rule)
    return normalized_path == normalized_rule or normalized_path.startswith(f"{normalized_rule}/")


def _repo_path_is_allowed(
    path: str,
    *,
    allowlist: list[str] | None = None,
    denylist: list[str] | None = None,
    max_directory_depth: int | None = None,
) -> bool:
    normalized_path = _normalize_repo_path(path)
    if not normalized_path:
        return False
    if max_directory_depth is not None:
        depth = max(0, len([part for part in normalized_path.split("/") if part]) - 1)
        if depth > max(0, int(max_directory_depth)):
            return False
    if denylist and any(_repo_path_matches_rule(normalized_path, rule) for rule in denylist):
        return False
    if allowlist:
        return any(_repo_path_matches_rule(normalized_path, rule) for rule in allowlist)
    return True


def _infer_action_cisiv_stage(action_id: str | None) -> str:
    from src.cisiv import normalize_cisiv_stage

    normalized = _normalize_action_id(action_id)
    if normalized in {"run_pytest"}:
        return normalize_cisiv_stage("verification")
    return normalize_cisiv_stage("implementation")


def _filter_workspace_context_for_forge(
    workspace_context: dict | None,
    *,
    allowlist: list[str] | None = None,
    denylist: list[str] | None = None,
    max_directory_depth: int | None = None,
    max_files_to_inspect: int | None = None,
) -> dict:
    context = dict(workspace_context or {})
    limit = max(1, int(max_files_to_inspect)) if max_files_to_inspect is not None else None
    filtered_files = []
    for file_payload in list(context.get("files") or []):
        path = str(file_payload.get("relative_path") or file_payload.get("path") or "").strip()
        if not _repo_path_is_allowed(
            path,
            allowlist=allowlist,
            denylist=denylist,
            max_directory_depth=max_directory_depth,
        ):
            continue
        filtered_files.append(dict(file_payload))
        if limit is not None and len(filtered_files) >= limit:
            break
    filtered_results = []
    for result in list(context.get("results") or []):
        path = str(result.get("relative_path") or result.get("path") or "").strip()
        if not _repo_path_is_allowed(
            path,
            allowlist=allowlist,
            denylist=denylist,
            max_directory_depth=max_directory_depth,
        ):
            continue
        filtered_results.append(dict(result))
        if limit is not None and len(filtered_results) >= max(limit * 2, limit):
            break
    context["files"] = filtered_files
    if "results" in context:
        context["results"] = filtered_results
    return context
MEMORY_GOVERNED_DOMAIN_TERMS = (
    "workspace",
    "repo",
    "repository",
    "project",
    "api",
    "endpoint",
    "route",
    "filesystem",
    "memory bank",
    "workbench",
    "mission board",
    "governance",
    "provider",
    "runtime",
    "session",
    "run ledger",
    "patch review",
)
MEMORY_GOVERNED_ASSERTION_TERMS = (
    " is ",
    " are ",
    " was ",
    " were ",
    "read-only",
    "readonly",
    "writable",
    "writeable",
    "disabled",
    "enabled",
)
MEMORY_PREFERENCE_TERMS = (
    "my ",
    "i prefer",
    "prefer ",
    "keep ",
    "use ",
    "default ",
    "default to",
    "jarvis should",
    "jarvis must",
    "voice mode",
    "local first",
    "local-first",
    "private",
    "step by step",
)

IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    ".venv-py314-backup",
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

TEXT_EXTENSIONS = {
    ".bat",
    ".c",
    ".cfg",
    ".conf",
    ".cpp",
    ".css",
    ".csv",
    ".env",
    ".gitignore",
    ".go",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".sh",
    ".sql",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

WORKSPACE_QUERY_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "coding",
    "does",
    "for",
    "from",
    "help",
    "how",
    "i",
    "if",
    "in",
    "into",
    "it",
    "jarvis",
    "like",
    "make",
    "me",
    "my",
    "need",
    "of",
    "on",
    "please",
    "project",
    "question",
    "should",
    "so",
    "tell",
    "that",
    "the",
    "this",
    "to",
    "use",
    "we",
    "what",
    "where",
    "why",
    "with",
    "would",
    "you",
}

CODING_HINTS = {
    "api",
    "app",
    "backend",
    "bug",
    "build",
    "class",
    "code",
    "component",
    "console",
    "css",
    "debug",
    "endpoint",
    "error",
    "feature",
    "file",
    "fix",
    "flask",
    "frontend",
    "function",
    "implement",
    "jarvis",
    "jsx",
    "module",
    "page",
    "python",
    "react",
    "refactor",
    "repo",
    "route",
    "screen",
    "script",
    "session",
    "test",
    "tsx",
    "ui",
    "wire",
}

CODING_ACTION_HINTS = {
    "build",
    "debug",
    "explain",
    "find",
    "fix",
    "implement",
    "open",
    "read",
    "review",
    "search",
    "show",
    "trace",
    "understand",
    "update",
    "wire",
}

WORKSPACE_FILE_PATTERN = re.compile(
    r"[\w./-]+\.(?:py|js|jsx|ts|tsx|css|html|json|md|txt|ps1|yml|yaml|toml|sql)"
)

WORKSPACE_OPT_OUT_HINTS = (
    "don't search my files",
    "do not search my files",
    "without searching the workspace",
    "without workspace context",
    "no workspace search",
)

LIVE_INFO_HINTS = (
    "latest",
    "recent",
    "current",
    "news",
    "docs",
    "documentation",
    "changelog",
)

MAX_CONTEXT_RESULTS = 6
MAX_CONTEXT_FILES = 3
MAX_CONTEXT_FILE_CHARS = 900
MAX_ACTION_OUTPUT_CHARS = 5000
MAX_FORGE_CONTEXT_FILES = 6
MAX_FORGE_CONTEXT_FILE_CHARS = 3200
DEFAULT_FORGE_MAX_OUTPUT_CHARS = 20000
DEFAULT_EVOLVE_PRESET = "prompt_polish"

EVOLVE_PRESET_LIBRARY = {
    "prompt_polish": {
        "evaluation": {
            "mode": "forge_eval",
            "forge_eval_mode": "llm_rubric",
            "candidate_field": "program",
            "payload": {
                "config": {
                    "criteria": [
                        "task alignment",
                        "clarity",
                        "bounded improvement",
                    ]
                }
            },
        },
        "constraints": {
            "population_size": 4,
            "max_generations": 3,
        },
    },
    "code_refine": {
        "evaluation": {
            "mode": "forge_eval",
            "forge_eval_mode": "llm_rubric",
            "candidate_field": "program",
            "payload": {
                "config": {
                    "criteria": [
                        "correctness",
                        "minimal safe scope",
                        "readability",
                        "testability",
                    ]
                }
            },
        },
        "constraints": {
            "population_size": 4,
            "max_generations": 3,
        },
    },
    "debug_triage": {
        "evaluation": {
            "mode": "forge_eval",
            "forge_eval_mode": "llm_rubric",
            "candidate_field": "program",
            "payload": {
                "config": {
                    "criteria": [
                        "failure isolation",
                        "next-step usefulness",
                        "bounded reasoning",
                    ]
                }
            },
        },
        "constraints": {
            "population_size": 3,
            "max_generations": 2,
        },
    },
}

FORGE_LANGUAGE_BY_EXTENSION = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".json": "json",
    ".md": "markdown",
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
}

FORGE_EXECUTION_PHRASES = (
    "have forge build",
    "send to forge",
    "run forge",
    "forge this",
    "use forge for this",
    "let forge handle",
    "give this to forge",
    "forge should build",
)

FORGE_EXECUTION_NEGATIONS = (
    "don't use forge",
    "dont use forge",
    "do not use forge",
    "what is forge",
)

LANE_OPERATOR = "OPERATOR"
LANE_JARVIS = "JARVIS"
LANE_BUILDER = "BUILDER"
LANE_FORGE = "FORGE"
LANE_FORGE_EVAL = "FORGE_EVAL"
LANE_SORVA = "SORVA"
LANE_AUTHORITY_ORDER = (
    LANE_OPERATOR,
    LANE_SORVA,
    LANE_JARVIS,
    LANE_BUILDER,
    LANE_FORGE_EVAL,
    LANE_FORGE,
)

ACTION_REQUEST_PATTERNS = {
    "git_status": (
        "git status",
        "show git status",
        "repo status",
        "show repo status",
        "show git changes",
        "show repo changes",
        "working tree",
    ),
    "run_pytest": (
        "run tests",
        "run pytest",
        "rerun pytest",
        "rerun tests",
        "run the tests",
        "test this",
        "test the project",
    ),
    "build_frontend": (
        "build frontend",
        "frontend build",
        "npm build",
        "compile frontend",
        "build the web app",
    ),
}

MODE_ACTION_HINTS = {
    "debug": {
        "run_pytest": (
            "failing",
            "pytest",
            "run pytest",
            "run tests",
            "stack trace",
            "traceback",
            "test",
            "tests",
            "verify",
            "verification",
        ),
    },
    "operator": {
        "git_status": (
            "branch",
            "changes",
            "git",
            "repo",
            "status",
            "working tree",
        ),
        "run_pytest": (
            "broken",
            "check",
            "debug",
            "error",
            "failing",
            "pytest",
            "run tests",
            "test",
            "verify",
        ),
        "build_frontend": (
            "build frontend",
            "bundle",
            "compile",
            "frontend",
            "ui",
            "web app",
            "website",
        ),
    },
}

SAFE_ACTIONS = {
    "git_status": {
        "id": "git_status",
        "label": "Git Status",
        "description": "Inspect local git changes in AAIS-main without modifying files.",
        "category": "workspace",
        "working_directory": ".",
        "requires_approval": True,
        "command_preview": "git status --short --branch",
        "timeout_seconds": 20,
    },
    "run_pytest": {
        "id": "run_pytest",
        "label": "Run Pytest",
        "description": "Run the backend test suite in the current AAIS-main workspace.",
        "category": "verification",
        "working_directory": ".",
        "requires_approval": True,
        "command_preview": f"{Path(sys.executable).name} -m pytest -q",
        "timeout_seconds": 180,
    },
    "build_frontend": {
        "id": "build_frontend",
        "label": "Build Frontend",
        "description": "Create a production frontend build to catch UI and bundling regressions.",
        "category": "verification",
        "working_directory": "frontend",
        "requires_approval": True,
        "command_preview": "npm run build",
        "timeout_seconds": 240,
    },
    "apply_patch_review": {
        "id": "apply_patch_review",
        "label": "Apply Approved Patch",
        "description": "Apply a review-approved patch plan to the current workspace.",
        "category": "workspace",
        "working_directory": ".",
        "requires_approval": True,
        "command_preview": "apply review-approved workspace patch",
        "timeout_seconds": 60,
        "listed": False,
    },
}

VISUAL_DEBUG_SIGNAL_PATTERNS = {
    "python_traceback": ("traceback", "exception", "line ", "module not found", "no module named"),
    "javascript_error": ("typeerror", "referenceerror", "syntaxerror", "npm err", "cannot read properties"),
    "build_failure": ("build failed", "compiled with problems", "failed to compile", "webpack", "vite"),
    "test_failure": ("assertionerror", "pytest", "test failed", "expected", "received"),
    "git_state": ("untracked", "modified:", "changes not staged", "ahead of", "behind"),
}

BROWSER_FAILURE_HINTS = (
    "404",
    "failed to compile",
    "not found",
    "something went wrong",
    "unexpected application error",
    "unhandled runtime error",
    "traceback",
    "exception",
)

BROWSER_ROUTE_EXPECTATIONS = (
    {
        "key": "jarvis_console",
        "label": "Jarvis Console",
        "paths": ("/", "/jarvis"),
        "preferred_components": ("JarvisConsole",),
        "expected_headings": ("Jarvis",),
        "expected_buttons": ("Send", "Verify Route"),
        "expected_keywords": ("browser verify", "v8 loop", "workspace tools", "long-term memory"),
    },
    {
        "key": "workbench",
        "label": "Jarvis Workbench",
        "paths": ("/workbench", "/dashboard"),
        "preferred_components": ("Dashboard",),
        "expected_headings": ("Jarvis Workbench",),
        "expected_buttons": ("Open Jarvis Console", "Review Local Settings"),
        "expected_keywords": ("tri-core", "tri core", "private local stack", "operator deck"),
    },
    {
        "key": "prompt_lab",
        "label": "Prompt Lab",
        "paths": ("/prompt-lab", "/text-generator"),
        "preferred_components": ("TextGenerator",),
        "expected_headings": ("Prompt Lab", "Text Generator"),
        "expected_buttons": ("Generate Text",),
        "expected_keywords": ("prompt", "temperature", "max length"),
    },
    {
        "key": "image_analyzer",
        "label": "Image Analyzer",
        "paths": ("/image-analyzer",),
        "preferred_components": ("ImageAnalyzer",),
        "expected_headings": ("Image Analyzer",),
        "expected_buttons": ("Analyze Image",),
        "expected_keywords": ("select image", "upload", "vision", "operator assist"),
    },
    {
        "key": "image_generator",
        "label": "Image Generator",
        "paths": ("/image-generator",),
        "preferred_components": ("ImageGenerator",),
        "expected_headings": ("Image Generator",),
        "expected_buttons": ("Generate Image",),
        "expected_keywords": ("prompt", "generation", "image"),
    },
    {
        "key": "audio_processor",
        "label": "Audio Processor",
        "paths": ("/audio-processor",),
        "preferred_components": ("AudioProcessor",),
        "expected_headings": ("Audio Processor",),
        "expected_buttons": ("Process Audio",),
        "expected_keywords": ("audio", "speech", "transcribe", "upload"),
    },
    {
        "key": "batch_processor",
        "label": "Batch Processor",
        "paths": ("/batch-processor",),
        "preferred_components": ("BatchProcessor",),
        "expected_headings": ("Batch Processor",),
        "expected_buttons": ("Run Batch",),
        "expected_keywords": ("batch", "grouped prompts", "compare"),
    },
    {
        "key": "history",
        "label": "Operator Log",
        "paths": ("/history",),
        "preferred_components": ("History",),
        "expected_headings": ("Operator Log",),
        "expected_buttons": ("Clear All",),
        "expected_keywords": ("private history", "jarvis chats", "prompt lab"),
    },
    {
        "key": "settings",
        "label": "Settings",
        "paths": ("/settings",),
        "preferred_components": ("Settings",),
        "expected_headings": ("Settings",),
        "expected_buttons": ("Save Settings", "Reset to Default"),
        "expected_keywords": ("api url", "default model", "default temperature"),
    },
)


def _utc_now():
    """Return an ISO timestamp in UTC."""
    return datetime.now(UTC).isoformat()


def _tokenize_query(text):
    """Tokenize a text query into lowercase alphanumeric parts."""
    return [token for token in re.findall(r"[a-z0-9_]+", str(text or "").lower()) if token]


def _normalize_browser_path(path: str | None):
    """Normalize a browser route path for expectation lookup."""
    raw = " ".join(str(path or "").split()).strip() or "/"
    if "://" in raw:
        raw = re.sub(r"^[a-z]+://[^/]+", "", raw, flags=re.IGNORECASE) or "/"
    raw = raw.split("#", 1)[0].split("?", 1)[0] or "/"
    if not raw.startswith("/"):
        raw = f"/{raw}"
    return raw or "/"


def _compact_browser_identifier(value: str | None):
    """Collapse a route label or filename into a simple comparison key."""
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _normalize_tags(tags):
    """Normalize tags into short lowercase strings."""
    if not tags:
        return []

    if isinstance(tags, str):
        raw_tags = [piece.strip() for piece in tags.split(",")]
    else:
        raw_tags = [str(piece).strip() for piece in tags]

    normalized = []
    seen = set()
    for tag in raw_tags:
        cleaned = re.sub(r"\s+", "-", tag.lower()).strip("-")
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned[:32])

    return normalized[:6]


def _clip_text(text, limit=220):
    """Return a compact single-line string."""
    normalized = " ".join(str(text or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _join_text_parts(parts, limit=12):
    """Join distinct non-empty text parts into one normalized string."""
    selected = _unique_preserving_order(parts, limit=limit)
    return " ".join(part for part in selected if str(part or "").strip()).strip()


def _normalize_action_id(action_id: str):
    """Normalize action identifiers from chat or UI input."""
    cleaned = re.sub(r"[^a-z0-9_-]+", "_", str(action_id or "").strip().lower())
    cleaned = cleaned.strip("_")
    return cleaned


def _guess_forge_language(path: str) -> str | None:
    """Infer a Forge language label from one file path."""
    return FORGE_LANGUAGE_BY_EXTENSION.get(Path(str(path or "")).suffix.lower())


def _merge_nested_dict(base: dict | None, override: dict | None) -> dict:
    merged = dict(base or {})
    for key, value in dict(override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_nested_dict(merged.get(key), value)
        else:
            merged[key] = value
    return merged


def _detect_forge_execution_trigger(text: str) -> str | None:
    """Return the explicit Forge-routing phrase when the operator asked for Forge by name."""
    normalized = " ".join(str(text or "").lower().split()).strip()
    if not normalized:
        return None
    if any(phrase in normalized for phrase in FORGE_EXECUTION_NEGATIONS):
        return None
    return next((phrase for phrase in FORGE_EXECUTION_PHRASES if phrase in normalized), None)


def _extract_forge_task(text: str, matched_trigger: str | None = None) -> str:
    """Strip the routing phrase so Forge sees the actual operator goal."""
    cleaned = " ".join(str(text or "").split()).strip()
    if not cleaned:
        return ""

    if matched_trigger:
        trigger_re = re.compile(rf"\b{re.escape(matched_trigger)}\b[:\s,-]*", re.IGNORECASE)
        cleaned = trigger_re.sub(" ", cleaned, count=1)

    cleaned = re.sub(r"^\s*(?:can you|could you|would you|please|jarvis)\b[:, -]*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" .:-")
    return cleaned or " ".join(str(text or "").split()).strip()


def _resolve_active_lane(response_mode: str | None) -> str:
    """Map the current response mode onto the visible routing lane."""
    normalized = _normalize_mode_name(response_mode)
    if normalized == "operator":
        return LANE_OPERATOR
    if normalized == "builder":
        return LANE_BUILDER
    return LANE_JARVIS


def _higher_authority_lane(a: str | None, b: str | None) -> str:
    """Return the higher-authority lane label between two known lanes."""
    left = str(a or "").strip().upper()
    right = str(b or "").strip().upper()
    try:
        left_index = LANE_AUTHORITY_ORDER.index(left)
    except ValueError:
        left_index = None
    try:
        right_index = LANE_AUTHORITY_ORDER.index(right)
    except ValueError:
        right_index = None
    if left_index is None:
        return right or left
    if right_index is None:
        return left
    return left if left_index <= right_index else right


def _arbitrate_lane_transition(
    *,
    active_lane: str,
    target_lane: str,
    requests_forge_execution: bool,
    operator_override: bool = False,
    response_mode: str | None = None,
) -> dict[str, Any]:
    """Apply the current AAIS lane-routing guardrails to one proposed transition."""
    normalized_mode = _normalize_mode_name(response_mode)
    authority_lane = _higher_authority_lane(active_lane, target_lane)
    if normalized_mode in {"tiny", "small", "super", "governed_full"} and target_lane in {LANE_FORGE, LANE_FORGE_EVAL}:
        if normalized_mode == "small":
            label = "Small Nova"
            reason = "RULE_SMALL_NOVA_STAYS_CONVERSATIONAL"
        elif normalized_mode in {"super", "governed_full"}:
            label = "Super Nova"
            reason = "RULE_SUPER_NOVA_STAYS_CONVERSATIONAL"
        else:
            label = "Tiny Nova"
            reason = "RULE_TINY_NOVA_STAYS_CONVERSATIONAL"
        return {
            "allowed": False,
            "active_lane": active_lane,
            "requested_lane": target_lane,
            "resolved_lane": active_lane,
            "authority_lane": authority_lane,
            "reason": reason,
            "summary": f"{label} stays in a conversational lane and cannot hand the turn to Forge.",
        }
    if operator_override:
        return {
            "allowed": True,
            "active_lane": active_lane,
            "requested_lane": target_lane,
            "resolved_lane": target_lane,
            "authority_lane": authority_lane,
            "reason": "RULE_1_OPERATOR_SUPREMACY",
            "summary": "Operator authority explicitly allowed this lane transition.",
        }
    if target_lane == LANE_FORGE and not requests_forge_execution:
        return {
            "allowed": False,
            "active_lane": active_lane,
            "requested_lane": target_lane,
            "resolved_lane": active_lane,
            "authority_lane": authority_lane,
            "reason": "RULE_2_FORGE_REQUIRES_EXPLICIT_INTENT",
            "summary": "Forge execution requires an explicit operator request.",
        }
    if active_lane == LANE_BUILDER and target_lane == LANE_FORGE:
        return {
            "allowed": True,
            "active_lane": active_lane,
            "requested_lane": target_lane,
            "resolved_lane": target_lane,
            "authority_lane": authority_lane,
            "reason": "RULE_3_BUILDER_HANDOFF_TO_FORGE",
            "summary": "Builder may scope the work, but Forge owns the execution boundary.",
        }
    if active_lane == LANE_JARVIS and target_lane == LANE_FORGE:
        return {
            "allowed": True,
            "active_lane": active_lane,
            "requested_lane": target_lane,
            "resolved_lane": target_lane,
            "authority_lane": authority_lane,
            "reason": "RULE_4_JARVIS_ROUTES_TO_FORGE_PERSONA_MAINTAINED",
            "summary": "Jarvis may route the task to Forge while keeping Jarvis as the visible authority.",
        }
    if target_lane == LANE_SORVA:
        return {
            "allowed": False,
            "active_lane": active_lane,
            "requested_lane": target_lane,
            "resolved_lane": active_lane,
            "authority_lane": authority_lane,
            "reason": "RULE_5_SORVA_NOT_YET_INTEGRATED",
            "summary": "Sorva oversight is not yet integrated into the live runtime.",
        }
    return {
        "allowed": True,
        "active_lane": active_lane,
        "requested_lane": target_lane,
        "resolved_lane": target_lane,
        "authority_lane": authority_lane,
        "reason": "ARBITRATION_PASSED",
        "summary": "The lane transition passed the current Jarvis routing guardrails.",
    }


def _score_text_match(query_tokens, haystack):
    """Compute a simple lexical relevance score."""
    lower_haystack = haystack.lower()
    score = 0

    for token in query_tokens:
        if token in lower_haystack:
            score += 1

    return score


def _best_matching_line_index(content, query_tokens):
    """Return the line index with the strongest lexical overlap."""
    best_index = None
    best_score = 0

    for index, line in enumerate((content or "").splitlines()):
        line_score = _score_text_match(query_tokens, line)
        if line_score > best_score:
            best_index = index
            best_score = line_score

    return best_index, best_score


def _unique_preserving_order(items, limit=None):
    """Return unique strings in first-seen order."""
    unique_items = []
    seen = set()

    for item in items:
        normalized = str(item or "").strip()
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique_items.append(normalized)
        if limit and len(unique_items) >= limit:
            break

    return unique_items


def _looks_like_coding_request(text):
    """Heuristically detect when a prompt would benefit from workspace context."""
    lower = str(text or "").lower()
    if not lower:
        return False

    if any(hint in lower for hint in WORKSPACE_OPT_OUT_HINTS):
        return False

    if WORKSPACE_FILE_PATTERN.search(lower):
        return True

    code_specific_markers = (
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        "file ",
        "files ",
        "folder ",
        "route",
        "routes",
        "api",
        "backend",
        "frontend",
        "function",
        "component",
        "module",
        "repo",
        "workspace",
        "test",
        "tests",
        "bug",
        "error",
        "debug",
        "trace",
        "stack",
    )

    if any(hint in lower for hint in LIVE_INFO_HINTS) and any(
        marker in lower for marker in ("what changed", "compare", "latest", "recent")
    ):
        return False

    coding_hits = sum(1 for hint in CODING_HINTS if hint in lower)
    action_hits = sum(1 for hint in CODING_ACTION_HINTS if hint in lower)
    asks_question = "?" in lower
    has_code_specific_marker = any(marker in lower for marker in code_specific_markers)

    if not has_code_specific_marker:
        return False

    return coding_hits >= 2 or (coding_hits >= 1 and (action_hits >= 1 or asks_question))


def _build_workspace_query(text):
    """Extract the most useful search tokens from a coding-style prompt."""
    cleaned = " ".join(str(text or "").split()).strip()
    if not cleaned:
        return ""

    priority_terms = _unique_preserving_order(WORKSPACE_FILE_PATTERN.findall(cleaned), limit=3)
    tokens = []

    for token in _tokenize_query(cleaned):
        if token in WORKSPACE_QUERY_STOPWORDS:
            continue
        if len(token) < 2:
            continue
        tokens.append(token)

    merged = _unique_preserving_order(priority_terms + tokens, limit=8)
    return " ".join(merged[:6])


def _normalize_mode_name(mode):
    """Normalize mode ids for local routing."""
    return " ".join(str(mode or "").lower().split()).strip().replace("-", "_")


def _normalize_name(text):
    """Normalize short identifiers for case-insensitive comparisons."""
    return str(text or "").strip().lower()


def _mentioned_filenames(query):
    """Return explicit filenames mentioned in a workspace-style query."""
    return {
        Path(match).name.lower()
        for match in WORKSPACE_FILE_PATTERN.findall(str(query or ""))
        if Path(match).name
    }


@dataclass(slots=True)
class MemoryGovernanceResult:
    """Structured outcome for memory store or merge requests."""

    action: str
    stored: bool = False
    merged: bool = False
    reason: str = "none"
    detail: str = ""
    next_step: str = "none"
    memory: dict[str, Any] | None = None
    governance: dict[str, Any] | None = None
    requested_text: str | None = None
    target_id: str | None = None
    source_ids: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "stored": bool(self.stored),
            "merged": bool(self.merged),
            "reason": self.reason if self.reason in MEMORY_REJECTION_REASONS else "rejected",
            "detail": " ".join(str(self.detail or "").split()).strip(),
            "next_step": (
                self.next_step
                if self.next_step in MEMORY_REJECTION_NEXT_STEPS
                else "no_next_step"
            ),
            "memory": dict(self.memory or {}) if self.memory else None,
            "governance": dict(self.governance or {}) if self.governance else None,
            "requested_text": " ".join(str(self.requested_text or "").split()).strip() or None,
            "target_id": str(self.target_id or "").strip() or None,
            "source_ids": [str(item).strip() for item in list(self.source_ids or []) if str(item).strip()],
        }


class JarvisMemoryStore:
    """Persistent memory notes stored on disk for the local operator."""

    def __init__(self, memory_path: str | Path | None = None):
        self.memory_path = Path(memory_path) if memory_path else None
        self._lock = threading.RLock()
        self.memory_board = build_default_memory_controller()
        self._last_board_event: dict[str, Any] | None = None
        self._enforcer_authority: str | None = None
        self._enforcer_component_id: str | None = None
        self._bypass_reporter = None

    def configure_governance_enforcer(
        self,
        authority_token: str | None,
        *,
        component_id: str | None = None,
        reporter=None,
    ) -> None:
        """Attach or clear the live memory gateway authority token."""
        self._enforcer_authority = str(authority_token or "").strip() or None
        self._enforcer_component_id = str(component_id or "").strip() or None
        self._bypass_reporter = reporter

    def _require_enforcer_authority(
        self,
        action: str,
        provided_authority: str | None,
        *,
        target: str | None = None,
    ) -> None:
        """Fail closed when a live runtime memory operation bypasses the memory gateway."""
        expected = str(self._enforcer_authority or "").strip()
        if not expected:
            return
        if str(provided_authority or "").strip() == expected:
            return

        payload = {
            "action": str(action or "").strip().lower() or "unknown",
            "target": str(target or "").strip() or None,
            "component_id": self._enforcer_component_id,
            "detail": (
                "Live memory operations must route through the memory board enforcer; "
                f"direct `{action}` access was blocked."
            ),
        }
        if callable(self._bypass_reporter):
            try:
                self._bypass_reporter(payload)
            except Exception:
                logger.exception("Memory bypass reporter failed while handling a blocked mutation.")
        raise MemoryBoardBypassError(payload["detail"])

    @staticmethod
    def _clean_text(value, *, limit: int | None = None):
        """Collapse whitespace for short operator-facing memory fields."""
        cleaned = " ".join(str(value or "").split()).strip()
        if limit is not None and len(cleaned) > limit:
            return cleaned[: max(0, limit - 3)].rstrip() + "..."
        return cleaned

    @staticmethod
    def _normalize_category(category, tags=None):
        """Return a stable category id for one memory record."""
        raw = str(category or "").strip().lower()
        if not raw and tags:
            normalized_tags = _normalize_tags(tags)
            raw = normalized_tags[0] if normalized_tags else ""
        cleaned = re.sub(r"[^a-z0-9_-]+", "_", raw).strip("_")
        return cleaned or "general"

    @staticmethod
    def _normalize_priority(priority, *, pinned=False, override=False):
        """Clamp priority into a stable 0-100 range."""
        baseline = 100 if override else (80 if pinned else 50)
        try:
            value = int(priority)
        except (TypeError, ValueError):
            value = baseline
        value = max(0, min(value, 100))
        if override:
            return max(value, 95)
        if pinned:
            return max(value, 80)
        return value

    def _normalize_history(self, history, *, fallback_content: str = "", created_at: str = ""):
        """Normalize per-memory rewrite history for audit-friendly display."""
        normalized_entries = []
        if isinstance(history, list):
            for entry in history:
                if not isinstance(entry, dict):
                    continue
                meta = entry.get("meta")
                normalized_entries.append(
                    {
                        "id": str(entry.get("id") or uuid.uuid4()),
                        "type": self._clean_text(
                            entry.get("type") or entry.get("event") or "updated",
                            limit=48,
                        ).lower()
                        or "updated",
                        "at": str(
                            entry.get("at")
                            or entry.get("created_at")
                            or entry.get("updated_at")
                            or created_at
                            or _utc_now()
                        ),
                        "note": self._clean_text(entry.get("note") or entry.get("reason"), limit=280),
                        "why": self._clean_text(entry.get("why"), limit=280) or None,
                        "content": self._clean_text(
                            entry.get("content"),
                            limit=1200,
                        )
                        or None,
                        "meta": dict(meta or {}) if isinstance(meta, dict) else {},
                    }
                )
        if normalized_entries:
            return normalized_entries
        if fallback_content:
            return [
                {
                    "id": str(uuid.uuid4()),
                    "type": "created",
                    "at": str(created_at or _utc_now()),
                    "note": "Memory created.",
                    "why": None,
                    "content": self._clean_text(fallback_content, limit=1200) or None,
                    "meta": {},
                }
            ]
        return []

    def _append_history(
        self,
        memory: dict,
        *,
        event_type: str,
        note: str | None = None,
        why: str | None = None,
        content: str | None = None,
        meta: dict | None = None,
        at: str | None = None,
    ):
        """Append one normalized history event onto a memory record."""
        history = list(memory.get("history") or [])
        history.append(
            {
                "id": str(uuid.uuid4()),
                "type": self._clean_text(event_type, limit=48).lower() or "updated",
                "at": str(at or _utc_now()),
                "note": self._clean_text(note, limit=280),
                "why": self._clean_text(why, limit=280) or None,
                "content": self._clean_text(
                    content if content is not None else memory.get("content"),
                    limit=1200,
                )
                or None,
                "meta": dict(meta or {}),
            }
        )
        memory["history"] = self._normalize_history(history)

    def _normalize_memory_record(self, memory):
        """Upgrade legacy memory rows into the canonical memory-bank shape."""
        if not isinstance(memory, dict):
            memory = {}

        content = " ".join(
            str(memory.get("content") or memory.get("text") or "").split()
        ).strip()
        tags = _normalize_tags(memory.get("tags"))
        override = bool(memory.get("override") or str(memory.get("kind") or "").lower() == "override")
        pinned = bool(memory.get("pinned", False) or override)
        category = self._normalize_category(memory.get("category"), tags=tags)
        priority = self._normalize_priority(
            memory.get("priority"),
            pinned=pinned,
            override=override,
        )
        active_raw = memory.get("active")
        active = True if active_raw is None else bool(active_raw)
        created_at = str(memory.get("created_at") or _utc_now())
        updated_at = str(memory.get("updated_at") or created_at)
        last_used_at = memory.get("last_used_at")
        archived_at = str(memory.get("archived_at") or "").strip() or None
        if archived_at:
            active = False
        kind = str(memory.get("kind") or ("override" if override else "memory")).strip().lower() or "memory"
        normalized_tags = _normalize_tags(tags)
        merged_from = [
            str(item).strip()
            for item in list(memory.get("merged_from") or [])
            if str(item).strip()
        ]
        history = self._normalize_history(
            memory.get("history"),
            fallback_content=content,
            created_at=created_at,
        )

        normalized = {
            "id": str(memory.get("id") or uuid.uuid4()),
            "category": category,
            "content": content,
            "text": content,
            "priority": priority,
            "active": active,
            "created_at": created_at,
            "updated_at": updated_at,
            "last_used_at": last_used_at,
            "source": str(memory.get("source") or "manual"),
            "tags": normalized_tags,
            "pinned": bool(pinned),
            "kind": kind,
            "override": override,
            "scope": str(memory.get("scope") or "").strip() or None,
            "supersedes": str(memory.get("supersedes") or "").strip() or None,
            "why": self._clean_text(memory.get("why"), limit=280) or None,
            "archived_at": archived_at,
            "archived_reason": self._clean_text(memory.get("archived_reason"), limit=280) or None,
            "merged_into": str(memory.get("merged_into") or "").strip() or None,
            "merged_from": merged_from,
            "history": history,
            "state_class": str(memory.get("state_class") or "").strip() or None,
            "truth_status": str(memory.get("truth_status") or "").strip() or None,
            "retention_status": str(memory.get("retention_status") or "").strip() or None,
        }
        projected = project_record(
            normalized,
            kind="memory",
            source_type="memory_override" if override else "memory",
        )
        projected.pop("_state_hygiene_kind", None)
        return projected

    def _memory_tokens(self, memory: dict):
        """Return stable lexical tokens for merge/conflict heuristics."""
        combined = _join_text_parts(
            [
                memory.get("content"),
                memory.get("category"),
                memory.get("why"),
                " ".join(memory.get("tags") or []),
            ],
            limit=24,
        )
        return {
            token
            for token in _tokenize_query(combined)
            if len(token) > 2 and token not in WORKSPACE_QUERY_STOPWORDS
        }

    def _resolve_memory_path(self):
        """Resolve the JSON file that stores Jarvis memories."""
        if os.getenv(MEMORY_PATH_ENV):
            return Path(os.getenv(MEMORY_PATH_ENV)).expanduser().resolve()

        if self.memory_path is not None:
            return self.memory_path.expanduser().resolve()

        root = Path(__file__).resolve().parents[1]
        return root / ".local" / DEFAULT_MEMORY_FILENAME

    def _ensure_parent(self, path: Path):
        """Create parent directories when needed."""
        path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _default_store_payload() -> dict[str, Any]:
        """Return the persisted memory-bank payload shape."""
        return {
            "memories": [],
            "board_events": [],
            "board_event_count": 0,
        }

    def _load_store_payload(self) -> dict[str, Any]:
        """Load the full memory-bank payload including board governance history."""
        path = self._resolve_memory_path()
        if not path.exists():
            return self._default_store_payload()

        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            logger.warning("Jarvis memory store was unreadable, starting fresh")
            return self._default_store_payload()

        if isinstance(payload, list):
            payload = {"memories": payload}
        if not isinstance(payload, dict):
            return self._default_store_payload()

        normalized = self._default_store_payload()
        memories = payload.get("memories", [])
        board_events = payload.get("board_events", [])
        normalized["memories"] = memories if isinstance(memories, list) else []
        normalized["board_events"] = board_events if isinstance(board_events, list) else []
        try:
            normalized["board_event_count"] = max(
                int(payload.get("board_event_count") or 0),
                len(normalized["board_events"]),
            )
        except (TypeError, ValueError):
            normalized["board_event_count"] = len(normalized["board_events"])
        return normalized

    def _save_store_payload(self, payload: dict[str, Any]) -> None:
        """Persist memories and board governance history together."""
        path = self._resolve_memory_path()
        self._ensure_parent(path)
        board_events = [
            dict(event)
            for event in list(payload.get("board_events") or [])[-200:]
            if isinstance(event, dict)
        ]
        try:
            board_event_count = max(
                int(payload.get("board_event_count") or 0),
                len(board_events),
            )
        except (TypeError, ValueError):
            board_event_count = len(board_events)
        normalized = {
            "memories": [
                self._normalize_memory_record(memory)
                for memory in list(payload.get("memories") or [])
            ],
            "board_events": board_events,
            "board_event_count": board_event_count,
        }
        with path.open("w", encoding="utf-8") as handle:
            json.dump(normalized, handle, indent=2)

    def _load_memories(self):
        """Load the full memory list from disk."""
        payload = self._load_store_payload()
        memories = payload.get("memories", [])
        if not isinstance(memories, list):
            return []

        return [self._normalize_memory_record(memory) for memory in memories]

    def _save_memories(self, memories):
        """Persist the full memory list to disk."""
        payload = self._load_store_payload()
        payload["memories"] = [self._normalize_memory_record(memory) for memory in memories]
        self._save_store_payload(payload)

    def _slot_snapshot(self, slot_id: str | None) -> dict[str, Any]:
        """Return a compact board slot snapshot for one slot id."""
        slot = self.memory_board.slots.get(str(slot_id or "").strip())
        if slot is None:
            return {
                "slot_id": str(slot_id or "").strip() or None,
                "slot_role": None,
                "active": False,
                "module_id": None,
                "module_class": None,
                "trust_class": None,
            }
        module = slot.module
        return {
            "slot_id": slot.slot_id,
            "slot_role": slot.slot_name,
            "active": bool(slot.active),
            "module_id": module.module_id if module else None,
            "module_class": module.module_class if module else None,
            "trust_class": module.trust_class if module else None,
        }

    def _record_board_event(
        self,
        *,
        action: str,
        slot_id: str | None,
        memory: dict[str, Any] | None = None,
        decision: str = "allow",
        source: str | None = None,
        detail: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append one board-governance event to the memory-bank payload."""
        slot_snapshot = self._slot_snapshot(slot_id)
        event = {
            "event_id": str(uuid.uuid4()),
            "recorded_at": _utc_now(),
            "action": " ".join(str(action or "").lower().split()).strip() or "unknown",
            "decision": "ALLOW" if str(decision or "").strip().lower() == "allow" else "BLOCK",
            "slot_id": slot_snapshot["slot_id"],
            "slot_role": slot_snapshot["slot_role"],
            "slot_active": slot_snapshot["active"],
            "module_id": slot_snapshot["module_id"],
            "module_class": slot_snapshot["module_class"],
            "trust_class": slot_snapshot["trust_class"],
            "memory_id": str((memory or {}).get("id") or "").strip() or None,
            "category": str((memory or {}).get("category") or "").strip().lower() or None,
            "state_class": str((memory or {}).get("state_class") or "").strip().lower() or None,
            "truth_status": str((memory or {}).get("truth_status") or "").strip().lower() or None,
            "source": self._clean_text(source, limit=80) or None,
            "detail": self._clean_text(detail, limit=280) or None,
            "meta": dict(meta or {}),
        }
        payload = self._load_store_payload()
        payload["board_events"] = list(payload.get("board_events") or []) + [event]
        payload["board_event_count"] = max(
            int(payload.get("board_event_count") or 0) + 1,
            len(payload["board_events"]),
        )
        self._save_store_payload(payload)
        self._last_board_event = event
        return event

    def record_board_event(
        self,
        *,
        action: str,
        slot_id: str | None,
        memory: dict[str, Any] | None = None,
        decision: str = "allow",
        source: str | None = None,
        detail: str | None = None,
        meta: dict[str, Any] | None = None,
        _enforcer_authority: str | None = None,
    ) -> dict[str, Any]:
        """Record one explicit board-governance event through the live gateway."""
        self._require_enforcer_authority(
            action,
            _enforcer_authority,
            target=slot_id,
        )
        with self._lock:
            return self._record_board_event(
                action=action,
                slot_id=slot_id,
                memory=memory,
                decision=decision,
                source=source,
                detail=detail,
                meta=meta,
            )

    def last_board_event(self) -> dict[str, Any] | None:
        """Return the latest recorded board governance event when present."""
        return dict(self._last_board_event) if isinstance(self._last_board_event, dict) else None

    def _board_governance_summary(self, *, limit: int = 12) -> dict[str, Any]:
        """Return recent board governance evidence for the memory-bank surface."""
        payload = self._load_store_payload()
        events = [
            dict(event)
            for event in list(payload.get("board_events") or [])
            if isinstance(event, dict)
        ]
        counts: dict[str, int] = {}
        action_counts: dict[str, int] = {}
        for event in events:
            decision = str(event.get("decision") or "ALLOW").strip().upper() or "ALLOW"
            counts[decision] = counts.get(decision, 0) + 1
            action = str(event.get("action") or "unknown").strip().lower() or "unknown"
            action_counts[action] = action_counts.get(action, 0) + 1
        recent_events = list(reversed(events[-max(1, min(int(limit or 12), 25)) :]))
        return {
            "event_count": int(payload.get("board_event_count") or len(events)),
            "decision_counts": counts,
            "action_counts": action_counts,
            "recent_events": recent_events,
            "last_event": recent_events[0] if recent_events else None,
        }

    def list_memories(
        self,
        query: str | None = None,
        limit: int = 12,
        category: str | None = None,
        active: bool | None = None,
        sort: str = "priority",
        truth_scope: str = "live",
        _enforcer_authority: str | None = None,
    ):
        """Return memories sorted by relevance or recency."""
        self._require_enforcer_authority(
            "list_memories",
            _enforcer_authority,
            target=truth_scope,
        )
        with self._lock:
            memories = self._load_memories()

        query_tokens = _tokenize_query(query)
        category_filter = self._normalize_category(category) if category else None
        sort_key = str(sort or "priority").strip().lower()
        ranked = []

        for memory in memories:
            if category_filter and memory.get("category") != category_filter:
                continue
            if active is not None and bool(memory.get("active", True)) != bool(active):
                continue

            text = memory.get("content", "")
            tags = memory.get("tags", [])
            searchable = " ".join(
                [
                    text,
                    str(memory.get("category") or ""),
                    str(memory.get("why") or ""),
                    " ".join(tags),
                ]
            )
            score = _score_text_match(query_tokens, searchable) if query_tokens else 0

            if query_tokens and score == 0:
                continue

            if memory.get("pinned"):
                score += 0.5
            if memory.get("override"):
                score += 0.75

            priority = int(memory.get("priority", 0) or 0)
            updated_at = memory.get("updated_at", "")
            created_at = memory.get("created_at", "")
            sort_tuple = {
                "priority": (score, priority, updated_at, created_at),
                "recency": (score, updated_at, created_at, priority),
                "updated": (score, updated_at, priority, created_at),
                "created": (score, created_at, priority, updated_at),
            }.get(sort_key, (score, priority, updated_at, created_at))

            ranked.append((sort_tuple, memory))

        ranked.sort(key=lambda item: item[0], reverse=True)
        matches = [item[1] for item in ranked]
        if normalize_truth_scope(truth_scope) != "all":
            matches = filter_operator_records(matches, truth_scope=truth_scope)
        return matches[: max(1, min(limit, 50))]

    def get_memory(self, memory_id: str, *, _enforcer_authority: str | None = None):
        """Return one memory record by ID when present."""
        self._require_enforcer_authority(
            "get_memory",
            _enforcer_authority,
            target=memory_id,
        )
        with self._lock:
            memories = self._load_memories()
        for memory in memories:
            if memory.get("id") == memory_id:
                return memory
        return None

    def add_memory(
        self,
        text: str,
        tags=None,
        pinned: bool = False,
        source: str = "manual",
        *,
        category: str | None = None,
        priority: int | None = None,
        active: bool = True,
        kind: str = "memory",
        override: bool = False,
        scope: str | None = None,
        supersedes: str | None = None,
        why: str | None = None,
        state_class: str | None = None,
        truth_status: str | None = None,
        _enforcer_authority: str | None = None,
    ):
        """Save a new long-term memory note."""
        self._require_enforcer_authority(
            "add_memory",
            _enforcer_authority,
        )
        cleaned = " ".join(str(text or "").split()).strip()
        if not cleaned:
            raise ValueError("Memory text is required")

        normalized_tags = _normalize_tags(tags)
        normalized_category = self._normalize_category(category, tags=normalized_tags)
        memory = self._normalize_memory_record({
            "id": str(uuid.uuid4()),
            "category": normalized_category,
            "content": cleaned,
            "text": cleaned,
            "priority": self._normalize_priority(priority, pinned=pinned, override=override),
            "active": bool(active),
            "tags": normalized_tags,
            "pinned": bool(pinned),
            "source": source,
            "kind": "override" if override else kind,
            "override": bool(override),
            "scope": scope,
            "supersedes": supersedes,
            "why": why,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "last_used_at": None,
            "archived_at": None,
            "archived_reason": None,
            "merged_into": None,
            "merged_from": [],
            "history": [],
            "state_class": state_class,
            "truth_status": truth_status,
            "retention_status": None,
        })
        self._append_history(
            memory,
            event_type="created",
            note="Override created." if override else "Memory created.",
            why=memory.get("why"),
            content=memory.get("content"),
            at=memory.get("created_at"),
        )

        with self._lock:
            memories = self._load_memories()
            memories.append(memory)
            self._save_memories(memories)
            self._record_board_event(
                action="write",
                slot_id=self._classify_memory_slot(memory),
                memory=memory,
                source=source,
                detail="Persistent memory admitted through the board-governed write path.",
                meta={"override": bool(override), "kind": memory.get("kind")},
            )

        return memory

    def add_override(
        self,
        text: str,
        *,
        category: str = "override",
        priority: int | None = None,
        scope: str | None = None,
        supersedes: str | None = None,
        source: str = "override",
        why: str | None = None,
        state_class: str | None = None,
        truth_status: str | None = None,
        _enforcer_authority: str | None = None,
    ):
        """Persist a high-priority override memory."""
        return self.add_memory(
            text=text,
            tags=[category, "override"],
            pinned=True,
            source=source,
            category=category,
            priority=priority if priority is not None else 100,
            active=True,
            kind="override",
            override=True,
            scope=scope,
            supersedes=supersedes,
            why=why,
            state_class=state_class,
            truth_status=truth_status,
            _enforcer_authority=_enforcer_authority,
        )

    def delete_memory(self, memory_id: str, *, _enforcer_authority: str | None = None):
        """Delete a memory by ID."""
        self._require_enforcer_authority(
            "delete_memory",
            _enforcer_authority,
            target=memory_id,
        )
        with self._lock:
            memories = self._load_memories()
            deleted = next((memory for memory in memories if memory.get("id") == memory_id), None)
            next_memories = [memory for memory in memories if memory.get("id") != memory_id]
            if len(next_memories) == len(memories):
                return False
            self._save_memories(next_memories)
            self._record_board_event(
                action="delete",
                slot_id=self._classify_memory_slot(deleted or {}),
                memory=deleted,
                source="manual_delete",
                detail="Persistent memory was removed through the governed delete path.",
            )
            return True

    def update_memory(
        self,
        memory_id: str,
        text: str | None = None,
        tags=None,
        pinned=None,
        *,
        category: str | None = None,
        priority: int | None = None,
        active: bool | None = None,
        kind: str | None = None,
        override: bool | None = None,
        scope: str | None = None,
        supersedes: str | None = None,
        why: str | None = None,
        note: str | None = None,
        state_class: str | None = None,
        truth_status: str | None = None,
        _enforcer_authority: str | None = None,
    ):
        """Update a saved memory note without replacing unrelated fields."""
        self._require_enforcer_authority(
            "update_memory",
            _enforcer_authority,
            target=memory_id,
        )
        with self._lock:
            memories = self._load_memories()

            for memory in memories:
                if memory.get("id") != memory_id:
                    continue

                change_fields = []
                previous_content = str(memory.get("content") or "")

                if text is not None:
                    cleaned = " ".join(str(text).split()).strip()
                    if not cleaned:
                        raise ValueError("Memory text is required")
                    if cleaned != memory.get("content"):
                        memory["content"] = cleaned
                        memory["text"] = cleaned
                        change_fields.append("content")

                if tags is not None:
                    normalized_tags = _normalize_tags(tags)
                    if normalized_tags != list(memory.get("tags") or []):
                        memory["tags"] = normalized_tags
                        change_fields.append("tags")

                if pinned is not None:
                    next_pinned = bool(pinned)
                    if next_pinned != bool(memory.get("pinned")):
                        memory["pinned"] = next_pinned
                        change_fields.append("pinned")

                if category is not None:
                    next_category = self._normalize_category(category, tags=memory.get("tags"))
                    if next_category != memory.get("category"):
                        memory["category"] = next_category
                        change_fields.append("category")
                elif tags is not None and str(memory.get("category") or "").strip().lower() in {"", "general"}:
                    next_category = self._normalize_category(None, tags=memory.get("tags"))
                    if next_category != memory.get("category"):
                        memory["category"] = next_category
                        change_fields.append("category")

                if active is not None:
                    next_active = bool(active)
                    if next_active != bool(memory.get("active", True)):
                        memory["active"] = next_active
                        if next_active:
                            memory["archived_at"] = None
                            memory["archived_reason"] = None
                        change_fields.append("active")

                if kind is not None:
                    next_kind = str(kind).strip().lower() or "memory"
                    if next_kind != memory.get("kind"):
                        memory["kind"] = next_kind
                        change_fields.append("kind")

                if override is not None:
                    next_override = bool(override)
                    if next_override != bool(memory.get("override")):
                        memory["override"] = next_override
                        change_fields.append("override")

                if priority is not None or pinned is not None or override is not None:
                    next_priority = self._normalize_priority(
                        priority if priority is not None else memory.get("priority"),
                        pinned=memory.get("pinned", False),
                        override=memory.get("override", False),
                    )
                    if next_priority != int(memory.get("priority", 0) or 0):
                        memory["priority"] = next_priority
                        change_fields.append("priority")

                if scope is not None:
                    next_scope = str(scope).strip() or None
                    if next_scope != memory.get("scope"):
                        memory["scope"] = next_scope
                        change_fields.append("scope")

                if supersedes is not None:
                    next_supersedes = str(supersedes).strip() or None
                    if next_supersedes != memory.get("supersedes"):
                        memory["supersedes"] = next_supersedes
                        change_fields.append("supersedes")

                if why is not None:
                    next_why = self._clean_text(why, limit=280) or None
                    if next_why != memory.get("why"):
                        memory["why"] = next_why
                        change_fields.append("why")

                if state_class is not None:
                    next_state_class = str(state_class).strip().lower() or None
                    if next_state_class != memory.get("state_class"):
                        memory["state_class"] = next_state_class
                        change_fields.append("state_class")

                if truth_status is not None:
                    next_truth_status = str(truth_status).strip().lower() or None
                    if next_truth_status != memory.get("truth_status"):
                        memory["truth_status"] = next_truth_status
                        change_fields.append("truth_status")

                memory["tags"] = _normalize_tags(memory.get("tags"))
                memory["content"] = " ".join(str(memory.get("content") or memory.get("text") or "").split()).strip()
                memory["text"] = memory["content"]
                if not memory.get("active", True):
                    memory["archived_at"] = str(memory.get("archived_at") or _utc_now())
                elif change_fields and "active" in change_fields:
                    memory["archived_at"] = None
                    memory["archived_reason"] = None
                if not change_fields:
                    return self._normalize_memory_record(memory)
                memory["updated_at"] = _utc_now()
                self._append_history(
                    memory,
                    event_type="rewritten" if "content" in change_fields else "updated",
                    note=note
                    or (
                        "Updated memory fields: " + ", ".join(change_fields)
                    ),
                    why=memory.get("why"),
                    content=memory.get("content"),
                    meta={
                        "changed_fields": list(change_fields),
                        "previous_content": previous_content if previous_content != memory.get("content") else None,
                    },
                    at=memory.get("updated_at"),
                )
                self._save_memories(memories)
                self._record_board_event(
                    action="update",
                    slot_id=self._classify_memory_slot(memory),
                    memory=memory,
                    source="manual_update",
                    detail=(
                        "Persistent memory updated through the board-governed update path."
                    ),
                    meta={"changed_fields": list(change_fields)},
                )
                return self._normalize_memory_record(memory)

        return None

    def archive_memory(
        self,
        memory_id: str,
        *,
        reason: str | None = None,
        _enforcer_authority: str | None = None,
    ):
        """Archive one memory without deleting its history."""
        self._require_enforcer_authority(
            "archive_memory",
            _enforcer_authority,
            target=memory_id,
        )
        with self._lock:
            memories = self._load_memories()
            for memory in memories:
                if memory.get("id") != memory_id:
                    continue
                if memory.get("archived_at") and not memory.get("active", True):
                    return self._normalize_memory_record(memory)
                archived_at = _utc_now()
                memory["active"] = False
                memory["archived_at"] = archived_at
                memory["archived_reason"] = self._clean_text(reason, limit=280) or "Archived from the workbench."
                memory["updated_at"] = archived_at
                self._append_history(
                    memory,
                    event_type="archived",
                    note=memory.get("archived_reason"),
                    why=memory.get("why"),
                    content=memory.get("content"),
                    at=archived_at,
                )
                self._save_memories(memories)
                self._record_board_event(
                    action="archive",
                    slot_id=self._classify_memory_slot(memory),
                    memory=memory,
                    source="manual_archive",
                    detail="Persistent memory archived through the board-governed expiry path.",
                    meta={"reason": memory.get("archived_reason")},
                )
                return self._normalize_memory_record(memory)
        return None

    def merge_memories(
        self,
        *,
        target_id: str,
        source_ids,
        content: str | None = None,
        why: str | None = None,
        note: str | None = None,
        _enforcer_authority: str | None = None,
    ):
        """Merge one or more memories into a canonical target memory."""
        self._require_enforcer_authority(
            "merge_memories",
            _enforcer_authority,
            target=target_id,
        )
        normalized_source_ids = [
            str(item).strip()
            for item in list(source_ids or [])
            if str(item).strip() and str(item).strip() != str(target_id).strip()
        ]
        if not normalized_source_ids:
            raise ValueError("source_ids must include at least one memory other than the target.")

        with self._lock:
            memories = self._load_memories()
            memory_by_id = {memory.get("id"): memory for memory in memories}
            target = memory_by_id.get(target_id)
            if not target:
                return None
            target_state_class = str(target.get("state_class") or "live").strip().lower() or "live"
            if not target.get("active", True):
                raise ValueError("Target memory must stay active before it can absorb merged notes.")
            if target.get("merged_into"):
                raise ValueError("Target memory has already been merged into another canonical record.")

            sources = []
            for source_id in normalized_source_ids:
                source = memory_by_id.get(source_id)
                if not source:
                    raise FileNotFoundError(f"Memory `{source_id}` was not found.")
                source_state_class = str(source.get("state_class") or "live").strip().lower() or "live"
                if not source.get("active", True):
                    raise ValueError("Archived or inactive memories cannot be merged into live operator truth.")
                if source.get("merged_into"):
                    raise ValueError("A memory that already merged forward cannot be merged again.")
                if source_state_class != target_state_class:
                    raise ValueError("Memory merges must stay inside one state class.")
                sources.append(source)

            now = _utc_now()
            merged_content = self._clean_text(content)
            if not merged_content:
                merged_content = "\n\n".join(
                    _unique_preserving_order(
                        [
                            str(target.get("content") or "").strip(),
                            *[str(source.get("content") or "").strip() for source in sources],
                        ]
                    )
                ).strip()
            if not merged_content:
                raise ValueError("Merged memory content cannot be empty.")

            target["content"] = merged_content
            target["text"] = merged_content
            target["why"] = self._clean_text(why, limit=280) or target.get("why")
            target["merged_from"] = _unique_preserving_order(
                list(target.get("merged_from") or []) + normalized_source_ids
            )
            target["tags"] = _normalize_tags(
                list(target.get("tags") or [])
                + [tag for source in sources for tag in list(source.get("tags") or [])]
            )
            target["priority"] = max(
                [int(target.get("priority", 0) or 0)]
                + [int(source.get("priority", 0) or 0) for source in sources]
            )
            target["pinned"] = bool(target.get("pinned")) or any(bool(source.get("pinned")) for source in sources)
            target["override"] = bool(target.get("override")) or any(bool(source.get("override")) for source in sources)
            target["active"] = True
            target["archived_at"] = None
            target["archived_reason"] = None
            target["retention_status"] = None
            target["updated_at"] = now
            self._append_history(
                target,
                event_type="merged",
                note=note
                or f"Merged {len(sources)} memory record(s) into this canonical note.",
                why=target.get("why"),
                content=target.get("content"),
                meta={"source_ids": normalized_source_ids},
                at=now,
            )

            for source in sources:
                source["active"] = False
                source["archived_at"] = now
                source["archived_reason"] = f"Merged into {target_id}"
                source["merged_into"] = target_id
                source["retention_status"] = "archived"
                source["updated_at"] = now
                self._append_history(
                    source,
                    event_type="merged_into",
                    note=f"Merged into canonical memory {target_id}.",
                    why=source.get("why"),
                    content=source.get("content"),
                    meta={"target_id": target_id},
                    at=now,
                )

            self._save_memories(memories)
            self._record_board_event(
                action="merge",
                slot_id=self._classify_memory_slot(target),
                memory=target,
                source="manual_merge",
                detail="Duplicate memories were collapsed into one canonical record through the governed merge path.",
                meta={
                    "source_ids": normalized_source_ids,
                    "source_count": len(normalized_source_ids),
                },
            )
            return self._normalize_memory_record(target)

    def compact_state(self, *, _enforcer_authority: str | None = None):
        """Archive non-live active memories so they stop reading as operator truth."""
        self._require_enforcer_authority(
            "compact_state",
            _enforcer_authority,
            target="state_hygiene",
        )
        archived = 0
        now = _utc_now()
        with self._lock:
            memories = self._load_memories()
            for memory in memories:
                if not memory.get("active", True):
                    continue
                if str(memory.get("state_class") or "live") == "live":
                    continue
                memory["active"] = False
                memory["archived_at"] = now
                memory["archived_reason"] = "Archived by state hygiene compaction."
                memory["updated_at"] = now
                memory["retention_status"] = "archived"
                self._append_history(
                    memory,
                    event_type="archived",
                    note=memory["archived_reason"],
                    why=memory.get("why"),
                    content=memory.get("content"),
                    at=now,
                )
                archived += 1
            if archived:
                self._save_memories(memories)
                self._record_board_event(
                    action="compact_archive",
                    slot_id="slot_04",
                    source="state_hygiene",
                    detail="State hygiene compaction archived non-live memories through the board-governed expiry path.",
                    meta={"archived_memories": archived},
                )
        return {"archived_memories": archived}

    def build_summary(
        self,
        *,
        truth_scope: str = "live",
        _enforcer_authority: str | None = None,
    ):
        """Return aggregate memory-bank stats for the operator workbench."""
        self._require_enforcer_authority(
            "build_summary",
            _enforcer_authority,
            target=truth_scope,
        )
        with self._lock:
            memories = self._load_memories()
        scoped_memories = memories
        visible_memories = memories
        if normalize_truth_scope(truth_scope) != "all":
            scoped_memories = [memory for memory in memories if str(memory.get("state_class") or "live") == "live"]
            visible_memories = filter_operator_records(memories, truth_scope=truth_scope)

        categories: dict[str, int] = {}
        summary = {
            "total": len(memories),
            "scoped_total": len(scoped_memories),
            "visible": len(visible_memories),
            "active": 0,
            "archived": 0,
            "overrides": 0,
            "pinned": 0,
            "categories": {},
            "state_hygiene": summarize_records(memories),
        }
        for memory in scoped_memories:
            category = str(memory.get("category") or "general")
            categories[category] = categories.get(category, 0) + 1
            if memory.get("active", True):
                summary["active"] += 1
            else:
                summary["archived"] += 1
            if memory.get("override"):
                summary["overrides"] += 1
            if memory.get("pinned"):
                summary["pinned"] += 1
        summary["categories"] = dict(sorted(categories.items(), key=lambda item: (-item[1], item[0])))
        summary["memory_board"] = self.get_memory_board_snapshot(
            truth_scope=truth_scope,
            _enforcer_authority=_enforcer_authority,
        )
        return summary

    def _classify_memory_slot(self, memory: dict[str, Any]) -> str:
        """Map one memory record onto the nearest board slot role."""
        category = str(memory.get("category") or "").strip().lower()
        truth_status = str(memory.get("truth_status") or "").strip().lower()
        state_class = str(memory.get("state_class") or "").strip().lower()
        scope = str(memory.get("scope") or "").strip().lower()
        tags = {str(tag).strip().lower() for tag in list(memory.get("tags") or [])}

        if not memory.get("active", True) or memory.get("archived_at"):
            return "slot_04"
        if category in {"foundation", "doctrine", "identity"} or truth_status == "canonical":
            return "slot_01"
        if category == "preference" or "preference" in tags:
            return "slot_06"
        if category == "signal" or truth_status in {"signal", "pending"}:
            return "slot_05"
        if scope == "session" or state_class == "session":
            return "slot_03"
        return "slot_02"

    def get_memory_board_snapshot(
        self,
        *,
        truth_scope: str = "live",
        _enforcer_authority: str | None = None,
    ) -> dict[str, Any]:
        """Return the current six-card board installation plus classified record counts."""
        self._require_enforcer_authority(
            "get_memory_board_snapshot",
            _enforcer_authority,
            target=truth_scope,
        )
        snapshot = build_memory_board_snapshot(self.memory_board)
        with self._lock:
            memories = self._load_memories()
        visible_memories = filter_operator_records(memories, truth_scope=truth_scope)
        counts: dict[str, int] = {slot["slot_id"]: 0 for slot in snapshot["slots"]}
        for memory in visible_memories:
            slot_id = self._classify_memory_slot(memory)
            counts[slot_id] = counts.get(slot_id, 0) + 1
        for slot in snapshot["slots"]:
            slot["record_count"] = counts.get(slot["slot_id"], 0)
        snapshot["classified_record_count"] = sum(counts.values())
        snapshot["truth_scope"] = normalize_truth_scope(truth_scope)
        snapshot["governance"] = self._board_governance_summary(limit=12)
        from src.aais_ul.runtime import wrap_runtime_snapshot

        return wrap_runtime_snapshot(snapshot)

    def install_memory_module(
        self,
        slot_id: str,
        module: dict[str, Any] | Any,
        *,
        _enforcer_authority: str | None = None,
    ) -> dict[str, Any]:
        """Install a board module only through the protected controller path."""
        self._require_enforcer_authority(
            "install_memory_module",
            _enforcer_authority,
            target=slot_id,
        )
        normalized_slot_id = str(slot_id or "").strip()
        if not normalized_slot_id:
            raise ValueError("slot_id is required")
        if isinstance(module, dict):
            memory_module = MemoryModule(**module)
        else:
            memory_module = module
        installed = self.memory_board.register_module(normalized_slot_id, memory_module)
        event = self._record_board_event(
            action="protected_install",
            slot_id=normalized_slot_id,
            source="memory_board_controller",
            detail="Memory module installed through the protected board controller path.",
            meta={
                "module_id": installed.module_id,
                "module_class": installed.module_class,
                "supported_slot": installed.supported_slot,
            },
        )
        return {
            "module": installed,
            "event": event,
            "memory_board": self.get_memory_board_snapshot(
                truth_scope="all",
                _enforcer_authority=_enforcer_authority,
            ),
        }

    def swap_memory_module(
        self,
        slot_id: str,
        module: dict[str, Any] | Any,
        *,
        migration_records: list[dict[str, Any]] | None = None,
        _enforcer_authority: str | None = None,
    ) -> dict[str, Any]:
        """Swap a board module only through the protected controller path."""
        self._require_enforcer_authority(
            "swap_memory_module",
            _enforcer_authority,
            target=slot_id,
        )
        normalized_slot_id = str(slot_id or "").strip()
        if not normalized_slot_id:
            raise ValueError("slot_id is required")
        if isinstance(module, dict):
            memory_module = MemoryModule(**module)
        else:
            memory_module = module
        result = self.memory_board.swap_module(
            normalized_slot_id,
            memory_module,
            migration_records=migration_records,
        )
        event = self._record_board_event(
            action="protected_swap",
            slot_id=normalized_slot_id,
            source="memory_board_controller",
            detail="Memory module swap completed through the protected board controller path.",
            meta=dict(result.get("event") or {}),
        )
        return {
            **result,
            "event": event,
            "memory_board": self.get_memory_board_snapshot(
                truth_scope="all",
                _enforcer_authority=_enforcer_authority,
            ),
        }

    def list_archived_memories(
        self,
        limit: int = 6,
        *,
        truth_scope: str = "live",
        _enforcer_authority: str | None = None,
    ):
        """Return the most recent archived records for operator review."""
        self._require_enforcer_authority(
            "list_archived_memories",
            _enforcer_authority,
            target=truth_scope,
        )
        with self._lock:
            memories = self._load_memories()
        archived = [memory for memory in memories if not memory.get("active", True)]
        if normalize_truth_scope(truth_scope) != "all":
            archived = [memory for memory in archived if str(memory.get("state_class") or "live") == "live"]
        archived.sort(
            key=lambda item: (
                str(item.get("updated_at") or item.get("archived_at") or item.get("created_at") or ""),
                str(item.get("id") or ""),
            ),
            reverse=True,
        )
        return archived[: max(1, min(int(limit or 6), 20))]

    def list_why_gaps(self, limit: int = 6, *, _enforcer_authority: str | None = None):
        """Return active memories that still lack a rationale field."""
        self._require_enforcer_authority(
            "list_why_gaps",
            _enforcer_authority,
            target=f"limit:{max(1, min(int(limit or 6), 20))}",
        )
        with self._lock:
            memories = self._load_memories()
        gaps = [
            {
                "id": memory.get("id"),
                "category": memory.get("category"),
                "priority": int(memory.get("priority", 0) or 0),
                "content": memory.get("content"),
                "updated_at": memory.get("updated_at"),
                "prompt": "Explain why this memory belongs in Jarvis long-term state.",
            }
            for memory in memories
            if (
                memory.get("active", True)
                and str(memory.get("state_class") or "live") == "live"
                and not self._clean_text(memory.get("why"), limit=280)
            )
        ]
        gaps.sort(
            key=lambda item: (
                int(item.get("priority") or 0),
                str(item.get("updated_at") or ""),
                str(item.get("id") or ""),
            ),
            reverse=True,
        )
        return gaps[: max(1, min(int(limit or 6), 20))]

    def suggest_merge_candidates(self, limit: int = 6, *, _enforcer_authority: str | None = None):
        """Suggest likely duplicate memories that could collapse into one canonical note."""
        self._require_enforcer_authority(
            "suggest_merge_candidates",
            _enforcer_authority,
            target=f"limit:{max(1, min(int(limit or 6), 20))}",
        )
        with self._lock:
            memories = [
                memory
                for memory in self._load_memories()
                if memory.get("active", True) and str(memory.get("state_class") or "live") == "live"
            ]

        scored = []
        for index, left in enumerate(memories):
            if left.get("merged_into"):
                continue
            left_tokens = self._memory_tokens(left)
            left_tags = set(left.get("tags") or [])
            for right in memories[index + 1 :]:
                if right.get("merged_into"):
                    continue
                right_tokens = self._memory_tokens(right)
                shared_terms = sorted(left_tokens & right_tokens)
                shared_tags = sorted(left_tags & set(right.get("tags") or []))
                same_category = str(left.get("category") or "") == str(right.get("category") or "")
                if str(left.get("content") or "").strip().lower() == str(right.get("content") or "").strip().lower():
                    continue

                score = (len(shared_tags) * 3) + len(shared_terms) + (2 if same_category else 0)
                if score < 4 and not (same_category and len(shared_terms) >= 2):
                    continue

                target, source = sorted(
                    [left, right],
                    key=lambda item: (
                        int(item.get("priority", 0) or 0),
                        1 if item.get("override") else 0,
                        1 if item.get("pinned") else 0,
                        str(item.get("updated_at") or item.get("created_at") or ""),
                    ),
                    reverse=True,
                )
                reason_parts = []
                if same_category:
                    reason_parts.append(f"Both memories are in `{target.get('category')}`.")
                if shared_tags:
                    reason_parts.append(f"Shared tags: {', '.join(shared_tags[:3])}.")
                if shared_terms:
                    reason_parts.append(f"Shared terms: {', '.join(shared_terms[:4])}.")
                scored.append(
                    {
                        "score": score,
                        "target_id": target.get("id"),
                        "source_ids": [source.get("id")],
                        "target_excerpt": _clip_text(target.get("content"), limit=110),
                        "source_excerpt": _clip_text(source.get("content"), limit=110),
                        "shared_tags": shared_tags[:4],
                        "shared_terms": shared_terms[:6],
                        "reason": " ".join(reason_parts).strip()
                        or "These active memories overlap enough to merge into one canonical note.",
                    }
                )

        scored.sort(
            key=lambda item: (
                int(item.get("score") or 0),
                str(item.get("target_id") or ""),
                str((item.get("source_ids") or [""])[0]),
            ),
            reverse=True,
        )

        suggestions = []
        used_sources = set()
        for item in scored:
            source_id = str((item.get("source_ids") or [""])[0])
            if source_id in used_sources:
                continue
            used_sources.add(source_id)
            suggestions.append(item)
            if len(suggestions) >= max(1, min(int(limit or 6), 20)):
                break
        return suggestions

    def detect_conflicts(self, limit: int = 6, *, _enforcer_authority: str | None = None):
        """Return active memories that overlap but still disagree in wording or posture."""
        self._require_enforcer_authority(
            "detect_conflicts",
            _enforcer_authority,
            target=f"limit:{max(1, min(int(limit or 6), 20))}",
        )
        with self._lock:
            memories = [
                memory
                for memory in self._load_memories()
                if memory.get("active", True) and str(memory.get("state_class") or "live") == "live"
            ]

        conflicts = []
        for index, left in enumerate(memories):
            if left.get("merged_into"):
                continue
            left_tokens = self._memory_tokens(left)
            for right in memories[index + 1 :]:
                if right.get("merged_into"):
                    continue
                shared_terms = sorted(left_tokens & self._memory_tokens(right))
                if len(shared_terms) < 2:
                    continue
                if str(left.get("category") or "") != str(right.get("category") or ""):
                    continue
                if str(left.get("content") or "").strip().lower() == str(right.get("content") or "").strip().lower():
                    continue

                reason_parts = [f"Both notes claim `{left.get('category')}` memory territory."]
                if bool(left.get("override")) != bool(right.get("override")):
                    reason_parts.append("One note is an override while the other is not.")
                if self._clean_text(left.get("why"), limit=280) != self._clean_text(right.get("why"), limit=280):
                    reason_parts.append("Their rationale fields disagree or are missing.")

                conflicts.append(
                    {
                        "memory_ids": [left.get("id"), right.get("id")],
                        "category": left.get("category"),
                        "shared_terms": shared_terms[:6],
                        "left_excerpt": _clip_text(left.get("content"), limit=100),
                        "right_excerpt": _clip_text(right.get("content"), limit=100),
                        "reason": " ".join(reason_parts),
                    }
                )
                if len(conflicts) >= max(1, min(int(limit or 6), 20)):
                    break
            if len(conflicts) >= max(1, min(int(limit or 6), 20)):
                break
        return conflicts

    def build_governance_snapshot(self, limit: int = 6, *, _enforcer_authority: str | None = None):
        """Return one compact governance layer for the Workbench memory deck."""
        self._require_enforcer_authority(
            "build_governance_snapshot",
            _enforcer_authority,
            target=f"limit:{max(1, min(int(limit or 6), 20))}",
        )
        merge_suggestions = self.suggest_merge_candidates(
            limit=limit,
            _enforcer_authority=_enforcer_authority,
        )
        conflicts = self.detect_conflicts(
            limit=limit,
            _enforcer_authority=_enforcer_authority,
        )
        why_gaps = self.list_why_gaps(
            limit=limit,
            _enforcer_authority=_enforcer_authority,
        )
        archive_review = self.list_archived_memories(
            limit=limit,
            truth_scope="live",
            _enforcer_authority=_enforcer_authority,
        )
        from src.aais_ul.runtime import wrap_runtime_snapshot

        return wrap_runtime_snapshot(
            {
                "merge_suggestions": merge_suggestions,
                "conflicts": conflicts,
                "why_gaps": why_gaps,
                "archive_review": archive_review,
                "counts": {
                    "merge_suggestions": len(merge_suggestions),
                    "conflicts": len(conflicts),
                    "why_gaps": len(why_gaps),
                    "archive_review": len(archive_review),
                },
            }
        )

    def get_relevant_memories(
        self,
        query: str,
        limit: int = 4,
        *,
        _enforcer_authority: str | None = None,
    ):
        """Fetch memories relevant to the current request without mutating memory state."""
        return self.list_memories(
            query=query,
            limit=limit,
            active=True,
            sort="priority",
            _enforcer_authority=_enforcer_authority,
        )

    def render_memory_summary(
        self,
        query: str | None = None,
        limit: int = 5,
        *,
        _enforcer_authority: str | None = None,
    ):
        """Render a compact human-readable memory summary."""
        memories = self.list_memories(
            query=query,
            limit=limit,
            active=True,
            sort="priority",
            _enforcer_authority=_enforcer_authority,
        )
        if not memories:
            return "I do not have any saved long-term memories yet."

        lines = []
        for memory in memories:
            meta = [memory.get("category")]
            if memory.get("override"):
                meta.append("override")
            if memory.get("pinned"):
                meta.append("pinned")
            lines.append(
                f"- {_clip_text(memory.get('content', ''), limit=140)}"
                f" [{' | '.join(part for part in meta if part)}]"
            )
        return "\n".join(lines)


class WorkspaceTools:
    """Safe local workspace browsing tools limited to the operator's project root."""

    def __init__(self, workspace_root: str | Path | None = None):
        self.workspace_root = Path(workspace_root) if workspace_root else None

    def _resolve_workspace_root(self):
        """Resolve the workspace root that Jarvis may inspect."""
        if os.getenv(WORKSPACE_ROOT_ENV):
            return Path(os.getenv(WORKSPACE_ROOT_ENV)).expanduser().resolve()

        if self.workspace_root is not None:
            return self.workspace_root.expanduser().resolve()

        return Path(__file__).resolve().parents[2]

    def _preferred_project_name(self):
        """Return the project folder that should rank highest in ambiguous searches."""
        configured = os.getenv(PRIMARY_PROJECT_ENV, "").strip()
        if configured:
            return configured
        try:
            workspace_root = self._resolve_workspace_root()
            if (workspace_root / "AAIS-main").is_dir():
                return "AAIS-main"
        except OSError:
            pass
        return Path(__file__).resolve().parents[1].name

    def _resolve_path(self, relative_path: str):
        """Resolve a path within the allowed workspace root."""
        root = self._resolve_workspace_root()
        candidate = (root / relative_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError("Path must stay inside the workspace root") from exc
        return candidate

    def _iter_files(self):
        """Yield candidate files under the workspace root, skipping bulky/system dirs."""
        root = self._resolve_workspace_root()

        for current_root, dirs, files in os.walk(root):
            dirs[:] = [
                directory
                for directory in dirs
                if directory not in IGNORED_DIR_NAMES and not directory.startswith(".")
            ]

            for filename in files:
                path = Path(current_root) / filename
                if self._is_text_file(path):
                    yield path

    def _is_text_file(self, path: Path):
        """Check whether a file is safe and useful to preview/search as text."""
        if not path.is_file():
            return False

        normalized = str(path).replace("/", "\\").lower()
        if "\\training\\out\\" in normalized or "\\checkpoint-" in normalized:
            return False

        if path.stat().st_size > MAX_FILE_BYTES:
            return False

        suffix = path.suffix.lower()
        if suffix in TEXT_EXTENSIONS:
            return True

        return path.name.lower().startswith("readme")

    def _read_text_file(self, path: Path, max_chars: int | None = MAX_FILE_CHARS):
        """Read a bounded text preview from disk."""
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                return handle.read() if max_chars is None else handle.read(max_chars)
        except OSError as exc:
            raise ValueError(f"Could not read file: {path.name}") from exc

    def _extract_relevant_excerpt(self, content: str, query_tokens, max_chars: int):
        """Extract a bounded excerpt centered on the best matching line."""
        if not content:
            return "", False

        best_index, best_score = _best_matching_line_index(content, query_tokens)
        if best_index is None or best_score <= 0:
            excerpt = content[:max_chars]
            return excerpt, len(content) > len(excerpt)

        lines = content.splitlines()
        start = max(0, best_index - 2)
        end = min(len(lines), best_index + 5)
        excerpt_lines = lines[start:end]
        excerpt = "\n".join(excerpt_lines).strip()

        while len(excerpt) > max_chars and len(excerpt_lines) > 1:
            excerpt_lines = excerpt_lines[:-1]
            excerpt = "\n".join(excerpt_lines).strip()

        if len(excerpt) > max_chars:
            excerpt = excerpt[:max_chars].rstrip()

        truncated = start > 0 or end < len(lines) or len(excerpt) < len(content)
        if start > 0:
            excerpt = "...\n" + excerpt
        if end < len(lines):
            excerpt = excerpt + "\n..."

        return excerpt, truncated

    def _project_name_for(self, relative_path: str):
        """Return the top-level project folder for a relative path."""
        parts = Path(relative_path).parts
        return parts[0] if parts else ""

    def list_projects(self, limit: int = 12):
        """List top-level project directories with a short README summary."""
        root = self._resolve_workspace_root()
        projects = []

        for child in sorted(root.iterdir(), key=lambda path: path.name.lower()):
            if not child.is_dir():
                continue
            if child.name in IGNORED_DIR_NAMES or child.name.startswith("."):
                continue

            readme_path = None
            for candidate_name in ("README.md", "README.txt", "README"):
                candidate = child / candidate_name
                if candidate.exists() and candidate.is_file():
                    readme_path = candidate
                    break

            summary = ""
            if readme_path is not None:
                preview = self._read_text_file(readme_path, max_chars=600)
                lines = [
                    line.strip("# ").strip()
                    for line in preview.splitlines()
                    if line.strip()
                ]
                if lines:
                    summary = _clip_text(lines[1] if len(lines) > 1 else lines[0], limit=180)

            projects.append({
                "name": child.name,
                "relative_path": child.name,
                "readme_path": str(readme_path.relative_to(root)) if readme_path else None,
                "summary": summary,
            })

        return projects[: max(1, min(limit, 50))]

    def read_file(self, relative_path: str, max_chars: int = MAX_FILE_CHARS, query: str | None = None):
        """Read a bounded preview of a text file within the workspace."""
        path = self._resolve_path(relative_path)
        if not self._is_text_file(path):
            raise ValueError("Only safe text files can be previewed")

        root = self._resolve_workspace_root()
        raw_content = self._read_text_file(path, max_chars=None)
        query_tokens = _tokenize_query(query) if query else []
        if query_tokens:
            content, truncated = self._extract_relevant_excerpt(
                raw_content,
                query_tokens,
                max_chars=max_chars,
            )
        else:
            content = raw_content[:max_chars]
            truncated = len(raw_content) > len(content)

        return {
            "relative_path": str(path.relative_to(root)),
            "project": self._project_name_for(str(path.relative_to(root))),
            "content": content,
            "truncated": truncated,
        }

    def search(
        self,
        query: str,
        limit: int = 12,
        project_name: str | None = None,
        prefer_project: str | None = None,
    ):
        """Search file names and text content within the workspace."""
        cleaned_query = " ".join(str(query or "").split()).strip()
        if not cleaned_query:
            raise ValueError("Search query is required")

        query_tokens = _tokenize_query(cleaned_query)
        if not query_tokens:
            raise ValueError("Search query is required")

        root = self._resolve_workspace_root()
        preferred_project = _normalize_name(prefer_project or self._preferred_project_name())
        project_filter = _normalize_name(project_name)
        mentioned_filenames = _mentioned_filenames(cleaned_query)
        results = []
        scanned_files = 0

        for path in self._iter_files():
            relative_path = str(path.relative_to(root))
            project_name_for_path = self._project_name_for(relative_path)
            normalized_project_name = _normalize_name(project_name_for_path)
            if project_filter and normalized_project_name != project_filter:
                continue

            scanned_files += 1
            path_score = _score_text_match(query_tokens, relative_path)
            snippet = ""
            kind = None
            score = float(path_score)
            path_parts = {part.lower() for part in Path(relative_path).parts}
            file_name = path.name.lower()

            if path_score > 0:
                kind = "path"
                snippet = f"Path match in {relative_path}"

            if mentioned_filenames and file_name in mentioned_filenames:
                score += 3.5
                if kind is None:
                    kind = "path"
                    snippet = f"Exact file match in {relative_path}"

            content = self._read_text_file(path, max_chars=None)
            lower_content = content.lower()
            content_score = _score_text_match(query_tokens, lower_content)

            if content_score > 0:
                score += content_score + 0.5
                kind = "content"
                match_index, _ = _best_matching_line_index(content, query_tokens)
                match_line = ""
                if match_index is not None:
                    lines = content.splitlines()
                    if 0 <= match_index < len(lines):
                        match_line = lines[match_index].strip()
                snippet = _clip_text(match_line or content[:180], limit=180)

            if kind is None:
                continue

            if normalized_project_name == preferred_project:
                score += 4.0
                if "src" in path_parts or "app" in path_parts:
                    score += 0.75
                if "tests" in path_parts:
                    score -= 0.25

            results.append({
                "kind": kind,
                "relative_path": relative_path,
                "project": project_name_for_path,
                "snippet": snippet,
                "score": score,
            })

        results.sort(key=lambda item: (item["score"], item["relative_path"]), reverse=True)
        return {
            "workspace_root": str(root),
            "scanned_files": scanned_files,
            "results": results[: max(1, min(limit, 50))],
        }


class SafeLocalActionRunner:
    """Bounded local actions that Jarvis may run with explicit approval."""

    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root).resolve() if project_root else Path(__file__).resolve().parents[1]

    def list_actions(self):
        """Return the stable catalog of safe local actions."""
        return [dict(action) for action in SAFE_ACTIONS.values() if action.get("listed", True)]

    def get_action(self, action_id: str):
        """Return one action definition by ID."""
        return SAFE_ACTIONS.get(_normalize_action_id(action_id))

    def _resolve_workdir(self, relative_workdir: str):
        """Resolve an action working directory inside the allowed project root."""
        workdir = (self.project_root / relative_workdir).resolve()
        try:
            workdir.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError("Action working directory must stay inside AAIS-main") from exc
        return workdir

    def _build_command(self, action_id: str):
        """Build a subprocess command for a whitelisted action."""
        normalized = _normalize_action_id(action_id)
        if normalized == "git_status":
            return ["git", "status", "--short", "--branch"]
        if normalized == "run_pytest":
            return [sys.executable, "-m", "pytest", "-q"]
        if normalized == "build_frontend":
            return ["npm", "run", "build"]
        raise ValueError(f"Unsupported action '{action_id}'")

    def _summarize_result(self, action_id: str, returncode: int, stdout: str, stderr: str):
        """Generate a short operator-facing summary for an action result."""
        if action_id == "git_status":
            lines = [line for line in stdout.splitlines() if line.strip()]
            if not lines:
                return "Git status is clean."
            if len(lines) == 1 and lines[0].startswith("## "):
                return lines[0]
            return f"Git status returned {max(0, len(lines) - 1)} change lines."

        if action_id == "run_pytest":
            output = "\n".join(line for line in (stdout + "\n" + stderr).splitlines() if line.strip())
            match = re.search(r"=+\s+(.+?)\s+in\s+[0-9.]+s\s+=+", output)
            if match:
                return match.group(1)
            return "Pytest completed." if returncode == 0 else "Pytest reported failures."

        if action_id == "build_frontend":
            output = stdout + "\n" + stderr
            if "Compiled successfully." in output:
                return "Frontend build compiled successfully."
            return "Frontend build finished." if returncode == 0 else "Frontend build reported an error."

        return "Action completed." if returncode == 0 else "Action failed."

    def execute_action(self, action_id: str):
        """Execute a whitelisted local action and capture a bounded result."""
        action = self.get_action(action_id)
        if action is None:
            raise ValueError("Unknown action")

        command = self._build_command(action["id"])
        workdir = self._resolve_workdir(action["working_directory"])
        completed = subprocess.run(
            command,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=int(action["timeout_seconds"]),
            check=False,
        )
        stdout = _clip_text(completed.stdout, limit=MAX_ACTION_OUTPUT_CHARS)
        stderr = _clip_text(completed.stderr, limit=MAX_ACTION_OUTPUT_CHARS)
        summary = self._summarize_result(action["id"], completed.returncode, completed.stdout, completed.stderr)

        return {
            "action": dict(action),
            "status": "completed" if completed.returncode == 0 else "failed",
            "exit_code": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "summary": summary,
            "ran_at": _utc_now(),
        }


class JarvisOperator:
    """Bundle persistent memory and local workspace actions for Jarvis."""

    def __init__(self, memory_path: str | Path | None = None, workspace_root: str | Path | None = None):
        self.memory_store = JarvisMemoryStore(memory_path=memory_path)
        self.memory_enforcer = MemoryBoardEnforcer(self.memory_store)
        self.workspace_tools = WorkspaceTools(workspace_root=workspace_root)
        self.evolving_workspace = EvolvingWorkspaceIntel(workspace_root=workspace_root)
        runtime_dir = Path(__file__).resolve().parents[1] / ".runtime"
        self.evolving_approval_audit = EvolvingApprovalAuditStore(runtime_dir=runtime_dir)
        self.run_ledger = RunLedger(runtime_dir=runtime_dir)
        self.change_scope = ChangeScope(self.evolving_workspace)
        self.test_oracle = TestOracle()
        self.patchforge = PatchForge()
        self.patch_preview = PatchExecutionPreview(workspace_root=workspace_root)
        self.patch_apply = PatchApplyEngine(workspace_root=workspace_root)
        self.patch_reviews = PatchReviewStore(runtime_dir=runtime_dir)
        self.memory_smith = MemorySmith(runtime_dir=runtime_dir)
        self.memory_smith.configure_governance_callbacks(
            promote=self._promote_reviewed_memory_candidate,
            expire=self._apply_memory_expiry_review,
        )
        self.provider_mind = ProviderMind()
        self.action_runner = SafeLocalActionRunner()
        self.project_infi_law = ProjectInfiLaw(run_ledger=self.run_ledger)
        self.spatial_reasoning = SpatialReasoningPlug()
        self.mystic_engine = mystic_engine
        self.v9_core_engine = v9_core_engine
        self.v10_core_engine = v10_core_engine
        self.v9_runtime = v9_runtime
        self.v10_runtime = v10_runtime
        self.capability_bridge = CapabilityServiceBridge(
            spatial_query=self.spatial_reasoning.query,
            render_spatial=self._render_spatial_reason_response,
            mystic_read=self.mystic_engine.read,
            render_mystic=self._render_mystic_reading_response,
            v9_run=self.v9_runtime.run,
            render_v9=self._render_v9_core_response,
            v10_run=self.v10_runtime.run,
            render_v10=self._render_v10_core_response,
        )
        from src.capability_bridge_universal import attach_universal_gap_adapters

        attach_universal_gap_adapters(
            self.capability_bridge,
            memory_enforcer=self.memory_enforcer,
            workspace_tools=self.workspace_tools,
            profile_detector=self.detect_workspace_profile,
            governance_layer=self.project_infi_law,
            patchforge=self.patchforge if hasattr(self, "patchforge") else None,
        )

    def list_actions(self):
        """Expose the safe action catalog to the API/UI."""
        return self.action_runner.list_actions()

    def capability_bridge_snapshot(self):
        """Expose the governed capability bridge state for runtime inspection."""
        return self.capability_bridge.snapshot()

    def build_otem_catalog(self):
        """Expose the read-only OTEM workflow and tool catalogs for operator UI surfaces."""
        return build_otem_catalog_snapshot(self.list_actions())

    def build_otem_turn_result(
        self,
        text: str,
        *,
        session_id: str | None = None,
        prior_state: dict[str, Any] | None = None,
    ):
        """Build the OTEM v2-v5 read-only result for one turn without side effects."""
        base_result = build_otem_result(text)
        if str(base_result.get("status") or "").strip().lower() == "rejected":
            return {
                **base_result,
                "version": get_frozen_otem_version(),
                "phase": "deterministic_gate_rejected",
                "operation": "rejected",
                "session_context": {
                    "active": False,
                    "operation": "rejected",
                    "task": base_result.get("task"),
                    "restated_task": base_result.get("restated_task"),
                    "plan": [],
                    "focus_step_index": None,
                    "focus_step": None,
                    "note": "No plan was generated. This preserves OTEM's reasoning-only contract.",
                    "session_scoped": True,
                    "persistent": False,
                },
                "execution_awareness": {
                    "workflow_catalog": {
                        "count": 0,
                        "templates": [],
                        "read_only": True,
                    },
                    "recent_runs": [],
                    "approval_state": {
                        "pending": False,
                        "pending_action": {},
                        "action_lifecycle": {},
                        "read_only": True,
                    },
                    "recommendations": [],
                    "conflicts": [],
                    "summary": "OTEM rejected the task before execution-aware planning began.",
                },
                "workflow_handoff": None,
                "tool_awareness": {
                    "registry": [],
                    "suggestions": [],
                    "coverage": "not_applicable",
                    "summary": "OTEM stayed tool-cold because the task was rejected before tool matching.",
                },
            }
        workflow_templates = load_workflow_template_catalog()
        tool_registry = build_tool_registry(self.list_actions())
        recent_runs = self.list_runs(session_id=session_id, limit=6, truth_scope="live") if session_id else []
        approval_state = self.get_approval_state(session_id) if session_id else None
        operation_info = classify_otem_operation(text, prior_state=prior_state)
        result = enrich_otem_result(
            base_result,
            workflow_templates=workflow_templates,
            tool_registry=tool_registry,
            recent_runs=recent_runs,
            approval_state=approval_state,
            prior_state=prior_state,
            operation_info=operation_info,
            session_bound=bool(session_id),
        )
        result["answer"] = generate_otem_reason_only_answer_with_context(
            result.get("restated_task") or result.get("task"),
            list(result.get("plan") or []),
            session_context=result.get("session_context"),
            execution_awareness=result.get("execution_awareness"),
            workflow_handoff=result.get("workflow_handoff"),
            tool_awareness=result.get("tool_awareness"),
            operation=result.get("operation"),
        )
        result["reasoning_summary"] = (
            "Jarvis produced an OTEM governed proposal-only plan with read-only workflow, run, approval, and tool awareness."
        )
        assert result.get("version") == OTEM_VERSION, f"Unexpected OTEM payload version: {result.get('version')!r}"
        if session_id and result.get("workflow_handoff"):
            from src.otem_capability import allows_execution_approval_path, capability_posture

            result["otem_capability"] = capability_posture()
            if allows_execution_approval_path():
                try:
                    from src.otem_execution_approval_bridge import maybe_enqueue_otem_execution_approval

                    queue_meta = maybe_enqueue_otem_execution_approval(session_id, result)
                    if queue_meta:
                        result["execution_approval_queue"] = queue_meta
                except Exception:
                    logger.exception(
                        "OTEM execution approval enqueue failed for session %s",
                        session_id,
                    )
        try:
            from src.otem_capability import get_otem_capability_level
            from src.rls.adapters import from_otem_justification
            from src.rls.substrate import evaluate_reasoning_graph, rls_allows_escalation
            from src.wonder.gate import evaluate_conceptual_possibility, wonder_allows_escalation

            otem_level = get_otem_capability_level()
            wonder_verdict = evaluate_conceptual_possibility(
                {
                    "packet_type": "otem_turn",
                    "spans": [{"text": str(text or ""), "field": "operator_text"}],
                },
                otem_level=otem_level,
            )
            result["wonder_gate"] = wonder_verdict
            wonder_ok = wonder_allows_escalation(wonder_verdict, otem_level=otem_level)

            rls_verdict = None
            rls_ok = True
            justification = {
                "claim": result.get("restated_task") or result.get("task"),
                "reasoning": str(result.get("reasoning_summary") or ""),
                "evidence": [],
                "reasoning_graph": result.get("reasoning_graph"),
            }
            if any(str(justification.get(k) or "").strip() for k in ("claim", "reasoning")) or justification.get(
                "reasoning_graph"
            ):
                graph = from_otem_justification(justification)
                rls_verdict = evaluate_reasoning_graph(graph, otem_level=otem_level, record_quarantine=False)
                result["rls_gate"] = rls_verdict
                rls_ok = rls_allows_escalation(rls_verdict, otem_level=otem_level)

            if not wonder_ok or not rls_ok:
                result["cannot_justify_escalation"] = True
        except Exception:
            result["cannot_justify_escalation"] = True
        return result

    def _sync_evolving_workspace(self):
        """Keep the evolving workbench rooted in the same workspace as the classic tools."""
        self.evolving_workspace.workspace_root = self.workspace_tools._resolve_workspace_root()
        return self.evolving_workspace

    def _sync_patch_preview(self):
        """Keep patch preview rooted in the same workspace as the classic tools."""
        self.patch_preview.configure_workspace_root(self.workspace_tools._resolve_workspace_root())
        return self.patch_preview

    def _sync_patch_apply(self):
        """Keep patch apply rooted in the same workspace as the classic tools."""
        self.patch_apply.configure_workspace_root(self.workspace_tools._resolve_workspace_root())
        return self.patch_apply

    def configure_runtime_dir(self, runtime_dir: str | Path | None):
        """Keep runtime-backed organs pointed at the same writable inspection root."""
        self.evolving_approval_audit.configure_runtime_dir(runtime_dir)
        self.run_ledger.configure_runtime_dir(runtime_dir)
        self.patch_reviews.configure_runtime_dir(runtime_dir)
        self.memory_smith.configure_runtime_dir(runtime_dir)
        self.v9_runtime.configure_runtime_dir(runtime_dir)
        self.v10_runtime.configure_runtime_dir(runtime_dir)

    def choose_provider_path(
        self,
        message: str,
        *,
        response_mode: str | None = None,
        mode_scope: str | None = None,
        workspace_context: dict | None = None,
        preferred_provider: str | None = None,
    ):
        """Choose the high-level Jarvis engine path for one request."""
        return self.provider_mind.choose_path(
            {
                "message": message,
                "response_mode": response_mode,
                "mode_scope": mode_scope,
                "workspace_context": workspace_context,
                "preferred_provider": preferred_provider,
            }
        )

    def detect_workspace_profile(self, path_prefix: str | None = None):
        """Expose the evolving project profile detector."""
        return self._sync_evolving_workspace().detect_project_profile(path_prefix=path_prefix)

    def list_workspace_symbols(self, query: str | None = None, limit: int = 16, path_prefix: str | None = None):
        """Expose evolving symbol discovery through the shared operator."""
        return self._sync_evolving_workspace().list_symbols(
            query=query,
            limit=limit,
            path_prefix=path_prefix,
        )

    def read_workspace_symbol(self, symbol: str, path: str | None = None, path_prefix: str | None = None):
        """Expose one evolving symbol payload through the shared operator."""
        return self._sync_evolving_workspace().read_symbol(
            symbol=symbol,
            path=path,
            path_prefix=path_prefix,
        )

    def inspect_workspace_repo_map(
        self,
        goal: str | None = None,
        focus_path: str | None = None,
        symbol: str | None = None,
        limit: int = 12,
        path_prefix: str | None = None,
    ):
        """Expose the evolving repo map inspector through the shared operator."""
        return self._sync_evolving_workspace().inspect_repo_map(
            goal=goal,
            focus_path=focus_path,
            symbol=symbol,
            limit=limit,
            path_prefix=path_prefix,
        )

    def list_approval_audit(self, session_id: str, limit: int = 20):
        """Expose the evolving-style approval audit trail for one session."""
        return self.evolving_approval_audit.list(session_id=session_id, limit=limit)

    def sync_approval_state(self, session_id: str, pending_action=None, action_lifecycle=None):
        """Persist the current approval-gated action state separately from the audit history."""
        return self.evolving_approval_audit.sync_current(
            session_id=session_id,
            pending_action=pending_action,
            action_lifecycle=action_lifecycle,
        )

    def get_approval_state(self, session_id: str):
        """Return the persisted current approval state for one session when present."""
        return self.evolving_approval_audit.get_current(session_id=session_id)

    def _build_memory_smith_lifecycle(self, lifecycle: dict[str, Any] | None) -> dict[str, Any]:
        """Enrich lifecycle payloads with explicit stale-blocker targets when they are knowable."""
        memory_lifecycle = dict(lifecycle or {})
        action_id = str(memory_lifecycle.get("action_id") or "").strip().lower()
        stage = str(memory_lifecycle.get("stage") or "").strip().lower()
        if action_id != "run_pytest" or stage not in {"executed", "failed"}:
            return memory_lifecycle
        if any(memory_lifecycle.get(field) for field in ("expire_memory_ids", "stale_blocker_memory_ids", "target_memory_ids")):
            return memory_lifecycle
        target_ids = self._list_active_stale_blocker_memory_ids()
        if target_ids:
            memory_lifecycle["expire_memory_ids"] = target_ids
        return memory_lifecycle

    def record_action_lifecycle(self, session_id: str, lifecycle: dict):
        """Persist one action lifecycle transition into the evolving audit store."""
        audit_entry = self.evolving_approval_audit.append(session_id=session_id, lifecycle=lifecycle)
        self.run_ledger.append_lifecycle(session_id=session_id, lifecycle=lifecycle)
        self.memory_smith.observe_lifecycle(
            session_id=session_id,
            lifecycle=self._build_memory_smith_lifecycle(lifecycle),
        )
        return audit_entry

    def create_run(self, session_id: str, title: str, kind: str, meta: dict | None = None):
        """Create one durable run record."""
        return self.run_ledger.create_run(session_id=session_id, title=title, kind=kind, meta=meta)

    def list_runs(self, session_id: str | None = None, limit: int = 20, truth_scope: str = "live"):
        """Expose durable run history."""
        return self.run_ledger.list_runs(session_id=session_id, limit=limit, truth_scope=truth_scope)

    def list_patch_apply_runs(self, *, review_id: str | None = None, limit: int = 12, truth_scope: str = "live"):
        """Return recent patch-apply runs, optionally narrowed to one review."""
        scoped_runs = self.run_ledger.list_runs(
            limit=max(int(limit or 12) * 4, 24),
            truth_scope=truth_scope,
        )
        filtered = []
        for run in scoped_runs:
            if str(run.get("kind") or "") != "patch_apply":
                continue
            run_review_id = str((run.get("meta") or {}).get("review_id") or "").strip()
            if review_id and run_review_id != str(review_id).strip():
                continue
            filtered.append(run)
            if len(filtered) >= max(1, min(int(limit or 12), 30)):
                break
        return filtered

    def get_latest_patch_apply_run(self, review_id: str):
        """Return the latest patch-apply run for one review when present."""
        runs = self.list_patch_apply_runs(review_id=review_id, limit=1, truth_scope="all")
        return runs[0] if runs else None

    def get_run(self, run_id: str):
        """Return one durable run record when it exists."""
        return self.run_ledger.get_run(run_id)

    def append_run_step(self, run_id: str, step: dict):
        """Append one explicit step to a durable run."""
        return self.run_ledger.append_step(run_id, step)

    def attach_run_artifact(self, run_id: str, artifact: dict):
        """Attach one artifact to a durable run."""
        return self.run_ledger.attach_artifact(run_id, artifact)

    def close_run(self, run_id: str, status: str, summary: str | None = None):
        """Close one durable run."""
        return self.run_ledger.close_run(run_id, status=status, summary=summary)

    def analyze_change_scope(
        self,
        *,
        file_path: str | None = None,
        symbol: str | None = None,
        goal: str | None = None,
        path_prefix: str | None = None,
    ):
        """Expose impact analysis through the shared operator."""
        self._sync_evolving_workspace()
        return self.change_scope.analyze_file_impact(
            file_path=file_path,
            symbol=symbol,
            goal=goal,
            path_prefix=path_prefix,
        )

    def suggest_test_plan(self, change_impact: dict, workspace_context: dict | None = None):
        """Expose minimal verification planning through the shared operator."""
        return self.test_oracle.suggest_test_plan(change_impact, workspace_context=workspace_context)

    def build_patch_plan(
        self,
        request: str,
        workspace_context: dict | None,
        *,
        change_impact: dict | None = None,
        test_plan: dict | None = None,
    ):
        """Expose review-first patch planning through the shared operator."""
        return self.patchforge.build_patch_plan(
            request,
            workspace_context,
            change_impact=change_impact,
            test_plan=test_plan,
        )

    def build_forge_context(
        self,
        task: str,
        *,
        workspace_context: dict | None = None,
        constraints=None,
        style: dict | None = None,
        language: str | None = None,
        target_scope: str | None = None,
        focus_files: list[str] | None = None,
        excluded_files: list[str] | None = None,
        change_intent: str | None = None,
        max_change_budget: str | None = None,
        validation_target: str | None = None,
        operation_mode: str | None = None,
        max_files_to_inspect: int | None = None,
        max_directory_depth: int | None = None,
        file_path_allowlist: list[str] | None = None,
        explicit_denylist: list[str] | None = None,
        no_execution_without_handoff: bool = True,
        file_limit: int = MAX_FORGE_CONTEXT_FILES,
        file_chars: int = MAX_FORGE_CONTEXT_FILE_CHARS,
    ):
        """Convert Jarvis workspace context into Forge's task-local contractor payload."""

        cleaned_task = " ".join(str(task or "").split()).strip()
        if not cleaned_task:
            raise ValueError("task is required")

        normalized_focus_files = _normalize_repo_path_list(focus_files)
        normalized_excluded_files = _normalize_repo_path_list(excluded_files)
        normalized_allowlist = _normalize_repo_path_list(file_path_allowlist)
        normalized_denylist = _normalize_repo_path_list(explicit_denylist)
        effective_allowlist = _normalize_repo_path_list([
            *normalized_focus_files,
            *normalized_allowlist,
        ])
        effective_denylist = _normalize_repo_path_list([
            *normalized_excluded_files,
            *normalized_denylist,
        ])
        resolved_max_files_to_inspect = (
            max(1, min(int(max_files_to_inspect), 12))
            if max_files_to_inspect is not None
            else None
        )
        resolved_max_directory_depth = (
            max(0, int(max_directory_depth))
            if max_directory_depth is not None
            else None
        )
        effective_file_limit = (
            min(max(1, int(file_limit)), resolved_max_files_to_inspect)
            if resolved_max_files_to_inspect is not None
            else max(1, int(file_limit))
        )

        if not isinstance(workspace_context, dict):
            workspace_context = self.build_workspace_context(
                cleaned_task,
                result_limit=max(4, effective_file_limit),
                file_limit=effective_file_limit,
                file_chars=max(400, int(file_chars)),
                reason="forge_request",
                auto_attached=False,
                force=True,
            )
        workspace_context = _filter_workspace_context_for_forge(
            workspace_context,
            allowlist=effective_allowlist or None,
            denylist=effective_denylist or None,
            max_directory_depth=resolved_max_directory_depth,
            max_files_to_inspect=resolved_max_files_to_inspect,
        )

        files = []
        seen_paths: set[str] = set()
        for file_payload in list((workspace_context or {}).get("files") or []):
            relative_path = str(file_payload.get("relative_path") or file_payload.get("path") or "").strip()
            relative_path = relative_path.replace("\\", "/")
            if not relative_path or relative_path in seen_paths:
                continue
            seen_paths.add(relative_path)
            files.append(
                {
                    "path": relative_path,
                    "content": str(file_payload.get("content") or ""),
                    "truncated": bool(file_payload.get("truncated")),
                }
            )
            if len(files) >= effective_file_limit:
                break

        if len(files) < effective_file_limit:
            for result in list((workspace_context or {}).get("results") or []):
                relative_path = str(result.get("relative_path") or "").strip()
                relative_path = relative_path.replace("\\", "/")
                if not relative_path or relative_path in seen_paths:
                    continue
                try:
                    preview = self.workspace_tools.read_file(
                        relative_path,
                        max_chars=max(400, int(file_chars)),
                        query=cleaned_task,
                    )
                except ValueError:
                    continue
                seen_paths.add(relative_path)
                files.append(
                    {
                        "path": str(preview["relative_path"]).replace("\\", "/"),
                        "content": preview["content"],
                        "truncated": bool(preview.get("truncated")),
                    }
                )
                if len(files) >= effective_file_limit:
                    break

        project_languages = list(((workspace_context or {}).get("project_profile") or {}).get("languages") or [])
        resolved_language = (
            str(language or "").strip().lower()
            or (str(project_languages[0]).strip().lower() if project_languages else "")
            or (_guess_forge_language(files[0]["path"]) if files else "")
            or None
        )
        normalized_constraints = [
            str(item).strip()
            for item in list(constraints or [])
            if str(item).strip()
        ]
        normalized_style = dict(style or {}) if isinstance(style, dict) else {}
        contractor_constraints = {
            "max_output_chars": DEFAULT_FORGE_MAX_OUTPUT_CHARS,
        }
        if resolved_language:
            contractor_constraints["language"] = resolved_language
        if normalized_style:
            contractor_constraints["style"] = normalized_style
        if normalized_constraints:
            contractor_constraints["requirements"] = normalized_constraints

        payload = {
            "files": files,
            "goal": cleaned_task,
            "constraints": contractor_constraints,
        }
        normalized_target_scope = " ".join(str(target_scope or "").split()).strip()
        normalized_change_intent = " ".join(str(change_intent or "").split()).strip()
        normalized_budget = " ".join(str(max_change_budget or "").split()).strip()
        normalized_validation_target = " ".join(str(validation_target or "").split()).strip()
        normalized_operation_mode = " ".join(str(operation_mode or "").split()).strip()
        if normalized_target_scope:
            payload["target_scope"] = normalized_target_scope
        if normalized_focus_files:
            payload["focus_files"] = normalized_focus_files
        if normalized_excluded_files:
            payload["excluded_files"] = normalized_excluded_files
        if normalized_change_intent:
            payload["change_intent"] = normalized_change_intent
        if normalized_budget:
            payload["max_change_budget"] = normalized_budget
        if normalized_validation_target:
            payload["validation_target"] = normalized_validation_target
        if normalized_operation_mode:
            payload["operation_mode"] = normalized_operation_mode
        if resolved_max_files_to_inspect is not None:
            payload["max_files_to_inspect"] = resolved_max_files_to_inspect
        if resolved_max_directory_depth is not None:
            payload["max_directory_depth"] = resolved_max_directory_depth
        if normalized_allowlist:
            payload["file_path_allowlist"] = normalized_allowlist
        if normalized_denylist:
            payload["explicit_denylist"] = normalized_denylist
        payload["no_execution_without_handoff"] = bool(no_execution_without_handoff)
        from src.aais_ul.runtime import wrap_runtime_snapshot

        return wrap_runtime_snapshot(payload)

    def summarize_forge_context(self, forge_context: dict | None):
        """Return a UI-safe Forge context summary without raw file contents."""

        context = dict(forge_context or {})
        files = []
        for file_payload in list(context.get("files") or []):
            files.append(
                {
                    "path": str(file_payload.get("path") or "").strip(),
                    "truncated": bool(file_payload.get("truncated")),
                }
            )
        return {
            "goal": context.get("goal"),
            "file_count": len(files),
            "files": files,
            "constraints": dict(context.get("constraints") or {}),
            "target_scope": context.get("target_scope"),
            "focus_files": list(context.get("focus_files") or []),
            "excluded_files": list(context.get("excluded_files") or []),
            "change_intent": context.get("change_intent"),
            "max_change_budget": context.get("max_change_budget"),
            "validation_target": context.get("validation_target"),
            "operation_mode": context.get("operation_mode"),
            "max_files_to_inspect": context.get("max_files_to_inspect"),
            "max_directory_depth": context.get("max_directory_depth"),
            "file_path_allowlist": list(context.get("file_path_allowlist") or []),
            "explicit_denylist": list(context.get("explicit_denylist") or []),
            "no_execution_without_handoff": bool(context.get("no_execution_without_handoff", True)),
        }

    def request_forge_code(
        self,
        task: str,
        *,
        kind: str = "generate_diff",
        workspace_context: dict | None = None,
        constraints=None,
        style: dict | None = None,
        language: str | None = None,
        target_scope: str | None = None,
        focus_files: list[str] | None = None,
        excluded_files: list[str] | None = None,
        change_intent: str | None = None,
        max_change_budget: str | None = None,
        validation_target: str | None = None,
        operation_mode: str | None = None,
        max_files_to_inspect: int | None = None,
        max_directory_depth: int | None = None,
        file_path_allowlist: list[str] | None = None,
        explicit_denylist: list[str] | None = None,
        no_execution_without_handoff: bool = True,
    ):
        """Call the isolated Forge contractor through HTTP and return one operator-ready payload."""

        cleaned_kind = str(kind or "").strip() or "generate_diff"
        task_id = f"forge-{uuid.uuid4().hex[:12]}"
        cleaned_task = " ".join(str(task or "").split()).strip()
        forge_context = self.build_forge_context(
            task,
            workspace_context=workspace_context,
            constraints=constraints,
            style=style,
            language=language,
            target_scope=target_scope,
            focus_files=focus_files,
            excluded_files=excluded_files,
            change_intent=change_intent,
            max_change_budget=max_change_budget,
            validation_target=validation_target,
            operation_mode=operation_mode,
            max_files_to_inspect=max_files_to_inspect,
            max_directory_depth=max_directory_depth,
            file_path_allowlist=file_path_allowlist,
            explicit_denylist=explicit_denylist,
            no_execution_without_handoff=no_execution_without_handoff,
        )
        result = forge_client.request(
            kind=cleaned_kind,
            context=forge_context,
            task_id=task_id,
        )
        law_enforcement, ul_snapshot, law_event_log = finalize_contractor_runtime_action(
            surface="forge_contractor",
            action_id=cleaned_kind,
            target=task_id,
            cisiv_stage=_infer_forge_cisiv_stage(cleaned_kind),
            result=result if isinstance(result, dict) else {},
            summary=str((result or {}).get("summary") or cleaned_task or "Forge contractor completed."),
            details={
                "task_preview": cleaned_task[:220],
                "forge_context_goal": str(forge_context.get("goal") or "")[:220],
                "operation_mode": forge_context.get("operation_mode"),
            },
            finalize_details={
                "task_id": task_id,
                "kind": cleaned_kind,
            },
        )

        return build_forge_contractor_payload(
            task_id=task_id,
            task=cleaned_task,
            kind=cleaned_kind,
            result=result,
            forge_context=forge_context,
            auto_approve=auto_approve_forge_result(result),
            law_enforcement=law_enforcement,
            ul_snapshot=ul_snapshot,
            law_event_log=law_event_log,
        )

    def request_forge_repo_manager(
        self,
        task: str,
        *,
        workspace_context: dict | None = None,
        constraints=None,
        style: dict | None = None,
        language: str | None = None,
        target_scope: str | None = None,
        focus_files: list[str] | None = None,
        excluded_files: list[str] | None = None,
        change_intent: str | None = None,
        max_change_budget: str | None = None,
        validation_target: str | None = None,
        operation_mode: str | None = None,
        max_files_to_inspect: int | None = None,
        max_directory_depth: int | None = None,
        file_path_allowlist: list[str] | None = None,
        explicit_denylist: list[str] | None = None,
        no_execution_without_handoff: bool = True,
    ):
        return self.request_forge_code(
            task,
            kind="repo_manager",
            workspace_context=workspace_context,
            constraints=constraints,
            style=style,
            language=language,
            target_scope=target_scope,
            focus_files=focus_files,
            excluded_files=excluded_files,
            change_intent=change_intent,
            max_change_budget=max_change_budget,
            validation_target=validation_target,
            operation_mode=operation_mode,
            max_files_to_inspect=max_files_to_inspect,
            max_directory_depth=max_directory_depth,
            file_path_allowlist=file_path_allowlist,
            explicit_denylist=explicit_denylist,
            no_execution_without_handoff=no_execution_without_handoff,
        )

    def request_forge_evaluation(
        self,
        mode: str,
        *,
        payload: dict | None = None,
        task_id: str | None = None,
    ):
        """Call the isolated ForgeEval service through HTTP and return one evaluator payload."""

        normalized_mode = str(mode or "").strip()
        if not normalized_mode:
            raise ValueError("mode is required")
        if payload is not None and not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        resolved_task_id = str(task_id or f"forge-eval-{uuid.uuid4().hex[:12]}")
        result = forge_eval_client.evaluate(
            mode=normalized_mode,
            payload=dict(payload or {}),
            task_id=resolved_task_id,
        )
        law_enforcement, ul_snapshot, law_event_log = finalize_contractor_runtime_action(
            surface="forge_eval",
            action_id=normalized_mode,
            target=resolved_task_id,
            cisiv_stage=_infer_forge_cisiv_stage("analyze"),
            result=result if isinstance(result, dict) else {},
            summary=str((result or {}).get("summary") or f"ForgeEval {normalized_mode} completed."),
            details={"mode": normalized_mode},
            finalize_details={"task_id": resolved_task_id, "mode": normalized_mode},
        )

        return build_forge_eval_payload(
            task_id=resolved_task_id,
            mode=normalized_mode,
            result=result,
            law_enforcement=law_enforcement,
            ul_snapshot=ul_snapshot,
            law_event_log=law_event_log,
        )

    def request_evolution_job(
        self,
        task: str,
        *,
        preset: str | None = None,
        config: dict | None = None,
        evaluation: dict | None = None,
        constraints: dict | None = None,
        job_id: str | None = None,
        jarvis_run_id: str | None = None,
    ):
        """Call the isolated EvolveEngine service through HTTP and return one operator-ready payload."""

        cleaned_task = " ".join(str(task or "").split()).strip()
        if not cleaned_task:
            raise ValueError("task is required")
        if config is not None and not isinstance(config, dict):
            raise ValueError("config must be an object")
        if evaluation is not None and not isinstance(evaluation, dict):
            raise ValueError("evaluation must be an object")
        if constraints is not None and not isinstance(constraints, dict):
            raise ValueError("constraints must be an object")

        normalized_preset = str(preset or DEFAULT_EVOLVE_PRESET).strip().lower()
        if normalized_preset not in EVOLVE_PRESET_LIBRARY:
            raise ValueError(
                f"preset must be one of: {', '.join(sorted(EVOLVE_PRESET_LIBRARY))}"
            )
        preset_payload = EVOLVE_PRESET_LIBRARY[normalized_preset]
        resolved_config = _merge_nested_dict(preset_payload.get("config"), config)
        resolved_evaluation = _merge_nested_dict(preset_payload.get("evaluation"), evaluation)
        resolved_constraints = _merge_nested_dict(preset_payload.get("constraints"), constraints)
        resolved_evaluation.setdefault("mode", "forge_eval")
        resolved_evaluation.setdefault("forge_eval_mode", "llm_rubric")
        resolved_evaluation.setdefault("candidate_field", "program")
        if not isinstance(resolved_evaluation.get("payload"), dict):
            resolved_evaluation["payload"] = {}
        payload_config = dict(resolved_evaluation.get("payload") or {})
        if not isinstance(payload_config.get("config"), dict):
            payload_config["config"] = {
                "criteria": [
                    "task alignment",
                    "clarity",
                    "bounded improvement",
                ]
            }
        resolved_evaluation["payload"] = payload_config

        result = evolve_client.evolve(
            task=cleaned_task,
            config=resolved_config,
            evaluation=resolved_evaluation,
            constraints=resolved_constraints,
            job_id=job_id,
            jarvis_run_id=jarvis_run_id,
        )

        return govern_evolution_job_payload(
            task=cleaned_task,
            preset=normalized_preset,
            result=result if isinstance(result, dict) else {},
            job_id=str(result.get("job_id") or job_id or ""),
            jarvis_run_id=jarvis_run_id,
            config=resolved_config,
            evaluation=resolved_evaluation,
            constraints=resolved_constraints,
        )

    def get_evolution_job_trace(self, job_id: str):
        """Return one evolve job trace from the isolated evolve lane."""

        normalized_job_id = str(job_id or "").strip()
        if not normalized_job_id:
            raise ValueError("job_id is required")
        return evolve_client.get_job_trace(normalized_job_id)

    def get_evolution_job_evaluations(self, job_id: str, *, limit: int = 200):
        """Return one evolve job's evaluation ledger."""

        normalized_job_id = str(job_id or "").strip()
        if not normalized_job_id:
            raise ValueError("job_id is required")
        return evolve_client.get_job_evaluations(normalized_job_id, limit=limit)

    def get_evolution_run_trace(self, jarvis_run_id: str):
        """Return evolve jobs linked to one Jarvis run trace."""

        normalized_run_id = str(jarvis_run_id or "").strip()
        if not normalized_run_id:
            raise ValueError("jarvis_run_id is required")
        return evolve_client.get_run_trace(normalized_run_id)

    def list_evolution_hall_of_fame(self, *, limit: int = 20):
        """Return the latest successful mutations."""

        return evolve_client.list_hall_of_fame(limit=limit)

    def list_evolution_hall_of_shame(self, *, limit: int = 20):
        """Return the latest failed mutations."""

        return evolve_client.list_hall_of_shame(limit=limit)

    def prune_evolution_retention(
        self,
        *,
        max_jobs: int | None = None,
        max_hall_entries: int | None = None,
        max_evaluations: int | None = None,
    ):
        """Prune retained evolve traces and mutation halls."""

        return evolve_client.prune_retention(
            max_jobs=max_jobs,
            max_hall_entries=max_hall_entries,
            max_evaluations=max_evaluations,
        )

    def list_evolution_presets(self) -> list[dict[str, Any]]:
        """Expose the bounded evolve presets Jarvis can authorize."""

        summaries = {
            "prompt_polish": "Improve prompt-like candidates with clarity and task-fit scoring.",
            "code_refine": "Improve code-like candidates with correctness and safe-scope scoring.",
            "debug_triage": "Improve debugging candidates with failure isolation and next-step scoring.",
        }
        return [
            {
                "id": preset_id,
                "label": preset_id.replace("_", " "),
                "summary": summaries.get(preset_id, "Bounded evolve preset."),
                "evaluation": dict((payload.get("evaluation") or {})),
                "constraints": dict((payload.get("constraints") or {})),
            }
            for preset_id, payload in sorted(EVOLVE_PRESET_LIBRARY.items())
        ]

    def handoff_evolution_job_to_forge(
        self,
        job_id: str,
        *,
        task: str | None = None,
        kind: str = "analyze",
    ):
        """Route one evolve winner into Forge as a review-first contractor handoff."""

        trace = self.get_evolution_job_trace(job_id)
        job = dict((trace or {}).get("job") or {})
        best_program = str(job.get("best_program") or "").strip()
        if not best_program:
            raise ValueError("The selected evolve job does not have a best candidate to hand off.")

        handoff_task = (
            " ".join(str(task or "").split()).strip()
            or f"Review the evolved winner from job {job_id} and suggest the safest next bounded improvement."
        )
        synthetic_workspace_context = {
            "project_profile": {"languages": ["markdown"]},
            "files": [
                {
                    "relative_path": f"AAIS-main/.runtime/evolve/{job_id}-winner.txt",
                    "content": best_program,
                    "truncated": False,
                }
            ],
        }
        forge_payload = self.request_forge_code(
            handoff_task,
            kind=kind,
            workspace_context=synthetic_workspace_context,
            constraints=[
                "Treat the attached evolve winner as review-only context.",
                "Do not assume the mutation is already applied to the repo.",
            ],
        )
        return {
            "job_id": str(job_id),
            "task": handoff_task,
            "handoff_target": "forge",
            "source": {
                "best_score": job.get("best_score"),
                "generations_run": job.get("generations_run"),
                "evaluations": job.get("evaluations"),
            },
            "forge": forge_payload,
        }

    def preview_patch_plan(self, patch_plan: dict):
        """Preview whether a review-first patch still aligns with the current workspace."""
        return self._sync_patch_preview().preview_plan(patch_plan)

    def build_patch_apply_action(self, review_id: str):
        """Build one contextual apply action from a persisted patch review."""
        review = self.get_patch_review(review_id)
        if not review:
            raise FileNotFoundError(f"Patch review `{review_id}` was not found.")
        base_action = dict(self.action_runner.get_action("apply_patch_review") or SAFE_ACTIONS["apply_patch_review"])
        goal = str(review.get("goal") or "").strip() or "Apply a reviewed workspace patch."
        target_files = list((review.get("patch_plan") or {}).get("target_files") or [])
        apply_gate = dict(review.get("apply_gate") or {})
        blockers = [str(item).strip() for item in list(apply_gate.get("blockers") or []) if str(item).strip()]
        summary = (
            f"Apply the accepted review for {goal}"
            if not blockers
            else f"Patch apply is blocked until review gate issues are resolved: {blockers[0]}"
        )
        base_action.update(
            {
                "review_id": review["id"],
                "review_goal": goal,
                "review_status": (review.get("current_decision") or {}).get("state"),
                "target_files": target_files,
                "description": (
                    f"{summary}. "
                    f"Targets: {len(target_files)} file(s)."
                ),
                "command_preview": f"apply reviewed patch {review['id']} to {len(target_files)} file(s)",
                "blocked": not apply_gate.get("ready", False),
                "blocked_reason": blockers[0] if blockers else "",
            }
        )
        return base_action

    def resolve_action(self, action_id: str, **context):
        """Resolve static and contextual actions through one operator surface."""
        normalized = _normalize_action_id(action_id)
        if normalized == "apply_patch_review":
            review_id = str(context.get("review_id") or "").strip()
            if not review_id:
                raise ValueError("review_id is required for apply_patch_review.")
            return self.build_patch_apply_action(review_id)
        return self.action_runner.get_action(normalized)

    def create_patch_review(self, *, session_id: str | None, patch_plan: dict):
        """Persist one review record for a PatchForge proposal."""
        review = self.patch_reviews.create_review(session_id=session_id, patch_plan=patch_plan)
        return govern_patch_review_record(
            review,
            phase="create",
            action_id="create_patch_review",
            session_id=session_id,
            details={
                "plan_id": (patch_plan or {}).get("plan_id"),
                "target_files": list((patch_plan or {}).get("target_files") or [])[:12],
            },
        )

    def _extract_external_suggestion_details(self, *sources) -> dict[str, Any]:
        """Return one normalized external-suggestion law payload from mixed sources."""
        detail_keys = (
            "external_suggestion",
            "external_suggestion_usage",
            "law_filter_applied",
            "admitted_external_form",
            "content_transfer_mode",
            "share_mode",
            "export_mode",
            "pattern_share_mode",
            "collective_share_mode",
            "copy_raw_external",
            "share_raw",
            "raw_export",
            "copy_raw",
            "copy_private_run",
            "share_private_run",
            "private_export",
            "raw_prompts",
            "raw_chat_logs",
            "raw_code",
            "raw_traces",
            "raw_documents",
        )
        details: dict[str, Any] = {}
        for source in sources:
            if not isinstance(source, dict):
                continue
            for key in detail_keys:
                value = source.get(key)
                if value in (None, "", [], {}):
                    continue
                if key == "law_filter_applied" and value is not True:
                    continue
                details[key] = value
        return details

    def list_patch_reviews(self, *, session_id: str | None = None, limit: int = 20, truth_scope: str = "live"):
        """List persisted patch review records."""
        return self.patch_reviews.list_reviews(session_id=session_id, limit=limit, truth_scope=truth_scope)

    def get_patch_review(self, review_id: str):
        """Return one patch review record when present."""
        return self.patch_reviews.get_review(review_id)

    def record_patch_review_decision(
        self,
        review_id: str,
        *,
        decision: str,
        note: str | None = None,
        target_kind: str = "plan",
        target_index: int | None = None,
    ):
        """Store one patch review decision without mutating workspace files."""
        review = self.patch_reviews.record_decision(
            review_id,
            decision=decision,
            note=note,
            target_kind=target_kind,
            target_index=target_index,
        )
        if not review:
            return review
        return govern_patch_review_record(
            review,
            phase="decision",
            action_id="record_patch_review_decision",
            details={
                "decision": decision,
                "target_kind": target_kind,
                "target_index": target_index,
            },
        )

    def _apply_patch_review_raw(self, review_id: str):
        """Apply one review-approved patch inside the workspace root without finalization policy."""
        review = self.get_patch_review(review_id)
        if not review:
            raise FileNotFoundError(f"Patch review `{review_id}` was not found.")
        preview = self.preview_patch_plan(dict(review.get("patch_plan") or {}))
        if not preview.get("ready_for_review"):
            raise ValueError(
                "Patch preview drifted from the current workspace. Review it again before apply."
            )
        result = self._sync_patch_apply().apply_review(review)
        result["preview"] = preview
        result["review"] = review
        return result

    def apply_patch_review(
        self,
        review_id: str,
        *,
        session_id: str | None = None,
        verification_evidence: dict[str, Any] | None = None,
        external_suggestion_details: dict[str, Any] | None = None,
    ):
        """Apply one review-approved patch through the shared Project Infi governance spine."""
        review = dict(self.get_patch_review(review_id) or {})
        if not review:
            raise FileNotFoundError(f"Patch review `{review_id}` was not found.")
        run_session_id = (
            str(session_id or "").strip()
            or str(review.get("session_id") or "").strip()
            or "workbench"
        )
        external_details = self._extract_external_suggestion_details(
            review.get("patch_plan") or {},
            external_suggestion_details or {},
        )
        verification_plan = {
            "recommended_tests": list((review.get("patch_plan") or {}).get("test_suggestions") or []),
            "verification_checklist": list(
                (review.get("patch_plan") or {}).get("verification_checklist") or []
            ),
        }
        run = self.create_run(
            session_id=run_session_id,
            title=f"Apply patch: {str(review.get('goal') or review_id).strip() or review_id}",
            kind="patch_apply",
            meta={
                "review_id": review_id,
                "goal": str(review.get("goal") or review_id).strip() or review_id,
                "state_class": review.get("state_class"),
                "truth_status": review.get("truth_status"),
                "cisiv_stage": infer_patch_review_cisiv_stage(phase="apply"),
            },
        )
        try:
            contract, ul_snapshot, normalized_plan = self.project_infi_law.require_contract(
                surface="repo_action",
                action_id="apply_patch_review",
                actor_id="jarvis_operator",
                actor_role="system",
                session_id=run_session_id,
                target=review_id,
                repo_change=True,
                verification_plan=verification_plan,
                run_id=run["id"],
                cisiv_stage=infer_patch_review_cisiv_stage(phase="apply"),
                details={
                    "review_id": review_id,
                    **external_details,
                },
            )
            raw_result = self._apply_patch_review_raw(review_id)
            self.append_run_step(
                run["id"],
                {
                    "kind": "preview",
                    "title": "Patch Preview",
                    "summary": raw_result["preview"].get("summary"),
                    "status": "ready" if raw_result["preview"].get("ready_for_review") else "drifted",
                    "cisiv_stage": "implementation",
                    "meta": {"review_id": review_id, "status": raw_result["preview"].get("status")},
                },
            )
            self.attach_run_artifact(
                run["id"],
                {"kind": "patch_preview", "label": "Patch preview", "payload": raw_result["preview"]},
            )
            self.append_run_step(
                run["id"],
                {
                    "kind": "apply",
                    "title": "Apply Approved Patch",
                    "summary": raw_result.get("summary"),
                    "status": "completed",
                    "cisiv_stage": "implementation",
                    "meta": {"file_count": raw_result.get("file_count"), "review_id": review_id},
                },
            )
            self.attach_run_artifact(
                run["id"],
                {"kind": "patch_apply", "label": "Patch apply", "payload": raw_result},
            )
            self.append_run_step(
                run["id"],
                {
                    "kind": "verify",
                    "title": "Verification Lane",
                    "summary": (
                        f"Verify {len(normalized_plan['verification_checklist'])} post-apply check(s)."
                        if normalized_plan["verification_checklist"]
                        else "Run the stored post-apply verification plan before closing this repo change."
                    ),
                    "status": "planned",
                    "cisiv_stage": "verification",
                    "meta": {
                        "recommended_tests": len(normalized_plan["recommended_tests"]),
                        "verification_checklist": len(normalized_plan["verification_checklist"]),
                    },
                },
            )
            self.attach_run_artifact(
                run["id"],
                {"kind": "verification_plan", "label": "Verification plan", "payload": normalized_plan},
            )
            law_enforcement, law_event_log, judgment_log, logbook_entry = self.project_infi_law.finalize_repo_change(
                contract,
                apply_result=raw_result,
                actor_id="jarvis_operator",
                actor_role="system",
                run_id=run["id"],
                verification_evidence=verification_evidence,
            )
            outcome_status = str(
                (law_enforcement.get("project_infi_layers") or {}).get("outcome", {}).get("status") or ""
            ).strip()
            governed_status = str((law_enforcement.get("governed_cycle") or {}).get("status") or "").strip()
            if outcome_status == "passed":
                final_status = "completed"
            elif outcome_status == "awaiting_verification":
                final_status = "awaiting_verification"
            else:
                final_status = governed_status or "failed"
            summary = law_enforcement["project_infi_layers"]["outcome"]["detail"] or raw_result.get("summary")
            run = self.close_run(run["id"], status=final_status, summary=summary)
            return wrap_contractor_governed_payload(
                {
                    **raw_result,
                    "status": final_status,
                    "summary": summary,
                    "run": run,
                    "verification": normalized_plan,
                    "law_enforcement": law_enforcement,
                    "ul_snapshot": ul_snapshot,
                    "law_event_log": law_event_log,
                    "judgment_log": judgment_log,
                    "logbook_entry": logbook_entry,
                    "cisiv_stage": (
                        infer_patch_review_cisiv_stage(phase="verify")
                        if final_status == "awaiting_verification"
                        else infer_patch_review_cisiv_stage(phase="apply")
                    ),
                }
            )
        except Exception:
            self.close_run(run["id"], status="failed", summary="Project Infi law blocked or failed this repo change.")
            raise

    def review_memory_candidates(self, context: dict):
        """Expose MemorySmith review passes through the shared operator."""
        return self.memory_smith.review_memory_candidates(context)

    def _classify_reviewed_memory_candidate(self, text: str) -> dict[str, Any]:
        """Map a reviewed durable candidate onto one governed memory-bank shape."""
        cleaned = " ".join(str(text or "").split()).strip()
        lowered = cleaned.lower()
        if any(token in lowered for token in ("default", "prefer", "local-first", "local first", "jarvis should", "jarvis must")):
            return {
                "category": "preference",
                "tags": ["preference", "memory_smith"],
                "priority": 82,
                "truth_status": "stable_user",
            }
        if any(token in lowered for token in ("canonical", "foundation", "identity", "doctrine")):
            return {
                "category": "foundation",
                "tags": ["foundation", "memory_smith"],
                "priority": 90,
                "truth_status": "canonical",
            }
        return {
            "category": "operational",
            "tags": ["memory_smith", "reviewed"],
            "priority": 68,
            "truth_status": "verified",
        }

    def _find_matching_active_memory(self, text: str) -> dict[str, Any] | None:
        """Return one active memory with the same normalized content when present."""
        cleaned = self._normalize_memory_match_text(text)
        if not cleaned:
            return None
        for memory in self.memory_enforcer.list_memories(
            limit=200,
            sort="updated",
            truth_scope="all",
            runtime_context="operator_runtime",
        ):
            if not memory.get("active", True):
                continue
            content = self._normalize_memory_match_text(memory.get("content"))
            if content == cleaned:
                return memory
        return None

    def _normalize_memory_match_text(self, text: str | None) -> str:
        """Return one normalized memory string for exact review matching."""
        return " ".join(str(text or "").split()).strip().lower()

    def _looks_like_stale_blocker_memory(self, text: str | None) -> bool:
        """Return whether a memory reads like stale failing-state context."""
        lowered = self._normalize_memory_match_text(text)
        if not lowered:
            return False
        blocker_terms = ("failing", "failed", "failure", "broken", "blocker", "regression")
        if any(term in lowered for term in blocker_terms):
            return True
        verification_context = ("test", "tests", "pytest", "build", "ci", "verification", "suite")
        return "red" in lowered and any(term in lowered for term in verification_context)

    def _list_active_stale_blocker_memory_ids(self) -> list[str]:
        """Return explicit ids for currently active stale-blocker memories."""
        target_ids: list[str] = []
        for memory in self.memory_enforcer.list_memories(
            limit=200,
            active=True,
            truth_scope="all",
            sort="updated",
            runtime_context="operator_runtime",
        ):
            if not self._looks_like_stale_blocker_memory(memory.get("content")):
                continue
            memory_id = str(memory.get("id") or "").strip()
            if memory_id and memory_id not in target_ids:
                target_ids.append(memory_id)
        return target_ids

    def _promote_reviewed_memory_candidate(self, memory: dict[str, Any]) -> dict[str, Any]:
        """Promote one reviewed durable note through the board-governed memory path."""
        cleaned = " ".join(str((memory or {}).get("text") or "").split()).strip()
        if not cleaned:
            return {}
        existing = self._find_matching_active_memory(cleaned)
        if existing:
            event = self.memory_enforcer.record_board_event(
                action="promote_existing",
                slot_id=self.memory_store._classify_memory_slot(existing),
                memory=existing,
                source=str((memory or {}).get("source") or "memory_smith_review"),
                detail="Reviewed durable note matched an existing governed memory, so no duplicate write was admitted.",
                runtime_context="operator_runtime",
            )
            return {
                **existing,
                "governance": event,
                "promotion_status": "existing",
            }
        classification = self._classify_reviewed_memory_candidate(cleaned)
        promoted = self.memory_enforcer.add_memory(
            cleaned,
            tags=classification["tags"],
            pinned=False,
            source=str((memory or {}).get("source") or "memory_smith_review"),
            category=classification["category"],
            priority=classification["priority"],
            active=True,
            kind="memory",
            override=False,
            scope="persistent",
            why="Admitted from a reviewed MemorySmith durable note.",
            state_class="live",
            truth_status=classification["truth_status"],
            runtime_context="operator_runtime",
        )
        try:
            from src.ul_lineage import record_lineage_event

            record_lineage_event(
                node_type="memory_promotion",
                cisiv_stage="structure",
                claim_label="asserted",
                source_module="src.jarvis_operator",
                payload={"promotion_status": "promoted", "memory_id": promoted.get("id")},
            )
        except Exception:
            pass
        return {
            **promoted,
            "governance": self.memory_store.last_board_event(),
            "promotion_status": "promoted",
        }

    def _apply_memory_expiry_review(self, expired: dict[str, Any]) -> dict[str, Any]:
        """Record one stale-memory expiry review through the board-governed archive surface."""
        message = " ".join(str((expired or {}).get("message") or "").split()).strip()
        reason = " ".join(str((expired or {}).get("reason") or "").split()).strip().lower() or "reviewed_expiry"
        archived_ids: list[str] = []
        targeting_mode = "no_targets"
        skipped_target_ids: list[str] = []
        skipped_target_texts: list[str] = []
        requested_target_ids: list[str] = []
        requested_target_texts: list[str] = []

        for item in list((expired or {}).get("target_ids") or []):
            cleaned = str(item or "").strip()
            if cleaned and cleaned not in requested_target_ids:
                requested_target_ids.append(cleaned)
        for item in list((expired or {}).get("target_texts") or []):
            cleaned = self._normalize_memory_match_text(item)
            if cleaned and cleaned not in requested_target_texts:
                requested_target_texts.append(cleaned)

        if requested_target_ids:
            targeting_mode = "explicit_id"
            for memory_id in requested_target_ids:
                memory = self.memory_enforcer.get_memory(
                    memory_id,
                    runtime_context="operator_runtime",
                )
                if not memory or not memory.get("active", True):
                    skipped_target_ids.append(memory_id)
                    continue
                archived = self.memory_enforcer.archive_memory(
                    memory_id,
                    reason="Archived after MemorySmith marked a targeted stale blocker state as expired.",
                    runtime_context="operator_runtime",
                )
                if archived:
                    archived_ids.append(str(archived.get("id") or ""))
        elif requested_target_texts:
            targeting_mode = "explicit_text"
            matched_texts: set[str] = set()
            for memory in self.memory_enforcer.list_memories(
                limit=200,
                active=True,
                truth_scope="all",
                sort="updated",
                runtime_context="operator_runtime",
            ):
                content = self._normalize_memory_match_text(memory.get("content"))
                if content not in requested_target_texts:
                    continue
                matched_texts.add(content)
                archived = self.memory_enforcer.archive_memory(
                    str(memory.get("id") or ""),
                    reason="Archived after MemorySmith matched a targeted stale blocker note by exact text.",
                    runtime_context="operator_runtime",
                )
                if archived:
                    archived_ids.append(str(archived.get("id") or ""))
            skipped_target_texts = [
                text
                for text in requested_target_texts
                if text not in matched_texts
            ]
        elif reason == "stale_blocker":
            targeting_mode = "heuristic_fallback"
            for memory in self.memory_enforcer.list_memories(
                limit=200,
                active=True,
                truth_scope="all",
                sort="updated",
                runtime_context="operator_runtime",
            ):
                if not self._looks_like_stale_blocker_memory(memory.get("content")):
                    continue
                archived = self.memory_enforcer.archive_memory(
                    str(memory.get("id") or ""),
                    reason="Archived after MemorySmith marked stale blocker state as expired.",
                    runtime_context="operator_runtime",
                )
                if archived:
                    archived_ids.append(str(archived.get("id") or ""))
        event = self.memory_enforcer.record_board_event(
            action="expiry_review",
            slot_id="slot_04",
            source="memory_smith_review",
            detail=message or "MemorySmith reviewed one stale expiry candidate.",
            meta={
                "reason": reason,
                "targeting_mode": targeting_mode,
                "requested_target_ids": requested_target_ids,
                "requested_target_texts": requested_target_texts,
                "skipped_target_ids": skipped_target_ids,
                "skipped_target_texts": skipped_target_texts,
                "archived_ids": archived_ids,
                "archived_count": len(archived_ids),
            },
            runtime_context="operator_runtime",
        )
        return {
            "reason": reason,
            "targeting_mode": targeting_mode,
            "requested_target_ids": requested_target_ids,
            "requested_target_texts": requested_target_texts,
            "skipped_target_ids": skipped_target_ids,
            "skipped_target_texts": skipped_target_texts,
            "archived_ids": archived_ids,
            "governance": event,
        }

    def _extract_memory_store_request(self, cleaned: str) -> str | None:
        """Return the requested memory text when a direct store command is present."""
        normalized = " ".join(str(cleaned or "").split()).strip()
        candidate = re.sub(r"^\s*jarvis[\s,.:;!\-]+\s*", "", normalized, flags=re.IGNORECASE)
        lowered = candidate.lower()
        for prefix in MEMORY_STORE_PREFIXES:
            if lowered.startswith(prefix):
                return candidate[len(prefix):].strip()
        return None

    def _looks_like_preference_memory(self, cleaned: str) -> bool:
        """Detect operator preference notes that are safe to store as chat-command memories."""
        lowered = " ".join(str(cleaned or "").lower().split())
        return any(term in lowered for term in MEMORY_PREFERENCE_TERMS)

    def _looks_like_governed_truth_claim(self, cleaned: str) -> bool:
        """Detect workspace or runtime truth claims that should not enter canonical memory from chat."""
        lowered = f" {' '.join(str(cleaned or '').lower().split())} "
        has_domain = any(term in lowered for term in MEMORY_GOVERNED_DOMAIN_TERMS)
        has_assertion = any(term in lowered for term in MEMORY_GOVERNED_ASSERTION_TERMS)
        return has_domain and has_assertion

    def request_memory_store(self, text: str, *, source: str = "chat-command") -> dict[str, Any]:
        """Route direct chat memory stores through one governed decision surface."""
        cleaned = " ".join(str(text or "").split()).strip()
        if not cleaned:
            return MemoryGovernanceResult(
                action="store",
                reason="terminal_rejection",
                detail="The memory request was empty, so nothing was stored.",
                next_step="no_next_step",
                requested_text=text,
            ).to_dict()

        if self._looks_like_governed_truth_claim(cleaned):
            return MemoryGovernanceResult(
                action="store",
                reason="canonical_protection",
                detail=(
                    "Governed workspace and runtime truth cannot enter live canonical memory from a chat store request."
                ),
                next_step="use_session_scope",
                requested_text=cleaned,
            ).to_dict()

        if not self._looks_like_preference_memory(cleaned):
            return MemoryGovernanceResult(
                action="store",
                reason="truth_scope_violation",
                detail=(
                    "That request did not qualify as a stable operator preference, so it was not admitted to live canonical memory."
                ),
                next_step="no_next_step",
                requested_text=cleaned,
            ).to_dict()

        memory = self.memory_enforcer.add_memory(
            cleaned,
            source=source,
            runtime_context="live_runtime",
        )
        return MemoryGovernanceResult(
            action="store",
            stored=True,
            reason="none",
            detail="Memory stored.",
            next_step="none",
            memory=memory,
            governance=self.memory_store.last_board_event(),
            requested_text=cleaned,
        ).to_dict()

    def request_memory_merge(
        self,
        *,
        target_id: str,
        source_ids,
        content: str | None = None,
        why: str | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Wrap merge requests in the same structured governance result shape."""
        normalized_target_id = str(target_id or "").strip()
        normalized_source_ids = [
            str(item).strip()
            for item in list(source_ids or [])
            if str(item).strip()
        ]
        try:
            memory = self.memory_enforcer.merge_memories(
                target_id=normalized_target_id,
                source_ids=normalized_source_ids,
                content=content,
                why=why,
                note=note,
                runtime_context="live_runtime",
            )
        except FileNotFoundError as exc:
            return MemoryGovernanceResult(
                action="merge",
                reason="terminal_rejection",
                detail=str(exc),
                next_step="no_next_step",
                target_id=normalized_target_id,
                source_ids=normalized_source_ids,
            ).to_dict()
        except ValueError as exc:
            message = " ".join(str(exc).split()).strip()
            reason = "rejected"
            next_step = "no_next_step"
            lowered = message.lower()
            if "inactive" in lowered or "archived" in lowered:
                reason = "inactive_memory"
            elif "state class" in lowered:
                reason = "state_class_mismatch"
            elif "canonical" in lowered:
                reason = "canonical_protection"
            return MemoryGovernanceResult(
                action="merge",
                reason=reason,
                detail=message,
                next_step=next_step,
                target_id=normalized_target_id,
                source_ids=normalized_source_ids,
            ).to_dict()

        if memory is None:
            return MemoryGovernanceResult(
                action="merge",
                reason="terminal_rejection",
                detail="The target memory was not found, so nothing was merged.",
                next_step="no_next_step",
                target_id=normalized_target_id,
                source_ids=normalized_source_ids,
            ).to_dict()

        return MemoryGovernanceResult(
            action="merge",
            merged=True,
            reason="none",
            detail="Memory merge completed.",
            next_step="none",
            memory=memory,
            governance=self.memory_store.last_board_event(),
            target_id=normalized_target_id,
            source_ids=normalized_source_ids,
        ).to_dict()

    def handle_tool_request(
        self,
        tool_name: str,
        args: dict | None = None,
        *,
        runtime_context: str = "live_runtime",
    ):
        """Execute one structured Jarvis tool request."""
        normalized_tool = _normalize_name(tool_name)
        payload = dict(args or {})
        return self.capability_bridge.handle_tool_request(
            normalized_tool,
            payload,
            runtime_context=runtime_context,
        )

    def _render_spatial_reason_response(self, args: dict, result: dict) -> str:
        """Render one concise human summary for a spatial reasoning result."""
        mode = _normalize_name(args.get("mode"))
        space_id = args.get("space_id") or "unnamed_space"
        if result.get("error"):
            return f"Spatial reasoning in '{space_id}' failed: {result['error']}"

        if mode == "build":
            return result.get("summary") or (
                f"Built spatial model '{space_id}' with {result.get('node_count', 0)} nodes and "
                f"{result.get('edge_count', 0)} edges."
            )

        if mode in {"add_real_world_node", "geo_node"}:
            return result.get("summary") or (
                f"Added coordinate-aware node '{result.get('node_id')}' to '{space_id}'."
            )

        if mode == "place":
            return result.get("summary") or (
                f"Placed '{result.get('entity_id')}' at '{result.get('node')}' in '{space_id}'."
            )

        if mode in {"path", "shortest_path"}:
            path = " -> ".join(result.get("path", []))
            return (
                f"Shortest path in '{space_id}' from '{result.get('from')}' to '{result.get('to')}': "
                f"{path} (distance {result.get('distance')})."
            )

        if mode in {"distance", "geo_distance"}:
            unit = result.get("unit", "meters")
            return (
                f"Straight-line distance in '{space_id}' from '{result.get('from')}' to "
                f"'{result.get('to')}': {result.get('distance'):.2f} {unit}."
            )

        if mode in {"bearing", "heading"}:
            return (
                f"Bearing from '{result.get('from')}' to '{result.get('to')}' in '{space_id}' is "
                f"{result.get('bearing_degrees'):.2f} degrees ({result.get('bearing_label')})."
            )

        if mode in {"adjacent", "adjacency", "direct_connection"}:
            if result.get("adjacent"):
                return (
                    f"'{result.get('from')}' and '{result.get('to')}' are directly connected in '{space_id}'."
                )
            return (
                f"'{result.get('from')}' and '{result.get('to')}' are not directly connected in '{space_id}'."
            )

        if mode in {"travel_time", "travel"}:
            return (
                f"Estimated travel time in '{space_id}' from '{result.get('from')}' to '{result.get('to')}' "
                f"using {result.get('route_mode')} mode at {result.get('speed_kmh')} km/h is "
                f"{result.get('travel_minutes'):.1f} minutes."
            )

        if mode in {"visibility", "line_of_sight"}:
            origin = args.get("from")
            target = args.get("to")
            if result.get("visible"):
                path = result.get("path") or []
                path_text = f" via {' -> '.join(path)}" if path else ""
                return (
                    f"Visibility from '{origin}' to '{target}' is clear in '{space_id}'"
                    f"{path_text}. Reason: {result.get('reason')}"
                )

            blockers = ", ".join(result.get("blocked_by", [])) or "unknown blockers"
            return (
                f"Visibility from '{origin}' to '{target}' is blocked in '{space_id}'. "
                f"Blocked by: {blockers}. Reason: {result.get('reason')}"
            )

        if mode in {"real_world_visibility", "geo_visibility"}:
            origin = args.get("from")
            target = args.get("to")
            if result.get("visible"):
                return (
                    f"Real-world visibility from '{origin}' to '{target}' is clear in '{space_id}'. "
                    f"Distance: {result.get('distance_meters'):.2f} meters. Reason: {result.get('reason')}"
                )

            blockers = ", ".join(result.get("blocked_by", [])) or "unknown blockers"
            return (
                f"Real-world visibility from '{origin}' to '{target}' is blocked in '{space_id}'. "
                f"Blocked by: {blockers}. Reason: {result.get('reason')}"
            )

        return f"Spatial reasoning ran in '{space_id}'."

    def _render_mystic_reading_response(self, reading: dict) -> str:
        """Render one concise human summary for a Mystic reading."""
        state = reading.get("state_label") or reading.get("state") or "Seeking"
        dominant = reading.get("dominant_archetype_label") or reading.get("dominant_archetype") or "Witness"
        opposing = reading.get("opposing_archetype_label") or reading.get("opposing_archetype") or "Trickster"
        trial = reading.get("trial") or "Action vs avoidance"
        next_action = reading.get("next_action") or "Choose one small action and complete it fully."
        return (
            f"Mystic reading: {state} is active. {dominant} leads, opposed by {opposing}. "
            f"Trial: {trial}. Next action: {next_action}"
        )

    def _render_v9_core_response(self, result: dict) -> str:
        """Render one concise human summary for a V9 Core run."""
        if result.get("status") == "failed":
            return f"V9 Core could not run: {result.get('error', 'Unknown error')}"
        pipeline = " -> ".join(result.get("pipeline") or [])
        output = str(result.get("output") or "").strip()
        location = result.get("location") or "Unknown"
        if not output:
            return f"V9 Core ran the pipeline at {location}, but no scene text was returned."
        return f"V9 Core ran {pipeline} at {location}.\n\n{output}"

    def _render_v10_core_response(self, result: dict) -> str:
        """Render one concise human summary for a V10 Core run."""
        if result.get("status") == "failed":
            return f"V10 Core could not run: {result.get('error', 'Unknown error')}"
        pipeline = " -> ".join(result.get("pipeline") or [])
        output = str(result.get("output") or "").strip()
        score = (result.get("quality_report") or {}).get("quality_score")
        readiness = (result.get("quality_report") or {}).get("readiness") or "draft"
        location = result.get("location") or "Unknown"
        if not output:
            return f"V10 Core ran the pipeline at {location}, but no scene text was returned."
        score_suffix = f" Score {score}/100." if score is not None else ""
        return (
            f"V10 Core ran {pipeline} at {location}. Readiness: {readiness}.{score_suffix}\n\n"
            f"{output}"
        )

    def _parse_tool_payload(self, text: str):
        """Parse one JSON tool envelope pasted directly into chat."""
        candidate = str(text or "").strip()
        if not candidate.startswith("{") or not candidate.endswith("}"):
            return None

        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            return None

        if not isinstance(payload, dict):
            return None

        tool_name = payload.get("tool")
        args = payload.get("args")
        if not tool_name or not isinstance(args, dict):
            return None

        return {"tool": tool_name, "args": args}

    def _suggest_action(self, text: str, response_mode: str | None = None):
        """Suggest a safe local action from natural language."""
        lower = str(text or "").lower()
        normalized_mode = _normalize_mode_name(response_mode)

        for action_id, patterns in ACTION_REQUEST_PATTERNS.items():
            if any(pattern in lower for pattern in patterns):
                if action_id == "git_status" and not any(
                    token in lower for token in ("git", "repo", "branch", "status", "working tree")
                ):
                    continue
                action = self.action_runner.get_action(action_id)
                return {
                    "response": (
                        f"I can {action['description'].lower()} "
                        "Approval is required before I run it."
                    ),
                    "tool_result": {"type": "action_request", "action": action},
                }

        if normalized_mode != "operator":
            return None

        mode_hints = MODE_ACTION_HINTS.get(normalized_mode, {})
        for action_id, hints in mode_hints.items():
            if any(hint in lower for hint in hints):
                action = self.action_runner.get_action(action_id)
                if not action:
                    continue
                return {
                    "response": (
                        f"{action['label']} looks like the safest next operator move in {normalized_mode} mode. "
                        "Approval is required before I run it."
                    ),
                    "tool_result": {"type": "action_request", "action": action},
                }

        return None

    def _handle_explicit_forge_execution(self, text: str, response_mode: str | None = None):
        """Route explicit Forge execution requests through the contractor boundary."""
        matched_trigger = _detect_forge_execution_trigger(text)
        if not matched_trigger:
            return None

        active_lane = _resolve_active_lane(response_mode)
        lane_guardrail = _arbitrate_lane_transition(
            active_lane=active_lane,
            target_lane=LANE_FORGE,
            requests_forge_execution=bool(matched_trigger),
            operator_override=active_lane == LANE_OPERATOR,
            response_mode=response_mode,
        )
        task = _extract_forge_task(text, matched_trigger)
        if not lane_guardrail["allowed"]:
            return {
                "response": f"Forge was explicitly requested, but {lane_guardrail['summary']}",
                "tool_result": {
                    "type": "lane_guardrail",
                    "status": "blocked",
                    "summary": "Jarvis blocked the requested Forge handoff because it crossed the active lane guardrails.",
                    "lane_guardrail": lane_guardrail,
                    "forge": {
                        "task": task or text,
                        "matched_trigger": matched_trigger,
                    },
                },
            }

        workspace_context = self.build_workspace_context(
            task or text,
            result_limit=6,
            file_limit=4,
            file_chars=1800,
            reason="forge_request",
            auto_attached=False,
            force=True,
        )

        try:
            forge_payload = self.request_forge_code(
                task or text,
                workspace_context=workspace_context,
            )
        except RuntimeError as exc:
            return {
                "response": (
                    f"Forge was explicitly requested, so I held the turn on the contractor path. "
                    f"Forge routing failed: {exc}"
                ),
                "tool_result": {
                    "type": "forge_error",
                    "status": "failed",
                    "summary": "Forge was explicitly requested, but the contractor route could not be reached.",
                    "forge": {
                        "task": task or text,
                        "matched_trigger": matched_trigger,
                        "lane_guardrail": lane_guardrail,
                        "workspace_context": workspace_context,
                        "error": str(exc),
                    },
                },
            }

        forge_context = self.summarize_forge_context(forge_payload.get("forge_context"))
        contractor_result = dict(forge_payload.get("result") or {})
        diff_entries = list((contractor_result.get("result") or {}).get("diffs") or [])
        changed_paths = [
            str(entry.get("path") or "").strip()
            for entry in diff_entries
            if str(entry.get("path") or "").strip()
        ]
        response_parts = [
            f"Forge handled the request: {_clip_text(task or text, limit=180)}.",
            f"Attached {forge_context.get('file_count', 0)} workspace file preview(s) to the contractor envelope.",
        ]
        if changed_paths:
            response_parts.append(
                "Returned diffs for "
                + ", ".join(changed_paths[:4])
                + (", ..." if len(changed_paths) > 4 else ".")
            )
        elif contractor_result.get("ok"):
            response_parts.append("Forge returned a contractor result without falling back to an internal build path.")

        return {
            "response": " ".join(response_parts),
            "tool_result": {
                "type": "forge_result",
                "status": "completed" if contractor_result.get("ok", True) else "failed",
                "summary": "Jarvis routed the turn through Forge because the operator explicitly requested Forge execution.",
                "forge": {
                    "task_id": forge_payload.get("task_id"),
                    "task": forge_payload.get("task"),
                    "kind": forge_payload.get("kind"),
                    "matched_trigger": matched_trigger,
                    "lane_guardrail": lane_guardrail,
                    "auto_approve": bool(forge_payload.get("auto_approve")),
                    "workspace_context": workspace_context,
                    "forge_context": forge_context,
                    "result": contractor_result,
                },
            },
        }

    def execute_action(
        self,
        action_id: str,
        action=None,
        session_id: str | None = None,
        cognitive_bridge: dict[str, Any] | None = None,
    ):
        """Execute a safe action and wrap it for chat/UI consumption."""
        normalized = _normalize_action_id(action_id)
        action_payload = dict(action or {})
        external_details = self._extract_external_suggestion_details(action_payload)
        if normalized == "apply_patch_review":
            review_id = str(action_payload.get("review_id") or "").strip()
            if not review_id:
                raise ValueError("review_id is required to apply a reviewed patch.")
            patch_apply = self.apply_patch_review(
                review_id,
                session_id=session_id,
                external_suggestion_details=external_details,
            )
            result = {
                "action": self.build_patch_apply_action(review_id),
                "status": patch_apply.get("status"),
                "exit_code": 0,
                "stdout": "",
                "stderr": "",
                "summary": patch_apply.get("summary"),
                "ran_at": _utc_now(),
                "patch_apply": patch_apply,
                "law_enforcement": dict(patch_apply.get("law_enforcement") or {}),
                "ul_snapshot": dict(patch_apply.get("ul_snapshot") or {}),
                "law_event_log": dict(patch_apply.get("law_event_log") or {}),
            }
            if cognitive_bridge:
                result["cognitive_bridge"] = dict(cognitive_bridge)
            result["stdout"] = json.dumps(result["patch_apply"], indent=2)
        else:
            action_definition = dict(self.action_runner.get_action(normalized) or {})
            contract, ul_snapshot, _ = self.project_infi_law.require_contract(
                surface="runtime_action",
                action_id=normalized,
                actor_id="jarvis_operator",
                actor_role="system",
                session_id=session_id,
                target=action_definition.get("id") or normalized,
                repo_change=False,
                verification_plan=None,
                run_id=None,
                cisiv_stage=_infer_action_cisiv_stage(normalized),
                details={
                    "action_label": action_definition.get("label"),
                    **external_details,
                },
            )
            result = self.action_runner.execute_action(normalized)
            action_definition = dict(result.get("action") or action_definition)
            law_enforcement, law_event_log = self.project_infi_law.finalize_runtime_action(
                contract,
                action_status=result.get("status"),
                summary=result.get("summary") or "Runtime action completed.",
                actor_id="jarvis_operator",
                actor_role="system",
                details={
                    "exit_code": result.get("exit_code"),
                    "action_label": action_definition.get("label"),
                },
            )
            result["law_enforcement"] = law_enforcement
            result["ul_snapshot"] = ul_snapshot
            result["law_event_log"] = law_event_log
            if cognitive_bridge:
                result["cognitive_bridge"] = dict(cognitive_bridge)
        response = (
            f"{result['action']['label']} finished.\n"
            f"{result['summary']}\n\n"
            f"Exit code: {result['exit_code']}"
        )

        from src.aais_ul.runtime import wrap_operator_action

        return wrap_operator_action(
            {
                "response": response,
                "tool_result": {"type": "action_result", **result},
            }
        )

    def build_workspace_context(
        self,
        text: str,
        result_limit: int = MAX_CONTEXT_RESULTS,
        file_limit: int = MAX_CONTEXT_FILES,
        file_chars: int = MAX_CONTEXT_FILE_CHARS,
        reason: str = "coding_request",
        auto_attached: bool = True,
        force: bool = False,
        query_hint: str | None = None,
    ):
        """Automatically attach relevant workspace context for coding-style prompts."""
        self._sync_evolving_workspace()
        if not force and not _looks_like_coding_request(text):
            return None

        query_source = " ".join(
            piece.strip()
            for piece in (str(text or "").strip(), str(query_hint or "").strip())
            if piece and piece.strip()
        )
        query = _build_workspace_query(query_source)
        if not query:
            return None

        preferred_project = self.workspace_tools._preferred_project_name()
        search_result = self.workspace_tools.search(
            query,
            limit=result_limit,
            project_name=preferred_project,
            prefer_project=preferred_project,
        )
        results = search_result.get("results", [])
        scoped_project = preferred_project if results else None
        if not results:
            search_result = self.workspace_tools.search(
                query,
                limit=result_limit,
                prefer_project=preferred_project,
            )
            results = search_result.get("results", [])

        if not results:
            return None

        files = []
        for result in results:
            relative_path = result.get("relative_path")
            if not relative_path:
                continue

            try:
                preview = self.workspace_tools.read_file(
                    relative_path,
                    max_chars=file_chars,
                    query=query,
                )
            except ValueError:
                continue

            files.append({
                "relative_path": preview["relative_path"],
                "project": preview["project"],
                "snippet": result.get("snippet", ""),
                "kind": result.get("kind", "content"),
                "content": preview["content"],
                "truncated": preview["truncated"],
            })

            if len(files) >= max(1, int(file_limit)):
                break

        projects = _unique_preserving_order(
            [result.get("project") for result in results if result.get("project")],
            limit=4,
        )
        result_lines = [
            f"- {result['relative_path']} ({result['kind']}): {_clip_text(result['snippet'], limit=140)}"
            for result in results[:4]
        ]
        file_blocks = []
        for file_payload in files:
            truncated_suffix = "\n[preview truncated]" if file_payload["truncated"] else ""
            file_blocks.append(
                f"[File: {file_payload['relative_path']}]\n"
                f"{file_payload['content']}"
                f"{truncated_suffix}"
            )
        project_profile = self.evolving_workspace.detect_project_profile(path_prefix=scoped_project)
        symbol_payload = self.evolving_workspace.list_symbols(
            query=query,
            limit=4,
            path_prefix=scoped_project,
        )
        symbol_hits = list(symbol_payload.get("symbols") or [])
        repo_map = self.evolving_workspace.inspect_repo_map(
            goal=query,
            focus_path=files[0]["relative_path"] if files else None,
            limit=6,
            path_prefix=scoped_project,
        )
        profile_lines = []
        if project_profile.get("languages"):
            profile_lines.append(f"Languages: {', '.join(project_profile['languages'])}")
        if project_profile.get("frameworks"):
            profile_lines.append(f"Frameworks: {', '.join(project_profile['frameworks'])}")
        if project_profile.get("test_commands"):
            profile_lines.append(
                f"Likely test commands: {', '.join(project_profile['test_commands'][:2])}"
            )
        symbol_lines = [
            f"- {item['path']}::{item['qualname']} ({item['kind']})"
            for item in symbol_hits[:4]
        ]

        prompt_sections = [
            (
                "Workspace context was forced for this mode so Jarvis can ground the answer in local code."
                if force
                else (
                    "Workspace context auto-attached for this coding request."
                    if auto_attached
                    else "Workspace context gathered deliberately for a deeper coding pass."
                )
            ),
            f"Search query: {query}",
            (
                f"Project scope: {scoped_project}"
                if scoped_project
                else "Project scope: workspace-wide fallback"
            ),
            "Use the attached context silently. Do not open with 'I found these files' and do not enumerate file paths unless the operator explicitly asks for them.",
            "Use this only when it truly helps. If it looks irrelevant, say so instead of forcing it.",
            "Do not dump raw file previews or unrelated file paths back to the operator. Summarize only the evidence you actually use.",
            "Top matches:",
            "\n".join(result_lines) or "- no matches",
        ]
        if profile_lines:
            prompt_sections.extend(["", "Project profile:", "\n".join(profile_lines)])
        if symbol_lines:
            prompt_sections.extend(["", "Relevant symbols:", "\n".join(symbol_lines)])
        if repo_map.get("summary"):
            prompt_sections.extend(["", f"Repo map: {repo_map['summary']}"])

        if file_blocks:
            prompt_sections.extend(["", "File previews:", "\n\n".join(file_blocks)])

        summary = (
            f"Attached {len(results[:4])} workspace matches"
            + (f" from {', '.join(projects)}." if projects else ".")
        )

        from src.aais_ul.runtime import wrap_runtime_snapshot

        return wrap_runtime_snapshot(
            {
                "auto_attached": auto_attached,
                "reason": reason,
                "query": query,
                "project_scope": scoped_project,
                "summary": summary,
                "projects": projects,
                "results": results[:4],
                "files": files,
                "project_profile": project_profile,
                "symbol_hits": symbol_hits,
                "repo_map": repo_map,
                "prompt_block": "\n".join(prompt_sections).strip(),
            }
        )

    def _detect_visual_debug_signals(self, text: str):
        """Extract likely debugging signals from OCR or screenshot text."""
        lower = str(text or "").lower()
        signals = []

        for signal, patterns in VISUAL_DEBUG_SIGNAL_PATTERNS.items():
            if any(pattern in lower for pattern in patterns):
                signals.append(signal)

        explicit_files = _unique_preserving_order(
            WORKSPACE_FILE_PATTERN.findall(text or ""),
            limit=6,
        )
        if explicit_files:
            signals.append("explicit_file_reference")

        return _unique_preserving_order(signals)

    def _build_visual_workspace_context(
        self,
        query: str,
        result_limit: int = 5,
        file_limit: int = 2,
        file_chars: int = 900,
        prefer_frontend: bool = False,
        preferred_component_stems=None,
    ):
        """Search the workspace using screenshot-derived text instead of chat text."""
        cleaned_query = " ".join(str(query or "").split()).strip()
        if not cleaned_query:
            return None

        preferred_project = self.workspace_tools._preferred_project_name()
        search_result = self.workspace_tools.search(
            cleaned_query,
            limit=result_limit,
            project_name=preferred_project,
            prefer_project=preferred_project,
        )
        results = search_result.get("results", [])
        scoped_project = preferred_project if results else None
        if not results:
            search_result = self.workspace_tools.search(
                cleaned_query,
                limit=result_limit,
                prefer_project=preferred_project,
            )
            results = search_result.get("results", [])

        if not results:
            return None

        if prefer_frontend:
            preferred_component_stems = {
                _compact_browser_identifier(stem)
                for stem in (preferred_component_stems or [])
                if _compact_browser_identifier(stem)
            }

            def frontend_score(result):
                relative_path = str(result.get("relative_path") or "").replace("/", "\\").lower()
                score = float(result.get("score", 0.0))
                compact_stem = _compact_browser_identifier(Path(relative_path).stem)
                if "\\frontend\\" in relative_path:
                    score += 4.0
                if "\\src\\pages\\" in relative_path:
                    score += 1.6
                if relative_path.endswith((".jsx", ".tsx", ".css")):
                    score += 0.8
                if compact_stem and compact_stem in preferred_component_stems:
                    score += 4.2
                    if "\\src\\pages\\" in relative_path and relative_path.endswith((".jsx", ".tsx")):
                        score += 4.8
                    elif "\\src\\pages\\" in relative_path and relative_path.endswith(".css"):
                        score += 2.2
                    elif "\\src\\lib\\" in relative_path:
                        score -= 2.6
                if "\\mobile\\" in relative_path:
                    score -= 2.8
                if "\\tests\\" in relative_path:
                    score -= 1.6
                return score

            results = sorted(results, key=frontend_score, reverse=True)

        files = []
        for result in results:
            relative_path = result.get("relative_path")
            if not relative_path:
                continue

            try:
                preview = self.workspace_tools.read_file(
                    relative_path,
                    max_chars=file_chars,
                    query=cleaned_query,
                )
            except ValueError:
                continue

            files.append({
                "relative_path": preview["relative_path"],
                "project": preview["project"],
                "snippet": result.get("snippet", ""),
                "kind": result.get("kind", "content"),
                "content": preview["content"],
                "truncated": preview["truncated"],
            })

            if len(files) >= max(1, int(file_limit)):
                break

        projects = _unique_preserving_order(
            [result.get("project") for result in results if result.get("project")],
            limit=4,
        )

        return {
            "query": cleaned_query,
            "project_scope": scoped_project,
            "projects": projects,
            "summary": (
                f"Matched {len(results[:4])} workspace files"
                + (f" in {', '.join(projects)}." if projects else ".")
            ),
            "results": results[:4],
            "files": files,
        }

    def _suggest_visual_action(
        self,
        surface_type: str | None,
        debug_signals,
        workspace_context=None,
        readable_targets=None,
    ):
        """Choose the safest likely next action from screenshot evidence."""
        debug_signals = set(debug_signals or [])
        readable_targets = [str(target or "").lower() for target in (readable_targets or [])]
        workspace_results = (workspace_context or {}).get("results", [])
        workspace_paths = " ".join(result.get("relative_path", "").lower() for result in workspace_results)

        if "git_state" in debug_signals or any(
            token in " ".join(readable_targets)
            for token in ("branch", "commit", "staged", "changes")
        ):
            action = self.action_runner.get_action("git_status")
            return action, "The screenshot looks like repo state or git changes, so git status is the safest first read."

        if surface_type in {"code_screenshot", "document_capture"} or debug_signals.intersection(
            {"python_traceback", "javascript_error", "test_failure"}
        ):
            action = self.action_runner.get_action("run_pytest")
            return action, "The screenshot looks code- or error-oriented, so rerunning tests is the safest verification move."

        if surface_type in {"ui_screenshot", "dashboard_or_chart"} or any(
            part in workspace_paths for part in (".jsx", ".tsx", ".css", "frontend")
        ):
            action = self.action_runner.get_action("build_frontend")
            return action, "The screenshot looks UI-facing, so a frontend build is the safest first regression check."

        if any(part in workspace_paths for part in (".py", "\\tests\\", "/tests/", "src/api.py")):
            action = self.action_runner.get_action("run_pytest")
            return action, "The screenshot clues map back to Python workspace files, so rerunning tests is the safest first check."

        return None, None

    def build_visual_operator_assist(
        self,
        analysis,
        operator_context: str | None = None,
        result_limit: int = 5,
        file_limit: int = 2,
        file_chars: int = 900,
    ):
        """Turn screenshot analysis into workspace matches and a safe next move."""
        analysis = analysis or {}
        top_matches = analysis.get("top_matches") or []
        ui_result = analysis.get("ui") or {}
        ocr_result = analysis.get("ocr") or {}
        ocr_preview = str(ocr_result.get("text_preview") or "")
        readable_targets = ui_result.get("readable_targets") or []
        layout_clues = ui_result.get("layout_clues") or []
        code_language = ui_result.get("code_language")
        surface_type = ui_result.get("surface_type")

        query_source = _unique_preserving_order(
            [
                operator_context,
                " ".join(match.get("label", "") for match in top_matches[:4]),
                " ".join(readable_targets[:6]),
                code_language,
                ocr_preview,
            ],
            limit=8,
        )
        workspace_query = _build_workspace_query(" ".join(query_source))
        workspace_context = (
            self._build_visual_workspace_context(
                workspace_query,
                result_limit=result_limit,
                file_limit=file_limit,
                file_chars=file_chars,
                prefer_frontend=surface_type in {"ui_screenshot", "dashboard_or_chart"},
            )
            if workspace_query
            else None
        )

        debug_signals = self._detect_visual_debug_signals(
            "\n".join(
                [
                    operator_context or "",
                    ocr_preview,
                    surface_type or "",
                    " ".join(readable_targets),
                ]
            )
        )
        suggested_action, action_reason = self._suggest_visual_action(
            surface_type,
            debug_signals,
            workspace_context=workspace_context,
            readable_targets=readable_targets,
        )

        next_steps = []
        if suggested_action:
            next_steps.append(
                f"Approve {suggested_action['label']} if you want Jarvis to verify the likely issue safely."
            )
        if workspace_context and workspace_context.get("results"):
            next_steps.append(
                f"Inspect {workspace_context['results'][0]['relative_path']} first because it is the strongest workspace match."
            )
        if ocr_result.get("status") == "unavailable":
            next_steps.append("Enable document vision later if you want richer text extraction from screenshots.")
        if ui_result.get("status") == "unavailable":
            next_steps.append("Enable UI understanding later if you want deeper screenshot structure analysis.")

        summary_bits = []
        if surface_type:
            summary_bits.append(f"Surface type looks like {surface_type}.")
        if debug_signals:
            summary_bits.append(f"Detected signals: {', '.join(debug_signals)}.")
        if workspace_context:
            summary_bits.append(workspace_context["summary"])
        elif workspace_query:
            summary_bits.append("No direct workspace matches were found from the screenshot clues.")
        if action_reason:
            summary_bits.append(action_reason)

        return {
            "requested": True,
            "summary": " ".join(summary_bits) if summary_bits else "Screenshot operator assist is available.",
            "surface_type": surface_type,
            "code_language": code_language,
            "debug_signals": debug_signals,
            "workspace_query": workspace_query or None,
            "workspace_context": workspace_context,
            "readable_targets": readable_targets,
            "layout_clues": layout_clues,
            "suggested_action": suggested_action,
            "action_reason": action_reason,
            "next_steps": next_steps,
        }

    def _assess_browser_expectation(self, expectation: str | None, evidence_text: str):
        """Estimate whether the rendered browser state matches the operator's expectation."""
        cleaned_expectation = " ".join(str(expectation or "").split()).strip()
        if not cleaned_expectation:
            return {
                "status": "not_provided",
                "confidence": 0.0,
                "matched_terms": [],
                "summary": "No expected browser outcome was provided for this verification pass.",
            }

        tokens = [
            token
            for token in _tokenize_query(cleaned_expectation)
            if len(token) > 2 and token not in WORKSPACE_QUERY_STOPWORDS
        ][:8]
        lower_evidence = str(evidence_text or "").lower()
        matched_terms = [token for token in tokens if token in lower_evidence]
        confidence = (len(matched_terms) / len(tokens)) if tokens else 0.0

        if confidence >= 0.65:
            status = "aligned"
            summary = "The visible browser state lines up well with the expected outcome."
        elif confidence >= 0.3:
            status = "partial"
            summary = "The browser state only partially matches the expected outcome."
        else:
            status = "mismatch"
            summary = "The visible browser state does not strongly match the expected outcome yet."

        return {
            "status": status,
            "confidence": round(confidence, 3),
            "matched_terms": matched_terms,
            "summary": summary,
        }

    def _resolve_browser_route_expectation(self, snapshot, expectation: str | None = None):
        """Resolve a manual or built-in expectation for a browser route."""
        manual_expectation = " ".join(str(expectation or "").split()).strip()
        normalized_path = _normalize_browser_path((snapshot or {}).get("path"))

        if manual_expectation:
            return {
                "source": "manual",
                "route_key": None,
                "route_label": "Manual Expectation",
                "normalized_path": normalized_path,
                "expectation": manual_expectation,
                "spec": None,
                "summary": "Using the operator's manual expected outcome for this route.",
            }

        matched_spec = next(
            (
                spec
                for spec in BROWSER_ROUTE_EXPECTATIONS
                if any(
                    normalized_path == route_path
                    or (route_path != "/" and normalized_path.startswith(f"{route_path}/"))
                    for route_path in spec["paths"]
                )
            ),
            None,
        )

        if not matched_spec:
            return {
                "source": "none",
                "route_key": None,
                "route_label": None,
                "normalized_path": normalized_path,
                "expectation": None,
                "spec": None,
                "summary": "No built-in route expectation matched this browser path.",
            }

        pieces = [f"The {matched_spec['label']} route should load cleanly."]
        if matched_spec.get("expected_headings"):
            pieces.append(
                "Expected headings include "
                + ", ".join(matched_spec["expected_headings"][:3])
                + "."
            )
        if matched_spec.get("expected_buttons"):
            pieces.append(
                "Expected controls include "
                + ", ".join(matched_spec["expected_buttons"][:3])
                + "."
            )
        if matched_spec.get("expected_keywords"):
            pieces.append(
                "The page should also suggest "
                + ", ".join(matched_spec["expected_keywords"][:4])
                + "."
            )

        return {
            "source": "auto",
            "route_key": matched_spec["key"],
            "route_label": matched_spec["label"],
            "normalized_path": normalized_path,
            "expectation": " ".join(pieces),
            "spec": matched_spec,
            "summary": f"Using the built-in expectation for {matched_spec['label']}.",
        }

    def _assess_browser_route_spec(self, expectation_spec, headings, buttons, evidence_text: str):
        """Compare the live browser output against a structured expected route signature."""
        if not expectation_spec:
            return {
                "status": "not_available",
                "confidence": 0.0,
                "matched_headings": [],
                "matched_buttons": [],
                "matched_keywords": [],
                "summary": "No structured route signature is available for this browser check.",
            }

        lowered_headings = [str(value or "").lower() for value in (headings or [])]
        lowered_buttons = [str(value or "").lower() for value in (buttons or [])]
        lower_evidence = str(evidence_text or "").lower()

        expected_headings = list(expectation_spec.get("expected_headings") or [])
        expected_buttons = list(expectation_spec.get("expected_buttons") or [])
        expected_keywords = list(expectation_spec.get("expected_keywords") or [])

        matched_headings = [
            heading
            for heading in expected_headings
            if any(heading.lower() in observed for observed in lowered_headings)
            or heading.lower() in lower_evidence
        ]
        matched_buttons = [
            button
            for button in expected_buttons
            if any(button.lower() in observed for observed in lowered_buttons)
            or button.lower() in lower_evidence
        ]
        matched_keywords = [
            keyword
            for keyword in expected_keywords
            if keyword.lower() in lower_evidence
        ]

        total_checks = len(expected_headings) + len(expected_buttons) + len(expected_keywords)
        matched_total = len(matched_headings) + len(matched_buttons) + len(matched_keywords)
        confidence = (matched_total / total_checks) if total_checks else 0.0

        if confidence >= 0.65:
            status = "aligned"
            summary = "The live route strongly matches the expected UI signature."
        elif confidence >= 0.3:
            status = "partial"
            summary = "The live route only partially matches the expected UI signature."
        else:
            status = "mismatch"
            summary = "The live route is missing too much of the expected UI signature."

        return {
            "status": status,
            "confidence": round(confidence, 3),
            "matched_headings": matched_headings,
            "matched_buttons": matched_buttons,
            "matched_keywords": matched_keywords,
            "summary": summary,
        }

    def _classify_browser_surface(self, snapshot, combined_text: str, debug_signals):
        """Infer the rough kind of browser surface Jarvis is verifying."""
        path = str((snapshot or {}).get("path") or "").lower()
        title = str((snapshot or {}).get("title") or "").lower()
        lower_text = f"{path} {title} {str(combined_text or '').lower()}"
        debug_set = set(debug_signals or [])

        if debug_set.intersection({"python_traceback", "javascript_error", "build_failure", "test_failure"}):
            return "code_screenshot"
        if any(token in lower_text for token in ("dashboard", "chart", "analytics", "metrics")):
            return "dashboard_or_chart"
        if any(token in lower_text for token in ("form", "settings", "profile", "history", "console", "jarvis")):
            return "ui_screenshot"
        if any(token in lower_text for token in ("api", "route", "endpoint", "json")):
            return "document_capture"
        return "ui_screenshot"

    def build_browser_verification(
        self,
        snapshot,
        expectation: str | None = None,
        result_limit: int = 5,
        file_limit: int = 2,
        file_chars: int = 900,
    ):
        """Ground a rendered browser route back to local code and the safest next action."""
        snapshot = snapshot or {}
        target_url = " ".join(str(snapshot.get("url") or "").split()).strip()
        target_path = " ".join(str(snapshot.get("path") or "").split()).strip() or "/"
        page_title = " ".join(str(snapshot.get("title") or "").split()).strip()
        headings = _unique_preserving_order(snapshot.get("headings") or [], limit=6)
        buttons = _unique_preserving_order(snapshot.get("buttons") or [], limit=8)
        alerts = _unique_preserving_order(snapshot.get("alerts") or [], limit=6)
        route_markers = _unique_preserving_order(snapshot.get("route_markers") or [], limit=6)
        main_text = _clip_text(snapshot.get("main_text") or "", limit=1000)
        dom_counts = dict(snapshot.get("dom_counts") or {})
        viewport = dict(snapshot.get("viewport") or {})
        capture_mode = str(snapshot.get("capture_mode") or "iframe").strip() or "iframe"
        load_state = str(snapshot.get("load_state") or "loaded").strip() or "loaded"

        path_terms = [
            token.replace("-", " ")
            for token in re.findall(r"[a-z0-9_-]+", target_path.lower())
            if token not in {"http", "https"}
        ]
        evidence_text = _join_text_parts(
            [
                target_path,
                page_title,
                " ".join(route_markers),
                " ".join(headings),
                " ".join(buttons[:6]),
                " ".join(alerts),
                main_text,
            ],
            limit=16,
        )
        debug_signals = self._detect_visual_debug_signals(evidence_text)
        surface_type = self._classify_browser_surface(snapshot, evidence_text, debug_signals)
        route_expectation = self._resolve_browser_route_expectation(snapshot, expectation=expectation)
        effective_expectation = route_expectation.get("expectation")
        route_spec = route_expectation.get("spec") or {}
        preferred_components = list(route_spec.get("preferred_components") or [])
        component_filename_hints = _unique_preserving_order(
            [
                f"{component}.jsx"
                for component in preferred_components
            ]
            + [
                f"{component}.css"
                for component in preferred_components
            ],
            limit=6,
        )
        expectation_fit = self._assess_browser_expectation(effective_expectation, evidence_text)
        route_expectation_fit = self._assess_browser_route_spec(
            route_spec,
            headings,
            buttons,
            evidence_text,
        )
        if route_expectation.get("source") == "auto" and route_expectation_fit["status"] != "not_available":
            expectation_fit = {
                "status": route_expectation_fit["status"],
                "confidence": route_expectation_fit["confidence"],
                "matched_terms": (
                    route_expectation_fit["matched_headings"]
                    + route_expectation_fit["matched_buttons"]
                    + route_expectation_fit["matched_keywords"]
                ),
                "summary": route_expectation_fit["summary"],
            }

        query_source = _join_text_parts(
            [
                effective_expectation,
                " ".join(component_filename_hints),
                target_path,
                " ".join(path_terms),
                route_expectation.get("route_label"),
                " ".join(route_spec.get("expected_headings") or []),
                " ".join(route_spec.get("expected_buttons") or []),
                " ".join(route_spec.get("expected_keywords") or []),
                page_title,
                " ".join(route_markers),
                " ".join(headings[:4]),
                " ".join(alerts[:3]),
                main_text,
            ],
            limit=12,
        )
        workspace_query = _build_workspace_query(query_source)
        workspace_context = (
            self._build_visual_workspace_context(
                workspace_query,
                result_limit=result_limit,
                file_limit=file_limit,
                file_chars=file_chars,
                prefer_frontend=surface_type in {"ui_screenshot", "dashboard_or_chart"},
                preferred_component_stems=[
                    *preferred_components,
                    route_expectation.get("route_label"),
                    *path_terms,
                    *(route_spec.get("expected_headings") or []),
                ],
            )
            if workspace_query
            else None
        )

        readable_targets = _unique_preserving_order(
            route_markers + headings + buttons[:6] + path_terms,
            limit=12,
        )
        suggested_action, action_reason = self._suggest_visual_action(
            surface_type,
            debug_signals,
            workspace_context=workspace_context,
            readable_targets=readable_targets,
        )

        lower_evidence = evidence_text.lower()
        status = "healthy"
        if any(hint in lower_evidence for hint in BROWSER_FAILURE_HINTS):
            status = "fail"
        elif (
            alerts
            or expectation_fit["status"] == "mismatch"
            or route_expectation_fit["status"] == "mismatch"
        ):
            status = "warning"
        elif dom_counts.get("headings", 0) == 0 and dom_counts.get("buttons", 0) == 0 and not main_text:
            status = "warning"

        summary_bits = []
        if target_path:
            summary_bits.append(f"Verified {target_path}")
        if page_title:
            summary_bits.append(f"page title: {page_title}.")
        if alerts:
            summary_bits.append(f"Visible alerts: {', '.join(alerts[:2])}.")
        else:
            summary_bits.append("No obvious browser error banners were detected.")
        if workspace_context:
            summary_bits.append(workspace_context["summary"])
        if route_expectation["source"] != "none":
            summary_bits.append(route_expectation["summary"])
        if expectation_fit["status"] != "not_provided":
            summary_bits.append(expectation_fit["summary"])
        if route_expectation_fit["status"] not in {"not_available", "aligned"}:
            summary_bits.append(route_expectation_fit["summary"])
        if action_reason:
            summary_bits.append(action_reason)

        next_steps = []
        if suggested_action:
            next_steps.append(
                f"Approve {suggested_action['label']} if you want Jarvis to verify this route through a safe local action."
            )
        if workspace_context and workspace_context.get("results"):
            next_steps.append(
                f"Inspect {workspace_context['results'][0]['relative_path']} because it is the strongest code match for this route."
            )
        if expectation_fit["status"] == "mismatch":
            next_steps.append("Compare the expected outcome against the current headings, alerts, and strongest workspace file.")
        if route_expectation_fit["status"] == "mismatch" and route_expectation.get("route_label"):
            next_steps.append(
                f"Compare the live page against the expected {route_expectation['route_label']} headings and controls."
            )
        if not alerts and not workspace_context:
            next_steps.append("Add a clearer expected outcome or verify a more specific route for stronger grounding.")

        prompt_bits = [
            f"Browser verification target: {target_path}",
            f"Page title: {page_title or 'untitled'}",
        ]
        if headings:
            prompt_bits.append(f"Headings: {', '.join(headings[:4])}")
        if alerts:
            prompt_bits.append(f"Alerts: {', '.join(alerts[:3])}")
        if workspace_context:
            prompt_bits.append(workspace_context["summary"])
        if effective_expectation:
            prompt_bits.append(f"Expected outcome: {_clip_text(effective_expectation, limit=200)}")

        return {
            "requested": True,
            "status": status,
            "summary": " ".join(summary_bits).strip(),
            "target_url": target_url,
            "target_path": target_path,
            "page_title": page_title,
            "capture_mode": capture_mode,
            "load_state": load_state,
            "surface_type": surface_type,
            "debug_signals": debug_signals,
            "expectation": effective_expectation,
            "expectation_source": route_expectation.get("source"),
            "expectation_fit": expectation_fit,
            "route_expectation": {
                "source": route_expectation.get("source"),
                "route_key": route_expectation.get("route_key"),
                "route_label": route_expectation.get("route_label"),
                "normalized_path": route_expectation.get("normalized_path"),
                "summary": route_expectation.get("summary"),
                "expected_headings": list(route_spec.get("expected_headings") or []),
                "expected_buttons": list(route_spec.get("expected_buttons") or []),
                "expected_keywords": list(route_spec.get("expected_keywords") or []),
                "fit": route_expectation_fit,
            },
            "workspace_query": workspace_query or None,
            "workspace_context": workspace_context,
            "readable_targets": readable_targets,
            "page": {
                "headings": headings,
                "buttons": buttons,
                "alerts": alerts,
                "main_text": main_text,
                "dom_counts": dom_counts,
                "viewport": viewport,
            },
            "suggested_action": suggested_action,
            "action_reason": action_reason,
            "next_steps": next_steps,
            "draft_context": "\n".join(prompt_bits).strip(),
        }

    def handle_command(
        self,
        text: str,
        response_mode: str | None = None,
        *,
        allow_approval_commands: bool = False,
        session_id: str | None = None,
        otem_state: dict[str, Any] | None = None,
    ):
        """Handle direct memory/tool commands without spending model tokens."""
        cleaned = " ".join(str(text or "").split()).strip()
        lower = cleaned.lower()

        if not cleaned:
            return None

        tool_payload = self._parse_tool_payload(text)
        if tool_payload:
            return self.handle_tool_request(tool_payload["tool"], tool_payload["args"])

        if detect_otem(cleaned):
            otem_result = self.build_otem_turn_result(
                cleaned,
                session_id=session_id,
                prior_state=otem_state,
            )
            return {
                "response": otem_result["answer"],
                "tool_result": {
                    "type": "otem",
                    "status": otem_result["status"],
                    "summary": otem_result["reasoning_summary"],
                    "otem": otem_result,
                },
            }

        explicit_forge_result = self._handle_explicit_forge_execution(
            cleaned,
            response_mode=response_mode,
        )
        if explicit_forge_result is not None:
            return explicit_forge_result

        v10_prompt = extract_v10_core_prompt(cleaned)
        if v10_prompt is not None:
            return self.handle_tool_request(
                "v10_core",
                {"input": v10_prompt or cleaned},
            )

        v9_prompt = extract_v9_core_prompt(cleaned)
        if v9_prompt is not None:
            return self.handle_tool_request(
                "v9_core",
                {"input": v9_prompt or cleaned},
            )

        mystic_prompt = extract_mystic_prompt(cleaned)
        if mystic_prompt is not None:
            return self.handle_tool_request(
                "mystic_reading",
                {"input": mystic_prompt or cleaned},
            )

        memory_request = self._extract_memory_store_request(cleaned)
        if memory_request is not None:
            decision = self.request_memory_store(memory_request, source="chat-command")
            if decision.get("stored"):
                memory = decision.get("memory") or {}
                return {
                    "response": f"Stored in long-term memory: {_clip_text(memory.get('text') or memory.get('content'), limit=120)}",
                    "tool_result": {
                        "type": "memory_add",
                        "memory": memory,
                        "decision": decision,
                        "summary": "Stored one governed operator memory.",
                    },
                }
            return {
                "response": decision.get("detail") or "Memory was not stored.",
                "tool_result": {
                    "type": "memory_rejection",
                    "status": "rejected",
                    "memory_rejection": decision,
                    "summary": "Jarvis rejected the requested memory write and left canonical memory unchanged.",
                },
            }

        if lower in {"what do you remember", "show my memories", "list my memories"}:
            try:
                memory_summary = self.memory_enforcer.render_memory_summary(
                    limit=6,
                    runtime_context="operator_runtime",
                )
            except MemoryBoardEnforcerError as exc:
                return {
                    "response": str(exc),
                    "tool_result": {
                        "type": "memory_blocked",
                        "status": "blocked",
                        "memory_enforcer": self.memory_enforcer.last_audit(),
                        "summary": "Memory listing was blocked by the governed memory gateway.",
                    },
                }
            return {
                "response": memory_summary,
                "tool_result": {"type": "memory_list", "summary": "Listed the current operator-visible memories."},
            }

        if lower.startswith("search workspace for "):
            query = cleaned[21:].strip()
            search_result = self.workspace_tools.search(query, limit=6)
            lines = [
                f"- {result['relative_path']}: {result['snippet']}"
                for result in search_result["results"]
            ]
            response = (
                "Workspace search results:\n" + "\n".join(lines)
                if lines
                else f"No workspace matches found for '{query}'."
            )
            return {
                "response": response,
                "tool_result": {"type": "workspace_search", "query": query, **search_result},
            }

        if lower.startswith("find file "):
            query = cleaned[10:].strip()
            search_result = self.workspace_tools.search(query, limit=6)
            lines = [
                f"- {result['relative_path']}: {result['snippet']}"
                for result in search_result["results"]
            ]
            response = (
                "File search results:\n" + "\n".join(lines)
                if lines
                else f"No files matched '{query}'."
            )
            return {
                "response": response,
                "tool_result": {"type": "workspace_search", "query": query, **search_result},
            }

        if lower.startswith("read file "):
            relative_path = cleaned[10:].strip()
            file_payload = self.workspace_tools.read_file(relative_path, max_chars=2200)
            response = (
                f"Preview of {file_payload['relative_path']}:\n"
                f"{_clip_text(file_payload['content'], limit=900)}"
            )
            return {
                "response": response,
                "tool_result": {"type": "workspace_file", **file_payload},
            }

        if allow_approval_commands and lower.startswith("approve action "):
            action_id = cleaned[15:].strip()
            return self.execute_action(action_id)

        suggested_action = self._suggest_action(cleaned, response_mode=response_mode)
        if suggested_action:
            return suggested_action

        return None


jarvis_operator = JarvisOperator()
