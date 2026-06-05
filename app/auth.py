from __future__ import annotations

from fastapi import Header, HTTPException, Request, WebSocket

from app import config
from app.db import count_operator_users, get_operator_user_by_id
from src.auth import AuthManager


def is_auth_required() -> bool:
    if config.AUTH_REQUIRED:
        return True
    if config.APP_BEARER_TOKEN:
        return True
    return count_operator_users() > 0


def _extract_bearer_value(authorization: str | None) -> str:
    if not authorization:
        return ""
    if authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ").strip()
    return authorization.strip()


def validate_access_token(token: str) -> dict | None:
    if not token:
        return None

    payload = AuthManager.verify_token(token, expected_type="access")
    if payload:
        user_id = payload.get("sub")
        if not user_id:
            return None
        if user_id == "legacy_bearer":
            return {
                "sub": user_id,
                "username": "legacy_bearer",
                "role": payload.get("role", "operator"),
            }
        user = get_operator_user_by_id(str(user_id))
        if not user or not user.get("active"):
            return None
        return {
            "sub": user["id"],
            "username": user["username"],
            "role": user["role"],
        }

    if config.APP_BEARER_TOKEN and token == config.APP_BEARER_TOKEN:
        return {
            "sub": "legacy_bearer",
            "username": "legacy_bearer",
            "role": "operator",
        }
    return None


def require_token(authorization: str | None = Header(default=None)) -> dict | None:
    if not is_auth_required():
        return None

    principal = validate_access_token(_extract_bearer_value(authorization))
    if principal:
        return principal
    raise HTTPException(status_code=401, detail="Unauthorized")


def get_optional_principal(authorization: str | None = Header(default=None)) -> dict | None:
    return validate_access_token(_extract_bearer_value(authorization))


def check_sse_token(request: Request) -> None:
    if not is_auth_required():
        return
    token = request.query_params.get("token", "").strip()
    if validate_access_token(token):
        return
    raise HTTPException(status_code=401, detail="Unauthorized")


async def check_ws_token(websocket: WebSocket) -> None:
    if not is_auth_required():
        return
    token = websocket.query_params.get("token", "").strip()
    if validate_access_token(token):
        return
    await websocket.close(code=4401)
    raise RuntimeError("Unauthorized websocket")
