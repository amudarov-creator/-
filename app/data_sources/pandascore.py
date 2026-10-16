from collections.abc import AsyncIterator
from typing import Any
import httpx
from .base import DataSource


class PandaScoreSource(DataSource):
    name = "pandascore"
    def __init__(self, token: str, base_url: str) -> None:
        if not token: raise ValueError("PANDASCORE_TOKEN is required for authorised ingestion")
        self.client = httpx.AsyncClient(base_url=base_url, headers={"Authorization": f"Bearer {token}"}, timeout=30)

    async def past_matches(self, after: str | None = None) -> AsyncIterator[dict[str, Any]]:
        params: dict[str, Any] = {"sort": "-begin_at", "per_page": 100}
        if after: params["filter[begin_at]"] = after
        response = await self.client.get("/csgo/matches/past", params=params)
        response.raise_for_status()
        for match in response.json(): yield match

    async def match_player_stats(self, source_match_id: str) -> list[dict[str, Any]]:
        response = await self.client.get(f"/csgo/matches/{source_match_id}/players/stats")
        response.raise_for_status()
        return response.json()

    async def close(self) -> None: await self.client.aclose()
