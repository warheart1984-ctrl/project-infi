"""
HTTP API handler: operator posts approve/reject → durable callback completion.

Pairs with OtemWorkflowHttpApi POST /workflows/{workflowId}/decision in template.yaml.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

_lambda = boto3.client("lambda")


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    path_params = event.get("pathParameters") or {}
    workflow_id = str(path_params.get("workflowId") or "").strip()
    body_raw = event.get("body") or "{}"
    body = json.loads(body_raw) if isinstance(body_raw, str) else body_raw

    callback_id = str(body.get("callback_id") or "").strip()
    action = str(body.get("action") or "").strip().lower()

    if not workflow_id:
        return _response(400, {"error": "workflowId path parameter required"})
    if not callback_id:
        return _response(400, {"error": "callback_id required"})
    if action not in {"approve", "reject"}:
        return _response(400, {"error": "action must be approve or reject"})

    payload = json.dumps({"action": action, "workflow_id": workflow_id})
    durable_target = os.environ["OTEM_DURABLE_FUNCTION_NAME"]

    _lambda.send_durable_execution_callback_success(
        CallbackId=callback_id,
        Result=payload,
    )
    logger.info(
        "operator decision recorded",
        extra={"workflow_id": workflow_id, "action": action, "callback_id": callback_id},
    )
    return _response(200, {"accepted": True, "workflow_id": workflow_id, "action": action})


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
