"""Single watchdog boundary for dormant Super Nova calls."""

from __future__ import annotations

from typing import Callable, TypeVar

from src.super_nova_activation import (
    ActivationToken,
    SuperNovaActivationContextCheck,
    SuperNovaContinuityStatus,
)
from src.super_nova_runtime import SuperNovaScaffold


_T = TypeVar("_T")


def watchdog_validate(
    scaffold: SuperNovaScaffold,
    session_id: str,
    token: ActivationToken | None,
    *,
    continuity: SuperNovaContinuityStatus,
) -> SuperNovaActivationContextCheck:
    """Validate a Super Nova token against the watchdog boundary."""

    token_id = token.token_id if token is not None else ""
    return scaffold.validate_activation_context(
        session_id,
        token_id,
        continuity=continuity,
    )


def super_nova_guarded_call(
    scaffold: SuperNovaScaffold,
    session_id: str,
    token: ActivationToken | None,
    *,
    continuity: SuperNovaContinuityStatus,
    fn: Callable[..., _T],
    **kwargs,
) -> _T:
    """Run a callable only if the Super Nova watchdog still validates."""

    token_id = token.token_id if token is not None else ""
    return scaffold.guarded_call(
        session_id,
        token_id,
        fn,
        continuity=continuity,
        **kwargs,
    )
