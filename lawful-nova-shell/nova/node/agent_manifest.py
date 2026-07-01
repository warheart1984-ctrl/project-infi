from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
import time
from uuid import uuid4

from fastapi import APIRouter

from nova.node.ledger import stable_hash


router = APIRouter()


AGENT_MANIFEST: dict[str, Any] = {
    "agents": {
        "coder": {
            "id": "agent-coder",
            "role": "blue_team_builder",
            "color": "blue",
            "capabilities": ["write_patches", "implement_features", "fix_tests"],
            "tools": ["coder_tool"],
            "governance": {
                "can_write_files": True,
                "can_modify_deps": True,
                "requires_review": True,
                "emits_receipts": True,
            },
        },
        "wiring": {
            "id": "agent-wiring",
            "role": "green_team_integrator",
            "color": "green",
            "capabilities": ["wire_modules", "update_manifests", "configure_routes"],
            "tools": ["wiring_tool"],
            "governance": {
                "can_write_files": True,
                "can_modify_config": True,
                "requires_review": True,
                "emits_receipts": True,
            },
        },
        "reviewer": {
            "id": "agent-reviewer",
            "role": "red_team_inspector",
            "color": "red",
            "capabilities": ["review_patches", "assess_risk", "check_invariants", "suggest_tests"],
            "tools": ["review_tool", "invariant_checker", "risk_assessor"],
            "governance": {
                "can_write_files": False,
                "can_block_actions": True,
                "emits_receipts": True,
            },
        },
        "security": {
            "id": "agent-security",
            "role": "purple_team_security",
            "color": "purple",
            "capabilities": ["scan_dependencies", "detect_secrets", "warn_destructive_ops"],
            "tools": ["secscan_tool", "secret_detector", "dependency_diff_analyzer"],
            "governance": {
                "can_write_files": False,
                "can_block_actions": True,
                "emits_receipts": True,
            },
        },
        "test_engineer": {
            "id": "agent-test",
            "role": "yellow_team_verifier",
            "color": "yellow",
            "capabilities": ["generate_tests", "strengthen_tests", "run_tests"],
            "tools": ["testgen_tool", "coverage_analyzer", "fuzz_runner"],
            "governance": {
                "can_write_files": False,
                "can_request_patches": True,
                "emits_receipts": True,
            },
        },
        "architect": {
            "id": "agent-architect",
            "role": "white_team_system_designer",
            "color": "white",
            "capabilities": ["design_architecture", "enforce_module_boundaries", "advise_governance"],
            "tools": ["archmap_tool", "module_linter", "governance_policy_advisor"],
            "governance": {
                "can_write_files": False,
                "can_veto_patches": True,
                "emits_receipts": True,
            },
        },
        "operator": {
            "id": "agent-operator",
            "role": "black_team_runtime_executor",
            "color": "black",
            "capabilities": ["run_app", "run_migrations", "run_replay", "run_benchmarks"],
            "tools": ["runtime_exec", "replay_tool", "benchmark_tool"],
            "governance": {
                "can_write_files": False,
                "emits_receipts": True,
            },
        },
        "context_builder": {
            "id": "agent-context",
            "role": "silver_team_curator",
            "color": "silver",
            "capabilities": ["pin_files", "collect_logs", "assemble_context"],
            "tools": ["context_builder"],
            "governance": {
                "can_write_files": False,
                "emits_receipts": True,
            },
        },
        "explainer": {
            "id": "agent-explainer",
            "role": "gold_team_meta_reasoner",
            "color": "gold",
            "capabilities": ["explain_patches", "explain_risks", "explain_architecture"],
            "tools": ["explain_tool"],
            "governance": {
                "can_write_files": False,
                "emits_receipts": True,
            },
        },
        "sentinel": {
            "id": "agent-sentinel",
            "role": "orange_team_governance_enforcer",
            "color": "orange",
            "capabilities": ["validate_receipts", "enforce_policy", "detect_drift", "trigger_rollback"],
            "tools": ["governance_validator", "drift_detector", "rollback_tool"],
            "governance": {
                "can_write_files": False,
                "can_block_actions": True,
                "emits_receipts": True,
            },
        },
    },
    "orchestration": {
        "status": "manifest_only",
        "guardrail": "Tools remain stateless Ring-2 invocations; color-team loops are future UI/workflow guidance, not Node-side orchestration.",
    },
}


