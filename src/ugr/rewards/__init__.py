"""UGR Operator Rewards — governed cognitive economy."""

from src.ugr.rewards.operator_reward_engine import (
    OperatorRewardEngine,
    build_operator_reward_engine,
)
from src.ugr.rewards.rail_credit_spend import spend_rail_credits
from src.ugr.rewards.reward_issuer import (
    issue_reward,
    rewards_audit_only,
    rewards_enabled,
    rewards_shadow_only,
)

__all__ = [
    "OperatorRewardEngine",
    "build_operator_reward_engine",
    "issue_reward",
    "rewards_enabled",
    "rewards_shadow_only",
    "rewards_audit_only",
    "spend_rail_credits",
]
