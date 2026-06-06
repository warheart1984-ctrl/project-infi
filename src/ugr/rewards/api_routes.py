"""UGR rewards and discovery API route handlers."""

# Mythic: Rewards API Routes
# Engineering: RewardsApiRoutesEngine
from __future__ import annotations

import os
from typing import Any

from flask import jsonify, request


def _runtime_dir() -> str | None:
    return os.getenv("AAIS_RUNTIME_DIR") or None


def ugr_discover_contribution():
    from src.ugr.discovery.contribution_discovery import build_contribution_discovery_service

    data = request.get_json(silent=True) or {}
    service = build_contribution_discovery_service(_runtime_dir())
    result = service.discover(data)
    status = 200 if result.get("status") in {"discovered", "invalid", "not_found", "rejected"} else 500
    return jsonify(result), status


def ugr_discover_subsystem():
    data = request.get_json(silent=True) or {}
    if not data.get("contribution_type"):
        data = {**data, "contribution_type": "subsystem"}
    return ugr_discover_contribution()


def ugr_discover_contribution_get(contribution_id: str):
    from src.ugr.discovery.contribution_discovery import build_contribution_discovery_service

    tenant_id = str(request.args.get("tenant_id") or "global")
    service = build_contribution_discovery_service(_runtime_dir())
    receipt = service.get_receipt(contribution_id, tenant_id=tenant_id)
    if receipt is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"contribution_id": contribution_id, "receipt": receipt})


def ugr_reward_issue():
    from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine

    data = request.get_json(silent=True) or {}
    engine = build_operator_reward_engine(_runtime_dir())
    result = engine.issue(
        tenant_id=str(data.get("tenant_id") or ""),
        operator_id=str(data.get("operator_id") or ""),
        contribution_id=str(data.get("contribution_id") or data.get("subsystem_id") or ""),
        event_type=str(data.get("event_type") or ""),
        discovery_receipt_id=data.get("discovery_receipt_id"),
        governance_mission_id=data.get("governance_mission_id"),
        promotion_organ_id=data.get("promotion_organ_id"),
        governance_status=data.get("governance_status"),
    )
    return jsonify(result), 200


def ugr_rewards_spend():
    from src.ugr.rewards.rail_credit_spend import spend_rail_credits

    data = request.get_json(silent=True) or {}
    result = spend_rail_credits(
        tenant_id=str(data.get("tenant_id") or ""),
        operator_id=str(data.get("operator_id") or ""),
        amount=float(data.get("amount") or 0),
        trace_id=str(data.get("trace_id") or ""),
        purpose=str(data.get("purpose") or "express_boost"),
        runtime_dir=_runtime_dir(),
    )
    return jsonify(result), 200


def ugr_credits_purchase():
    from src.ugr.rewards.rail_credit_purchase import purchase_rail_credits

    data = request.get_json(silent=True) or {}
    result = purchase_rail_credits(
        tenant_id=str(data.get("tenant_id") or ""),
        operator_id=str(data.get("operator_id") or ""),
        amount=float(data.get("amount") or 0),
        payment_reference=str(data.get("payment_reference") or ""),
        trace_id=str(data.get("trace_id") or ""),
        purchase_receipt=dict(data.get("purchase_receipt") or {}),
        runtime_dir=_runtime_dir(),
    )
    return jsonify(result), 200


def ugr_reward_operator(operator_id: str):
    from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine

    tenant_id = str(request.args.get("tenant_id") or "global")
    engine = build_operator_reward_engine(_runtime_dir())
    profile = engine.get_profile(operator_id, tenant_id=tenant_id)
    events = engine.list_ledger(tenant_id=tenant_id, operator_id=operator_id, limit=20)
    return jsonify({"operator_id": operator_id, "profile": profile, "recent_events": events})


def ugr_reward_contribution(contribution_id: str):
    from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine

    tenant_id = str(request.args.get("tenant_id") or "global")
    engine = build_operator_reward_engine(_runtime_dir())
    events = engine.list_ledger(
        tenant_id=tenant_id,
        contribution_id=contribution_id,
        limit=50,
    )
    return jsonify({"contribution_id": contribution_id, "count": len(events), "events": events})


def ugr_reward_transfer():
    from src.ugr.rewards.rail_credit_transfer import transfer_rail_credits

    data = request.get_json(silent=True) or {}
    result = transfer_rail_credits(
        tenant_id=str(data.get("tenant_id") or ""),
        from_operator_id=str(data.get("from_operator_id") or ""),
        to_operator_id=str(data.get("to_operator_id") or ""),
        amount=float(data.get("amount") or 0),
        trace_id=str(data.get("trace_id") or ""),
        transfer_id=data.get("transfer_id"),
        runtime_dir=_runtime_dir(),
    )
    return jsonify(result), 200


def register_ugr_rewards_routes(app: Any) -> None:
    app.add_url_rule(
        "/api/ugr/discover/contribution",
        endpoint="ugr_discover_contribution",
        view_func=ugr_discover_contribution,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/ugr/discover/subsystem",
        endpoint="ugr_discover_subsystem",
        view_func=ugr_discover_subsystem,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/ugr/discover/contribution/<contribution_id>",
        endpoint="ugr_discover_contribution_get",
        view_func=ugr_discover_contribution_get,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/ugr/reward/issue",
        endpoint="ugr_reward_issue",
        view_func=ugr_reward_issue,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/ugr/rewards/spend",
        endpoint="ugr_rewards_spend",
        view_func=ugr_rewards_spend,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/ugr/credits/purchase",
        endpoint="ugr_credits_purchase",
        view_func=ugr_credits_purchase,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/ugr/reward/operator/<operator_id>",
        endpoint="ugr_reward_operator",
        view_func=ugr_reward_operator,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/ugr/reward/subsystem/<contribution_id>",
        endpoint="ugr_reward_subsystem",
        view_func=ugr_reward_contribution,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/ugr/reward/contribution/<contribution_id>",
        endpoint="ugr_reward_contribution",
        view_func=ugr_reward_contribution,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/ugr/reward/transfer",
        endpoint="ugr_reward_transfer",
        view_func=ugr_reward_transfer,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/ugr/rewards/transfer",
        endpoint="ugr_rewards_transfer",
        view_func=ugr_reward_transfer,
        methods=["POST"],
    )