TOOL_MANIFEST: list[dict[str, Any]] = [
    {"name": "coder_tool", "type": "governed", "scope": "code_edit", "stateless": True, "owner_agent": "agent-coder"},
    {"name": "wiring_tool", "type": "governed", "scope": "config_wiring", "stateless": True, "owner_agent": "agent-wiring"},
    {"name": "review_tool", "type": "governed", "scope": "patch_review", "stateless": True, "owner_agent": "agent-reviewer"},
    {"name": "invariant_checker", "type": "governed", "scope": "invariant_check", "stateless": True, "owner_agent": "agent-reviewer"},
    {"name": "risk_assessor", "type": "governed", "scope": "risk_assessment", "stateless": True, "owner_agent": "agent-reviewer"},
    {"name": "secscan_tool", "type": "governed", "scope": "security_scan", "stateless": True, "owner_agent": "agent-security"},
    {"name": "secret_detector", "type": "governed", "scope": "secret_detection", "stateless": True, "owner_agent": "agent-security"},
    {"name": "dependency_diff_analyzer", "type": "governed", "scope": "dependency_diff", "stateless": True, "owner_agent": "agent-security"},
    {"name": "testgen_tool", "type": "governed", "scope": "test_generation", "stateless": True, "owner_agent": "agent-test"},
    {"name": "coverage_analyzer", "type": "governed", "scope": "coverage_analysis", "stateless": True, "owner_agent": "agent-test"},
    {"name": "fuzz_runner", "type": "governed", "scope": "fuzz_testing", "stateless": True, "owner_agent": "agent-test"},
    {"name": "archmap_tool", "type": "governed", "scope": "architecture_mapping", "stateless": True, "owner_agent": "agent-architect"},
    {"name": "module_linter", "type": "governed", "scope": "module_lint", "stateless": True, "owner_agent": "agent-architect"},
    {"name": "governance_policy_advisor", "type": "governed", "scope": "policy_advice", "stateless": True, "owner_agent": "agent-architect"},
    {"name": "runtime_exec", "type": "governed", "scope": "runtime_execution", "stateless": True, "owner_agent": "agent-operator"},
    {"name": "replay_tool", "type": "governed", "scope": "replay", "stateless": True, "owner_agent": "agent-operator"},
    {"name": "benchmark_tool", "type": "governed", "scope": "benchmark", "stateless": True, "owner_agent": "agent-operator"},
    {"name": "context_builder", "type": "governed", "scope": "context_assembly", "stateless": True, "owner_agent": "agent-context"},
    {"name": "explain_tool", "type": "governed", "scope": "explanation", "stateless": True, "owner_agent": "agent-explainer"},
    {"name": "governance_validator", "type": "governed", "scope": "receipt_validation", "stateless": True, "owner_agent": "agent-sentinel"},
    {"name": "drift_detector", "type": "governed", "scope": "drift_detection", "stateless": True, "owner_agent": "agent-sentinel"},
    {"name": "rollback_tool", "type": "governed", "scope": "rollback", "stateless": True, "owner_agent": "agent-sentinel"},
]

IMPLEMENTED_TOOL_NAMES = {"coder_tool", "wiring_tool"}


@dataclass(frozen=True)
class AgentIdentity:
    id: str
    role: str
    color: str
    capabilities: list[str]
    tools: list[str]
    can_write_files: bool = False
    can_block_actions: bool = False
    can_modify_deps: bool = False
    can_modify_config: bool = False
    can_request_patches: bool = False
    can_veto_patches: bool = False
    emits_receipts: bool = True
    requires_review: bool = False


