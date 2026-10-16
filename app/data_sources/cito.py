"""Cito CS2 REST adapter; all external field names are normalized here."""
from collections.abc import AsyncIterator
from typing import Any
import httpx
from .base import DataSource


class CitoSource(DataSource):
    name = "cito"

    def __init__(self, api_key: str, base_url: str) -> None:
        if not api_key:
            raise ValueError("CITO_API_KEY is required when DATA_SOURCE=cito")
        self.client = httpx.AsyncClient(base_url=base_url, headers={"x-api-key": api_key, "Accept": "application/json"}, timeout=30)

    async def _get_data(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = await self.client.get(path, params=params)
        response.raise_for_status()
        body = response.json()
        if not body.get("success", False):
            raise RuntimeError(f"Cito returned unsuccessful response for {path}")
        return body.get("data", [])

    async def past_matches(self, after: str | None = None) -> AsyncIterator[dict[str, Any]]:
        params: dict[str, Any] = {"limit": 100}
        if after: params["from"] = after
        rows = await self._get_data("/cs2/matches/past", params)
        for raw in rows:
            yield self._canonical_match(raw)

    async def match_games(self, source_match_id: str) -> list[dict[str, Any]]:
        rows = await self._get_data(f"/cs2/matches/{source_match_id}/maps")
        return [self._canonical_map(row) for row in rows]

    async def match_player_stats(self, source_match_id: str) -> list[dict[str, Any]]:
        rows = await self._get_data(f"/cs2/matches/{source_match_id}/player-stats")
        return [self._canonical_player_stat(row) for row in rows]

    @staticmethod
    def _canonical_match(raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": raw["id"], "status": "finished" if raw.get("status") == "completed" else raw.get("status", "unknown"),
            "begin_at": raw.get("startsAt"), "number_of_games": raw.get("bestOf"),
            "opponents": [
                {"opponent": {"id": raw.get("team1Id"), "name": raw.get("team1Name"), "slug": raw.get("team1Slug")}},
                {"opponent": {"id": raw.get("team2Id"), "name": raw.get("team2Name"), "slug": raw.get("team2Slug")}},
            ],
            "winner": {"id": raw.get("winnerTeamId")},
            "tournament": {"id": raw.get("eventId"), "name": raw.get("eventName"), "tier": raw.get("eventTier"), "begin_at": raw.get("eventStartsAt"), "end_at": raw.get("eventEndsAt")},
        }

    @staticmethod
    def _canonical_map(raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": raw["id"], "map": raw.get("mapName") or raw.get("name") or raw.get("map"),
            "position": raw.get("mapNumber") or raw.get("position"),
            "winner": {"id": raw.get("winnerTeamId")},
            "results": [
                {"team_id": raw.get("team1Id"), "score": raw.get("team1Score")},
                {"team_id": raw.get("team2Id"), "score": raw.get("team2Score")},
            ],
        }

    @staticmethod
    def _canonical_player_stat(raw: dict[str, Any]) -> dict[str, Any]:
        player = raw.get("player") or {"id": raw.get("playerId"), "name": raw.get("playerName"), "slug": raw.get("playerSlug")}
        return {
            "player": player,
            "team": raw.get("team") or {"id": raw.get("teamId")},
            "game_id": raw.get("gameId") or raw.get("mapId"),
            "stats": {"counts": {"kills": raw.get("kills"), "deaths": raw.get("deaths"),
                                 "assists": raw.get("assists"), "damage": raw.get("damage"),
                                 "rounds_played": raw.get("roundsPlayed"), "first_kills": raw.get("firstKills"),
                                 "first_deaths": raw.get("firstDeaths"), "clutch_rounds_won": raw.get("clutchesWon"),
                                 "clutch_rounds_played": raw.get("clutchAttempts")},
                      "per_game_averages": {"rating": raw.get("rating"), "kast": raw.get("kast"), "impact": raw.get("impact")}},
        }

    async def close(self) -> None:
        await self.client.aclose()
