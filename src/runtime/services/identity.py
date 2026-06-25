"""Identity service — register or resolve subject by email."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.runtime.models import Subject
from src.runtime.schemas import CoreLoopRequest


def register_or_resolve_subject(db: Session, request: CoreLoopRequest) -> uuid.UUID:
    """
    POST identity/v1/register equivalent.
    Returns existing subject_id when email already exists.
    """
    return register_subject(db, email=str(request.email), display_name=request.display_name)


def register_subject(db: Session, *, email: str, display_name: str) -> uuid.UUID:
    """Register or resolve a subject by email (mesh HTTP handler)."""
    normalized = email.strip().lower()
    existing = db.execute(select(Subject).where(Subject.email == normalized)).scalar_one_or_none()
    if existing is not None:
        if display_name and existing.display_name != display_name:
            existing.display_name = display_name
            db.flush()
        return existing.id

    subject = Subject(email=normalized, display_name=display_name)
    db.add(subject)
    db.flush()
    return subject.id