@dataclass(frozen=True)
class AgentReceipt:
    id: str
    agent_id: str
    action: str
    payload: dict[str, Any]
    policy_version: str
    trace_id: str
    timestamp: float

    def compute_output_hash(self, output: Any) -> str:
        return stable_hash(output)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentIdentity] = {}

    def register(self, agent: AgentIdentity) -> None:
        self._agents[agent.id] = agent

    def get(self, agent_id: str) -> AgentIdentity:
        return self._agents[agent_id]

    def can(self, agent_id: str, capability: str) -> bool:
        return capability in self.get(agent_id).capabilities

    def all(self) -> list[AgentIdentity]:
        return list(self._agents.values())


class CapabilityGate:
    def __init__(self, registry: AgentRegistry, policy_version: str) -> None:
        self.registry = registry
        self.policy_version = policy_version

    def authorize(self, agent_id: str, action: str, payload: dict[str, Any]) -> AgentReceipt:
        agent = self.registry.get(agent_id)
        if action == "write_files" and not agent.can_write_files:
            raise PermissionError(f"{agent_id} cannot write files")
        if action == "modify_deps" and not agent.can_modify_deps:
            raise PermissionError(f"{agent_id} cannot modify dependencies")
        if action == "modify_config" and not agent.can_modify_config:
            raise PermissionError(f"{agent_id} cannot modify config")
        if action not in _allowed_actions(agent):
            raise PermissionError(f"{agent_id} cannot perform {action}")
        return AgentReceipt(
            id=str(uuid4()),
            agent_id=agent_id,
            action=action,
            payload=payload,
            policy_version=self.policy_version,
            trace_id=str(payload.get("trace_id") or f"trace-{agent_id}"),
            timestamp=time.time(),
        )


def default_agent_registry() -> AgentRegistry:
    registry = AgentRegistry()
    for data in AGENT_MANIFEST["agents"].values():
        governance = data.get("governance") or {}
        registry.register(
            AgentIdentity(
                id=str(data["id"]),
                role=str(data["role"]),
                color=str(data["color"]),
                capabilities=list(data["capabilities"]),
                tools=list(data["tools"]),
                can_write_files=bool(governance.get("can_write_files", False)),
                can_block_actions=bool(governance.get("can_block_actions", False)),
                can_modify_deps=bool(governance.get("can_modify_deps", False)),
                can_modify_config=bool(governance.get("can_modify_config", False)),
                can_request_patches=bool(governance.get("can_request_patches", False)),
                can_veto_patches=bool(governance.get("can_veto_patches", False)),
                emits_receipts=bool(governance.get("emits_receipts", True)),
                requires_review=bool(governance.get("requires_review", False)),
            )
        )
    return registry


def tool_manifest(name: str) -> dict[str, Any] | None:
    for entry in TOOL_MANIFEST:
        if entry["name"] == name:
            return entry
    return None


def agent_tool_manifest() -> list[dict[str, Any]]:
    return [
        {
            **entry,
            "implemented": entry["name"] in IMPLEMENTED_TOOL_NAMES,
        }
        for entry in TOOL_MANIFEST
    ]


@router.get("/node/agents")
async def get_agents() -> dict[str, Any]:
    return AGENT_MANIFEST


@router.get("/node/agent-tools")
async def get_agent_tools() -> dict[str, Any]:
    return {"tools": agent_tool_manifest()}


def _allowed_actions(agent: AgentIdentity) -> set[str]:
    actions = set(agent.capabilities)
    if agent.can_write_files:
        actions.add("write_files")
    if agent.can_modify_deps:
        actions.add("modify_deps")
    if agent.can_modify_config:
        actions.add("modify_config")
    if agent.can_block_actions:
        actions.add("block_actions")
    if agent.can_request_patches:
        actions.add("request_patches")
    if agent.can_veto_patches:
        actions.add("veto_patches")
    return actions
