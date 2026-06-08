"""Twilio SMS pager for governance escalations that require human authority."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from requests.auth import HTTPBasicAuth


def _pager_config() -> dict[str, str]:
    return {
        "account_sid": os.getenv("TWILIO_ACCOUNT_SID", "").strip(),
        "auth_token": os.getenv("TWILIO_AUTH_TOKEN", "").strip(),
        "from_number": os.getenv("TWILIO_FROM_NUMBER", "").strip(),
        "messaging_service_sid": os.getenv("TWILIO_MESSAGING_SERVICE_SID", "").strip(),
        "operator_to": os.getenv("OPERATOR_PAGER_TO", "").strip(),
    }


def pager_config_from_env() -> dict[str, str]:
    return _pager_config()


def pager_is_configured(config: dict[str, str] | None = None) -> bool:
    cfg = config or _pager_config()
    has_sender = bool(cfg.get("from_number") or cfg.get("messaging_service_sid"))
    return bool(cfg.get("account_sid") and cfg.get("auth_token") and cfg.get("operator_to") and has_sender)


def should_page_for_escalation(escalation: dict[str, Any]) -> bool:
    """Page when the runtime clamps, reroutes, or blocks a dangerous escalation."""
    response = str(escalation.get("response") or "").upper()
    return response in {"CLAMP", "REROUTE", "REJECT"}


def format_immune_escalation_page(session_id: str, escalation: dict[str, Any]) -> str:
    response = str(escalation.get("response") or "UNKNOWN").upper()
    allowed = bool(escalation.get("allowed"))
    reason = str(escalation.get("reason") or "").strip()
    status = "allowed" if allowed else "blocked"
    parts = [
        "[project-infi] Immune escalation",
        f"{response} ({status}).",
        f"session={session_id}.",
    ]
    if reason:
        parts.append(f"reason={reason}.")
    parts.append("Human operator review required per co-collaboration charter.")
    return " ".join(parts)[:320]


def send_operator_page(body: str, *, config: dict[str, str] | None = None) -> dict[str, Any]:
    """Send one SMS via Twilio Programmable Messaging REST API."""
    cfg = config or _pager_config()
    if not pager_is_configured(cfg):
        return {"ok": False, "skipped": True, "reason": "pager_not_configured"}

    payload: dict[str, str] = {"To": cfg["operator_to"], "Body": body}
    if cfg.get("messaging_service_sid"):
        payload["MessagingServiceSid"] = cfg["messaging_service_sid"]
    else:
        payload["From"] = cfg["from_number"]

    url = f"https://api.twilio.com/2010-04-01/Accounts/{cfg['account_sid']}/Messages.json"
    try:
        response = requests.post(
            url,
            data=payload,
            auth=HTTPBasicAuth(cfg["account_sid"], cfg["auth_token"]),
            timeout=15,
        )
    except requests.RequestException as exc:
        return {"ok": False, "skipped": False, "error": str(exc)}

    if response.status_code >= 400:
        return {
            "ok": False,
            "skipped": False,
            "status": response.status_code,
            "error": response.text[:500],
        }

    data = response.json()
    return {
        "ok": True,
        "skipped": False,
        "sid": data.get("sid"),
        "status": data.get("status"),
    }


def maybe_page_immune_escalation(session_id: str, escalation: dict[str, Any]) -> dict[str, Any] | None:
    """Notify the human operator when an immune escalation needs attention."""
    if not should_page_for_escalation(escalation):
        return None
    body = format_immune_escalation_page(session_id, escalation)
    return send_operator_page(body)


DASHBOARD_PAGE_SEVERITIES = frozenset({"high", "critical"})
_DEFAULT_PAGER_STATE_PATH = Path(__file__).resolve().parents[1] / "ci-artifacts" / "operator_pager_state.json"


def _pager_state_path() -> Path:
    raw = str(os.environ.get("OPERATOR_PAGER_STATE_PATH") or "").strip()
    return Path(raw) if raw else _DEFAULT_PAGER_STATE_PATH


def _load_pager_state() -> dict[str, Any]:
    path = _pager_state_path()
    if not path.is_file():
        return {"dashboard_fingerprints": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"dashboard_fingerprints": {}}
    if not isinstance(data, dict):
        return {"dashboard_fingerprints": {}}
    fingerprints = data.get("dashboard_fingerprints")
    if not isinstance(fingerprints, dict):
        data["dashboard_fingerprints"] = {}
    return data


def _save_pager_state(state: dict[str, Any]) -> None:
    path = _pager_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dashboard_alert_fingerprint(alert: dict[str, Any]) -> str:
    alert_id = str(alert.get("id") or "unknown").strip() or "unknown"
    summary = str(alert.get("summary") or "").strip()
    severity = str(alert.get("severity") or "").strip().lower()
    return f"{alert_id}|{severity}|{summary}"


def should_page_for_dashboard_alert(alert: dict[str, Any]) -> bool:
    severity = str(alert.get("severity") or "").strip().lower()
    return severity in DASHBOARD_PAGE_SEVERITIES


def format_dashboard_alert_page(alert: dict[str, Any]) -> str:
    alert_id = str(alert.get("id") or "unknown")
    severity = str(alert.get("severity") or "unknown").upper()
    summary = str(alert.get("summary") or "Operator dashboard alert")
    body = (
        f"[project-infi] Dashboard {severity}: {summary} "
        f"(id={alert_id}). Human review required per co-collaboration charter."
    )
    return body[:320]


def maybe_page_dashboard_alerts(
    alerts: list[dict[str, Any]],
    *,
    config: dict[str, str] | None = None,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Page once per distinct high/critical dashboard alert (deduped by fingerprint)."""
    results: list[dict[str, Any]] = []
    state = _load_pager_state()
    fingerprints: dict[str, str] = dict(state.get("dashboard_fingerprints") or {})
    now = datetime.now(timezone.utc).isoformat()
    changed = False

    for alert in alerts:
        if not should_page_for_dashboard_alert(alert):
            continue
        fingerprint = dashboard_alert_fingerprint(alert)
        if not force and fingerprint in fingerprints:
            continue
        body = format_dashboard_alert_page(alert)
        result = send_operator_page(body, config=config)
        result["alert_id"] = alert.get("id")
        result["fingerprint"] = fingerprint
        results.append(result)
        if result.get("ok") and not result.get("skipped"):
            fingerprints[fingerprint] = now
            changed = True

    if changed:
        state["dashboard_fingerprints"] = fingerprints
        _save_pager_state(state)
    return results
