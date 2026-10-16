from datetime import datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from .models import MapResult, Match, Player, Team, Tournament


async def upsert_player(session: AsyncSession, *, source: str, source_id: str, nickname: str, **fields: object) -> Player:
    stmt = insert(Player).values(source=source, source_id=source_id, nickname=nickname, updated_at=datetime.utcnow(), **fields)
    stmt = stmt.on_conflict_do_update(index_elements=["source", "source_id"], set_={"nickname": nickname, "updated_at": datetime.utcnow(), **fields}).returning(Player)
    return (await session.scalars(stmt)).one()


async def upsert_team(session: AsyncSession, *, source: str, source_id: str, name: str, **fields: object) -> Team:
    stmt = insert(Team).values(source=source, source_id=source_id, name=name, updated_at=datetime.utcnow(), **fields)
    stmt = stmt.on_conflict_do_update(index_elements=["source", "source_id"], set_={"name": name, "updated_at": datetime.utcnow(), **fields}).returning(Team)
    return (await session.scalars(stmt)).one()


async def _upsert(session: AsyncSession, model: object, values: dict[str, object], keys: list[str]):
    stmt = insert(model).values(**values)
    updates = {key: value for key, value in values.items() if key not in keys}
    stmt = stmt.on_conflict_do_update(index_elements=keys, set_=updates).returning(model)
    return (await session.scalars(stmt)).one()


async def upsert_tournament(session: AsyncSession, **values: object) -> Tournament:
    return await _upsert(session, Tournament, values, ["source", "source_id"])


async def upsert_match(session: AsyncSession, **values: object) -> Match:
    return await _upsert(session, Match, values, ["source", "source_id"])


async def upsert_map_result(session: AsyncSession, **values: object) -> MapResult:
    return await _upsert(session, MapResult, values, ["source", "source_id"])
