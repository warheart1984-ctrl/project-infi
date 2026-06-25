"""Built-in agent capability profiles (engineering names; mythic labels in docs only)."""

from __future__ import annotations

from operator_kernel.contracts import AgentProfile, TaskConstraints

BUILTIN_AGENT_PROFILES: dict[str, AgentProfile] = {
    "explorer": AgentProfile(
        id="explorer",
        label="Explorer",
        description="Read-only: list, search, and inspect files without writes or shell.",
        constraints=TaskConstraints(
            read_only=True,
            allow_shell=False,
            allow_git_commit=False,
            allow_network=False,
            max_steps=10,
        ),
    ),
    "builder": AgentProfile(
        id="builder",
        label="Builder",
        description="Edit files and run shell commands; no git commits.",
        constraints=TaskConstraints(
            read_only=False,
            allow_shell=True,
            allow_git_commit=False,
            allow_network=False,
            max_steps=16,
        ),
    ),
    "reviewer": AgentProfile(
        id="reviewer",
        label="Reviewer",
        description="Read-only analysis with search; suited for audits and explanations.",
        constraints=TaskConstraints(
            read_only=True,
            allow_shell=False,
            allow_git_commit=False,
            allow_network=False,
            max_steps=8,
        ),
    ),
}


def list_profiles() -> list[AgentProfile]:
    return list(BUILTIN_AGENT_PROFILES.values())


def get_profile(agent_id: str) -> AgentProfile | None:
    return BUILTIN_AGENT_PROFILES.get(agent_id)


def merge_constraints(profile_id: str | None, overrides: TaskConstraints) -> TaskConstraints:
    base = TaskConstraints()
    if profile_id:
        profile = get_profile(profile_id)
        if profile:
            base = profile.constraints.model_copy()
    merged = base.model_dump()
    for key, value in overrides.model_dump().items():
        if key == "max_steps" and overrides.max_steps == TaskConstraints.model_fields["max_steps"].default:
            continue
        merged[key] = value
    return TaskConstraints(**merged)
