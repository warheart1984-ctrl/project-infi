from __future__ import annotations

from collections.abc import Callable
from typing import Any


class SliceRunner:
    def run(self, slice_callable: Callable[[Any], Any], payload: Any) -> Any:
        return slice_callable(payload)
