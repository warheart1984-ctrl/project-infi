"""Decision environment continuity panel — Article Q-5."""

from __future__ import annotations

from constitutional.core.articles import ARTICLE_Q5_REFERENCE
from constitutional.eck1.registers import EnvironmentRegister, load_environment_register
from constitutional.significance.decision_environment_runtime import DecisionEnvironmentState


def format_decision_environment_panel(
    env_state: DecisionEnvironmentState,
    environment_register: EnvironmentRegister | None = None,
) -> str:
    lines = [
        "",
        f"=== DECISION ENVIRONMENT PANEL ({ARTICLE_Q5_REFERENCE}) ===",
        f"Environment Health Index: {env_state.environment_health_index:.2f}",
        f"Failed Surfaces: {[f.value for f in env_state.failed_surfaces]}",
        "",
        "--- Context Loss Decisions ---",
        str(env_state.context_loss_decisions or []),
        "--- Drift Candidates ---",
        str(env_state.drift_candidates or []),
        "--- Misaligned Context ---",
        str(env_state.misaligned_context_decisions or []),
    ]
    if environment_register is not None:
        recent = environment_register.entries[-3:]
        lines.extend(
            [
                "",
                "--- ECK-1 Environment Register (recent) ---",
                str(
                    [
                        {
                            "decision_id": entry.decision_id,
                            "constraints": entry.constraints_active,
                            "factors": entry.environmental_factors,
                        }
                        for entry in recent
                    ]
                ),
            ]
        )
    lines.append("====================================\n")
    return "\n".join(lines)
