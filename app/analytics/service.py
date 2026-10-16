from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import MapResult, Match, Player, PlayerMapStat
from .contracts import MapStat, StatFilter
from .metrics import adr, average, form_change, kd, stability_index


async def find_players(session: AsyncSession, query: str, limit: int = 10) -> list[Player]:
    return list((await session.scalars(select(Player).where(Player.nickname.ilike(f"%{query}%")).limit(limit))).all())


async def player_stats(session: AsyncSession, player_id: int, filters: StatFilter) -> list[MapStat]:
    stmt = (select(PlayerMapStat, MapResult, Match)
            .join(MapResult, MapResult.id == PlayerMapStat.map_result_id)
            .join(Match, Match.id == MapResult.match_id)
            .where(PlayerMapStat.player_id == player_id))
    if filters.start: stmt = stmt.where(Match.begin_at >= filters.start)
    if filters.end: stmt = stmt.where(Match.begin_at <= filters.end)
    if filters.map_name: stmt = stmt.where(MapResult.map_name.ilike(filters.map_name))
    if filters.opponent_team_id: stmt = stmt.where(PlayerMapStat.opponent_team_id == filters.opponent_team_id)
    if filters.team_id: stmt = stmt.where(PlayerMapStat.team_id == filters.team_id)
    stmt = stmt.order_by(Match.begin_at.desc())
    if filters.limit: stmt = stmt.limit(filters.limit)
    rows = (await session.execute(stmt)).all()
    return [MapStat(player_id=player_id, map_name=m.map_name, played_at=match.begin_at or datetime.min,
                    kills=s.kills, deaths=s.deaths, damage=s.damage, rounds_played=s.rounds_played,
                    rating=s.rating, kast=s.kast, impact=s.impact, opponent_team_id=s.opponent_team_id,
                    team_id=s.team_id) for s, m, match in rows]


def report(stats: list[MapStat]) -> list:
    return [kd(stats), adr(stats), average(stats, "rating", "Средний рейтинг источника"), average(stats, "kast", "KAST"), average(stats, "impact", "Impact"), stability_index(stats), form_change(list(reversed(stats)))]
