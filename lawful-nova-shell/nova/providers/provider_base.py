from __future__ import annotations

from typing import Any, Iterator, Protocol


class NovaProvider(Protocol):
    provider_id: str
    model: str

    def chat_completion(self, governed_request: dict[str, Any]) -> dict[str, Any]:
        ...

    def chat_completion_stream(self, governed_request: dict[str, Any]) -> Iterator[dict[str, Any]]:
        ...
