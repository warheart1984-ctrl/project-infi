"""EXPRESS domain templates for Cloud Forge (Phase 2)."""

from __future__ import annotations

from typing import Any

from src.cloud_forge.types import Rail, TaskSignature

DOMAIN_FORGE_VOSS_OS = "forge/voss/os_architecture"

DOMAIN_TEMPLATES: dict[str, dict[str, Any]] = {
    DOMAIN_FORGE_VOSS_OS: {
        "template_id": DOMAIN_FORGE_VOSS_OS,
        "pattern_class_default": "docs_explanation",
        "mutation_scope_default": "none",
        "law_signals_default": ["read_only", "docs", "governance"],
        "tool_intents": ["doc_search", "grep_code"],
        "prefetch_docs": [
            "META_ARCHITECT_LAWBOOK.md",
            "REPO_PROOF_LAW.md",
            "docs/cloud-forge-governed-accelerator-program.md",
            "docs/contracts/cloud-forge-rail-contract.md",
            "document/blueprints/PROJECT_BLUEPRINTS_MASTER.md",
        ],
        "express_model_tier": "mid",
        "summary": (
            "Governed architecture Q&A: constitutional law, Voss boundaries, "
            "Forge platform vs Cloud Forge cognitive rails."
        ),
    },
}


def get_domain_template(domain: str | None) -> dict[str, Any] | None:
    if not domain:
        return None
    return DOMAIN_TEMPLATES.get(str(domain).strip())


def apply_task_template_defaults(task: TaskSignature) -> TaskSignature:
    """Fill task defaults from domain template when domain is registered."""
    template = get_domain_template(task.domain)
    if not template:
        return task

    pattern = task.pattern_class
    if not pattern or pattern == "unknown":
        pattern = template["pattern_class_default"]
    scope = task.mutation_scope or template["mutation_scope_default"]
    intents = list(task.tool_intents) if task.tool_intents else list(template["tool_intents"])

    return TaskSignature(
        task_id=task.task_id,
        pattern_class=pattern,
        mutation_scope=scope,
        domain=task.domain,
        normalized_prompt_hash=task.normalized_prompt_hash,
        tool_intents=intents,
        context_text=task.context_text,
    )


def enrich_plan_with_template(
    plan: dict[str, Any],
    domain: str | None,
    rail: Rail | str,
) -> dict[str, Any]:
    """Attach template metadata to CognitionPlan dict for EXPRESS (or matching domain)."""
    template = get_domain_template(domain)
    if not template:
        return plan

    rail_value = rail.value if isinstance(rail, Rail) else str(rail)
    enriched = dict(plan)
    enriched["domain_template"] = template["template_id"]
    enriched["template"] = {
        "template_id": template["template_id"],
        "tool_intents": list(template["tool_intents"]),
        "prefetch_docs": list(template["prefetch_docs"]),
        "summary": template["summary"],
        "active_on_rail": rail_value,
    }
    if rail_value == Rail.EXPRESS.value:
        enriched["model_tier"] = template.get("express_model_tier", enriched.get("model_tier"))
    return enriched
