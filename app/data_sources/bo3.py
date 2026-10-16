"""Experimental BO3.gg adapter.

The endpoint is not a documented supplier API. It is intentionally isolated so
it can be disabled or replaced without touching storage/analytics code.
"""
from collections.abc import AsyncIterator
from typing import Any
import httpx
from .base import DataSource


class Bo3Source(DataSource):
    name = "bo3"

    def __init__(self, base_url: str) -> None:
        self.client = httpx.AsyncClient(base_url=base_url, headers={"Accept": "application/json"}, timeout=30)
        self._games: dict[str, list[dict[str, Any]]] = {}

    async def past_matches(self, after: str | None = None) -> AsyncIterator[dict[str, Any]]:
        params = {
            "scope": "widget-matches", "page[offset]": 0, "page[limit]": 100,
            "sort": "-start_date", "filter[matches.status][in]": "finished",
            "filter[matches.discipline_id][eq]": 1, "with": "teams,tournament,games",
        }
        response = await self.client.get("/matches", params=params)
        response.raise_for_status()
        body = response.json()
        entries = body.get("data", body) if isinstance(body, dict) else body
        for raw in entries:
            match = self._canonical_match(raw)
            self._games[match["id"]] = match.pop("games", [])
            yield match

    async def match_games(self, source_match_id: str) -> list[dict[str, Any]]:
        return self._games.get(source_match_id, [])

    async def match_player_stats(self, source_match_id: str) -> list[dict[str, Any]]:
        # The wrapper's public match call does not expose per-game player stats.
        return []

    @staticmethod
    def _canonical_match(raw: dict[str, Any]) -> dict[str, Any]:
        teams = raw.get("teams") or raw.get("match_teams") or []
        opponents = [{"opponent": {"id": team.get("id"), "name": team.get("name") or team.get("title"),
                                      "slug": team.get("slug"), "country": team.get("country", {}).get("code") if isinstance(team.get("country"), dict) else None}}
                     for team in teams if team.get("id") is not None]
        winner = raw.get("winner") or raw.get("winner_team") or {}
        return {
            "id": raw["id"], "status": raw.get("status", "finished"),
            "begin_at": raw.get("start_date") or raw.get("begin_at"),
            "number_of_games": raw.get("best_of") or raw.get("number_of_games"),
            "opponents": opponents, "winner": winner,
            "tournament": raw.get("tournament"), "games": raw.get("games") or [],
        }

    async def close(self) -> None:
        await self.client.aclose()
