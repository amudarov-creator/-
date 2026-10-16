"""Explicit, idempotent import entrypoint. It never scrapes HLTV."""
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.data_sources.normalizer import (game_scores, map_name, parse_datetime, stat_count,
                                         stat_game_id, stat_player, stat_rate, teams_from_match)
from app.data_sources.pandascore import PandaScoreSource
from app.data_sources.bo3 import Bo3Source
from app.data_sources.cito import CitoSource
from app.database.models import IngestionRun, PlayerMapStat
from app.database.repositories import (upsert_map_result, upsert_match, upsert_player,
                                       upsert_team, upsert_tournament)
from app.database.session import SessionLocal

log = logging.getLogger(__name__)


async def import_match(session, source, payload: dict) -> None:
    """Import one completed match and stats where PandaScore gives a game id.

    The endpoint may return match aggregates only. Such records create players,
    but are deliberately not written into `player_map_stats`.
    """
    source_name, source_match_id = source.name, str(payload["id"])
    teams = teams_from_match(payload)
    team_ids: dict[str, int] = {}
    for team in teams:
        row = await upsert_team(session, source=source_name, source_id=team.source_id,
                                name=team.name, slug=team.slug, country=team.country)
        team_ids[team.source_id] = row.id

    tournament_id = None
    tournament = payload.get("tournament") or payload.get("serie") or payload.get("league")
    if isinstance(tournament, dict) and tournament.get("id") is not None and tournament.get("name"):
        row = await upsert_tournament(session, source=source_name, source_id=str(tournament["id"]),
                                      name=tournament["name"], tier=tournament.get("tier"),
                                      starts_at=parse_datetime(tournament.get("begin_at")), ends_at=parse_datetime(tournament.get("end_at")))
        tournament_id = row.id

    winner = payload.get("winner") or {}
    ordered_source_team_ids = list(team_ids)
    team_a = team_ids.get(ordered_source_team_ids[0]) if len(ordered_source_team_ids) > 0 else None
    team_b = team_ids.get(ordered_source_team_ids[1]) if len(ordered_source_team_ids) > 1 else None
    match = await upsert_match(session, source=source_name, source_id=source_match_id,
                               tournament_id=tournament_id, begin_at=parse_datetime(payload.get("begin_at")),
                               best_of=payload.get("number_of_games") or payload.get("best_of"),
                               team_a_id=team_a, team_b_id=team_b,
                               winner_team_id=team_ids.get(str(winner.get("id"))),
                               status=payload.get("status") or "unknown")

    games = await source.match_games(source_match_id)
    map_ids: dict[str, int] = {}
    source_team_ids = set(team_ids)
    for position, game in enumerate(games, start=1):
        if game.get("id") is None or not map_name(game):
            continue
        scores = game_scores(game, source_team_ids)
        winner = game.get("winner") or {}
        map_row = await upsert_map_result(
            session, source=source_name, source_id=str(game["id"]), match_id=match.id,
            map_name=map_name(game), sequence=game.get("position") or position,
            team_a_score=scores.get(ordered_source_team_ids[0]) if len(ordered_source_team_ids) > 0 else None,
            team_b_score=scores.get(ordered_source_team_ids[1]) if len(ordered_source_team_ids) > 1 else None,
            winner_team_id=team_ids.get(str(winner.get("id"))),
        )
        map_ids[str(game["id"])] = map_row.id

    for raw_stat in await source.match_player_stats(source_match_id):
        player = stat_player(raw_stat)
        if not player:
            continue
        player_row = await upsert_player(session, source=source_name, source_id=str(player["id"]),
                                         nickname=player.get("slug") or player["name"], full_name=player.get("name"),
                                         country=player.get("nationality") or player.get("country"))
        game_id = stat_game_id(raw_stat)
        if game_id not in map_ids:
            continue
        raw_team = raw_stat.get("team") or {}
        source_team = str(raw_team.get("id"))
        team_id = team_ids.get(source_team)
        opponents = [team_id for key, team_id in team_ids.items() if key != source_team]
        values = {
            "player_id": player_row.id, "map_result_id": map_ids[game_id], "team_id": team_id,
            "opponent_team_id": opponents[0] if len(opponents) == 1 else None,
            "kills": stat_count(raw_stat, "kills"), "deaths": stat_count(raw_stat, "deaths"),
            "assists": stat_count(raw_stat, "assists"), "damage": stat_count(raw_stat, "damage"),
            "rounds_played": stat_count(raw_stat, "rounds_played"),
            "rating": stat_rate(raw_stat, "rating"), "kast": stat_rate(raw_stat, "kast"),
            "impact": stat_rate(raw_stat, "impact"), "first_kills": stat_count(raw_stat, "first_kills"),
            "first_deaths": stat_count(raw_stat, "first_deaths"),
            "clutches_won": stat_count(raw_stat, "clutch_rounds_won"),
            "clutch_attempts": stat_count(raw_stat, "clutch_rounds_played"),
            "rating_version": "provider_unspecified",
        }
        stmt = insert(PlayerMapStat).values(**values).on_conflict_do_update(
            index_elements=["player_id", "map_result_id"],
            set_={key: value for key, value in values.items() if key not in {"player_id", "map_result_id"}},
        )
        await session.execute(stmt)


async def run() -> int:
    settings = get_settings()
    if settings.data_source == "cito":
        source = CitoSource(settings.cito_api_key, settings.cito_base_url)
    elif settings.data_source == "bo3":
        source = Bo3Source(settings.bo3_base_url)
    elif settings.data_source == "pandascore":
        if not settings.pandascore_token:
            log.warning("No PANDASCORE_TOKEN: ingestion skipped; bot remains usable with imported data.")
            return 0
        source = PandaScoreSource(settings.pandascore_token, settings.pandascore_base_url)
    else:
        raise ValueError("DATA_SOURCE must be 'cito', 'bo3' or 'pandascore'")
    async with SessionLocal() as session:
        record = IngestionRun(source=source.name, status="running")
        session.add(record); await session.commit()
        try:
            async for match in source.past_matches():
                if record.records_seen >= settings.sync_max_matches:
                    break
                record.records_seen += 1
                if match.get("status") != "finished" or not match.get("id"):
                    continue
                await import_match(session, source, match)
            record.status = "succeeded"; record.finished_at = datetime.now(timezone.utc)
            await session.commit()
            return record.records_seen
        except Exception as exc:
            record.status = "failed"; record.error = str(exc); record.finished_at = datetime.now(timezone.utc)
            await session.commit(); raise
        finally:
            await source.close()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(run())
