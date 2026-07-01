from __future__ import annotations

from typing import Any

from skillzmcgee.governance.invariants import ALLOWED_STATUSES, REQUIRED_RECEIPT_FIELDS


class MinimalValidator:
    def validate_entry(self, entry: dict[str, Any]) -> bool:
        for field in REQUIRED_RECEIPT_FIELDS:
            if field not in entry:
                raise ValueError(f"receipt missing required field: {field}")

        if entry["status"] not in ALLOWED_STATUSES:
            raise ValueError(f"receipt status must be one of {ALLOWED_STATUSES}")

        return True
