"""Conservative PandaScore normalizer.

Fields are emitted only when the provider identifies them.  A player aggregate
without a game id is never passed off as map-level statistics.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def value_at(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


@dataclass(frozen=True)
class NormalizedTeam:
    source_id: str
    name: str
    slug: str | None
    country: str | None


def teams_from_match(match: dict[str, Any]) -> list[NormalizedTeam]:
    teams: list[NormalizedTeam] = []
    for item in match.get("opponents") or []:
        raw = item.get("opponent", item)
        if raw.get("id") is not None and raw.get("name"):
            teams.append(NormalizedTeam(str(raw["id"]), raw["name"], raw.get("slug"), raw.get("location") or raw.get("country")))
    return teams


def map_name(game: dict[str, Any]) -> str | None:
    raw = game.get("map") or game.get("map_name")
    return raw.get("name") if isinstance(raw, dict) else raw


def game_scores(game: dict[str, Any], source_team_ids: set[str]) -> dict[str, int]:
    scores: dict[str, int] = {}
    for item in game.get("opponents") or game.get("results") or []:
        team = item.get("team") or item.get("opponent") or {}
        team_id = team.get("id") or item.get("team_id")
        score = item.get("score")
        if team_id is not None and score is not None:
            scores[str(team_id)] = int(score)
    # Some PandaScore payload variants have `results: [{team_id, score}]`.
    return {key: val for key, val in scores.items() if key in source_team_ids}


def stat_game_id(stat: dict[str, Any]) -> str | None:
    game = stat.get("game") or {}
    raw = game.get("id") or stat.get("game_id")
    return str(raw) if raw is not None else None


def stat_player(stat: dict[str, Any]) -> dict[str, Any] | None:
    player = stat.get("player") or {}
    return player if player.get("id") is not None and (player.get("name") or player.get("slug")) else None


def stat_count(stat: dict[str, Any], field: str) -> int | None:
    raw = value_at(stat, "stats", "counts", field)
    if raw is None: raw = value_at(stat, "stats", field)
    return int(raw) if raw is not None else None


def stat_rate(stat: dict[str, Any], field: str) -> float | None:
    raw = value_at(stat, "stats", "per_game_averages", field)
    if raw is None: raw = value_at(stat, "stats", field)
    return float(raw) if raw is not None else None
