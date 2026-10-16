from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class DataSource(ABC):
    """Authorised data only. Adapters must preserve source IDs and provenance."""
    name: str

    @abstractmethod
    async def past_matches(self, after: str | None = None) -> AsyncIterator[dict[str, Any]]: ...

    @abstractmethod
    async def match_player_stats(self, source_match_id: str) -> list[dict[str, Any]]: ...
