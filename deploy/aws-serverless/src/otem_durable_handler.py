"""
OTEM governed execution — Lambda durable function.

Mirrors src/otem_temporal/workflows.py:
  wait for operator decision → substrate approve → substrate apply

Deploy as part of deploy/aws-serverless/ (SAM). At runtime, substrate calls can
target the in-process Python module when packaged with AAIS, or HTTP to the ECS API.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from aws_durable_execution_sdk_python import (
    DurableContext,
    StepContext,
    durable_execution,
    durable_step,
)
from aws_durable_execution_sdk_python.config import (
    Duration,
    StepConfig,
    WaitForCallbackConfig,
)
from aws_durable_execution_sdk_python.retries import (
    JitterStrategy,
    RetryStrategyConfig,
    create_retry_strategy,
)

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

_ACTIVITY_RETRY = StepConfig(
    retry_strategy=create_retry_strategy(
        RetryStrategyConfig(
            max_attempts=3,
            initial_delay=Duration.from_seconds(5),
            max_delay=Duration.from_seconds(60),
            backoff_rate=2.0,
            jitter_strategy=JitterStrategy.FULL,
        )
    )
)


@durable_step
def otem_substrate_approve(step_ctx: StepContext, workflow_id: str) -> dict[str, Any]:
    try:
        from src.otem_execution_substrate import get_otem_execution_substrate

        return get_otem_execution_substrate().approve(
            workflow_id,
            runtime_context=os.getenv("AAIS_RUNTIME_CONTEXT", "operator_runtime"),
        )
    except ImportError:
        step_ctx.logger.warning("substrate not in Lambda package; returning stub approve")
        return {"workflow_id": workflow_id, "status": "approved_stub"}


@durable_step
def otem_substrate_apply(step_ctx: StepContext, workflow_id: str) -> dict[str, Any]:
    try:
        from src.otem_execution_substrate import get_otem_execution_substrate

        return get_otem_execution_substrate().apply(
            workflow_id,
            runtime_context=os.getenv("AAIS_RUNTIME_CONTEXT", "operator_runtime"),
        )
    except ImportError:
        step_ctx.logger.warning("substrate not in Lambda package; returning stub apply")
        return {"workflow_id": workflow_id, "status": "applied_stub"}


@durable_execution
def handler(event: dict[str, Any], context: DurableContext) -> dict[str, Any]:
    """
    Durable entrypoint. Expects:
      { "workflow_id": "...", "proposal": { ... } }
    """
    workflow_id = str(event.get("workflow_id") or "").strip()
    if not workflow_id:
        raise ValueError("workflow_id is required")

    proposal = event.get("proposal") or {}
    timeout_hours = int(os.getenv("OTEM_CALLBACK_TIMEOUT_HOURS", "72"))

    def submit_operator_wait(callback_id: str, ctx: Any) -> None:
        ctx.logger.info(
            "operator approval required",
            extra={
                "workflow_id": workflow_id,
                "callback_id": callback_id,
                "proposal_keys": list(proposal.keys()) if isinstance(proposal, dict) else [],
            },
        )

    decision_payload = context.wait_for_callback(
        submitter=submit_operator_wait,
        name="wait-for-operator-decision",
        config=WaitForCallbackConfig(
            timeout=Duration.from_hours(timeout_hours),
            heartbeat_timeout=Duration.from_minutes(5),
        ),
    )

    if isinstance(decision_payload, (bytes, bytearray)):
        decision_payload = json.loads(decision_payload.decode())
    elif isinstance(decision_payload, str):
        decision_payload = json.loads(decision_payload)

    action = str(decision_payload.get("action") or "").strip().lower()
    if action == "reject":
        return {"status": "rejected", "workflow_id": workflow_id, "substrate": None}
    if action != "approve":
        raise ValueError(f"Unsupported operator decision: {action!r}")

    approved = context.step(otem_substrate_approve(workflow_id), config=_ACTIVITY_RETRY)
    applied = context.step(otem_substrate_apply(workflow_id), config=_ACTIVITY_RETRY)
    return {
        "status": "approved",
        "workflow_id": workflow_id,
        "substrate_approved": approved,
        "substrate": applied,
    }
