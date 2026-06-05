from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_optional_principal, is_auth_required, require_token
from app.config import ALLOW_OPERATOR_REGISTRATION
from app.db import (
    count_operator_users,
    create_operator_user,
    get_operator_user_by_id,
    get_operator_user_by_username,
    public_operator_user,
)
from app.schemas import (
    AuthLoginRequest,
    AuthRefreshRequest,
    AuthRegisterRequest,
    AuthStatusResponse,
    AuthTokenResponse,
    AuthUserResponse,
)
from src.auth import ACCESS_TOKEN_EXPIRE_MINUTES, AuthManager

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user: dict) -> AuthTokenResponse:
    token_data = {"sub": user["id"], "username": user["username"], "role": user["role"]}
    access_token = AuthManager.create_access_token(token_data)
    refresh_token = AuthManager.create_refresh_token({"sub": user["id"]})
    public_user = public_operator_user(user)
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=AuthUserResponse(**public_user),
    )


def _registration_allowed() -> bool:
    if count_operator_users() == 0:
        return True
    return ALLOW_OPERATOR_REGISTRATION


@router.get("/status", response_model=AuthStatusResponse)
def auth_status(principal: dict | None = Depends(get_optional_principal)) -> AuthStatusResponse:
    user = None
    authenticated = False
    if principal and principal.get("sub") not in (None, "legacy_bearer"):
        user_record = get_operator_user_by_id(str(principal["sub"]))
        user = public_operator_user(user_record)
        authenticated = user is not None
    elif principal and principal.get("sub") == "legacy_bearer":
        authenticated = True

    return AuthStatusResponse(
        auth_required=is_auth_required(),
        registration_allowed=_registration_allowed(),
        authenticated=authenticated,
        user=AuthUserResponse(**user) if user else None,
    )


@router.post("/register", response_model=AuthTokenResponse)
def auth_register(req: AuthRegisterRequest) -> AuthTokenResponse:
    if not _registration_allowed():
        raise HTTPException(status_code=403, detail="Registration is disabled")

    if get_operator_user_by_username(req.username):
        raise HTTPException(status_code=409, detail="Username already exists")

    role = "admin" if count_operator_users() == 0 else "operator"
    user = create_operator_user(
        username=req.username,
        password_hash=AuthManager.hash_password(req.password),
        role=role,
    )
    if not user:
        raise HTTPException(status_code=500, detail="Could not create user")
    return _issue_tokens(user)


@router.post("/login", response_model=AuthTokenResponse)
def auth_login(req: AuthLoginRequest) -> AuthTokenResponse:
    user = get_operator_user_by_username(req.username)
    if not user or not user.get("active"):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not AuthManager.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return _issue_tokens(user)


@router.post("/refresh", response_model=AuthTokenResponse)
def auth_refresh(req: AuthRefreshRequest) -> AuthTokenResponse:
    payload = AuthManager.verify_token(req.refresh_token, expected_type="refresh")
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = get_operator_user_by_id(str(payload["sub"]))
    if not user or not user.get("active"):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return _issue_tokens(user)


@router.get("/me", response_model=AuthUserResponse)
def auth_me(principal: dict = Depends(require_token)) -> AuthUserResponse:
    if principal.get("sub") == "legacy_bearer":
        raise HTTPException(status_code=400, detail="Legacy bearer token has no user profile")

    user = get_operator_user_by_id(str(principal["sub"]))
    public_user = public_operator_user(user)
    if not public_user:
        raise HTTPException(status_code=404, detail="User not found")
    return AuthUserResponse(**public_user)
