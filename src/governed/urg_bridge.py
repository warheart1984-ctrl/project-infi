"""Step 2 — Convert LAW_EVAL into a URG mission and run it."""

from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from nova.bridges.nova_to_urg_bridge import NovaToURGBridge

from src.governed.config import GovernedRuntimeConfig, get_governed_config
from src.governed.darz_bridge import build_darz_metadata
from src.governed.t5_bridge import attach_t5_references
from src.ugr.mission.mission_runtime import build_mission_runtime


def build_mission_from_law_eval(
    *,
    law_eval: dict[str, Any],
    steward_identity: dict[str, Any],
    user_text: str,
    config: GovernedRuntimeConfig,
) -> dict[str, Any]:
    """Build the URG mission payload from a LAW_EVAL artifact."""
    bridge = NovaToURGBridge()
    evaluation = dict(law_eval.get("evaluation") or law_eval)
    operator_id = str(
        steward_identity.get("operator_id")
        or steward_identity.get("steward_id")
        or "operator"
    )
    mission = bridge.mission_from_law_eval(
        evaluation=evaluation,
        operator_id=operator_id,
        aais_instance_id=config.aais_instance_id,
        prompt=user_text,
        tenant_id=config.mission_tenant_id,
        law_context=dict(law_eval.get("law_context") or {}),
    )
    context = dict(mission.get("context") or {})
    context["t5_refs"] = attach_t5_references(law_eval)
    context["darz_metadata"] = build_darz_metadata(law_eval)
    context["identity"] = dict(steward_identity)
    context["law_eval_id"] = str(law_eval.get("id") or "")
    mission["context"] = context
    return mission


def _post_urg_mission(mission: dict[str, Any], config: GovernedRuntimeConfig) -> dict[str, Any]:
    body = json.dumps({"mission": mission}).encode("utf-8")
    req = request.Request(
        config.urg_url(),
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_and_send_urg_mission(
    *,
    law_eval: dict[str, Any],
    steward_identity: dict[str, Any],
    user_text: str = "",
    config: GovernedRuntimeConfig | None = None,
) -> dict[str, Any]:
    """Convert LAW_EVAL → URG mission receipt."""
    cfg = config or get_governed_config()
    mission = build_mission_from_law_eval(
        law_eval=law_eval,
        steward_identity=steward_identity,
        user_text=user_text,
        config=cfg,
    )

    if cfg.use_http_urg:
        try:
            receipt = _post_urg_mission(mission, cfg)
        except error.URLError as exc:
            raise RuntimeError(f"URG mission HTTP failed: {exc}") from exc
    else:
        runtime = cfg.mission_runtime or build_mission_runtime()
        receipt = runtime.run_mission(mission)

    receipt["law_eval_id"] = str(law_eval.get("id") or mission.get("context", {}).get("law_eval_id") or "")
    receipt["mission_id"] = str(receipt.get("mission_id") or "")
    return receipt
