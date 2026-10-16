from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class MapStat:
    player_id: int
    map_name: str
    played_at: datetime
    kills: int | None = None
    deaths: int | None = None
    damage: float | None = None
    rounds_played: int | None = None
    rating: float | None = None
    kast: float | None = None
    impact: float | None = None
    opponent_team_id: int | None = None
    team_id: int | None = None


@dataclass(frozen=True)
class StatFilter:
    start: datetime | None = None
    end: datetime | None = None
    map_name: str | None = None
    opponent_team_id: int | None = None
    team_id: int | None = None
    limit: int | None = None


@dataclass(frozen=True)
class MetricResult:
    name: str
    value: float | None
    maps: int
    warning: str | None = None
    definition: str = ""
    formula_version: str = "1.0"


SampleLevel = Literal["extremely_low", "limited", "preliminary", "informative", "reliable"]
