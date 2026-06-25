"""Asset service — create governed assets linked to subjects."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from src.runtime.models import Asset
from src.runtime.schemas import AssetInput


def create_asset(db: Session, *, subject_id: uuid.UUID, asset: AssetInput) -> uuid.UUID:
    """POST asset/v1/assets equivalent."""
    row = Asset(
        subject_id=subject_id,
        type=asset.type,
        name=asset.name,
        asset_metadata=asset.metadata,
    )
    db.add(row)
    db.flush()
    return row.id
