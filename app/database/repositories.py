from datetime import datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Player, Team


async def upsert_player(session: AsyncSession, *, source: str, source_id: str, nickname: str, **fields: object) -> Player:
    stmt = insert(Player).values(source=source, source_id=source_id, nickname=nickname, updated_at=datetime.utcnow(), **fields)
    stmt = stmt.on_conflict_do_update(index_elements=["source", "source_id"], set_={"nickname": nickname, "updated_at": datetime.utcnow(), **fields}).returning(Player)
    return (await session.scalars(stmt)).one()


async def upsert_team(session: AsyncSession, *, source: str, source_id: str, name: str, **fields: object) -> Team:
    stmt = insert(Team).values(source=source, source_id=source_id, name=name, updated_at=datetime.utcnow(), **fields)
    stmt = stmt.on_conflict_do_update(index_elements=["source", "source_id"], set_={"name": name, "updated_at": datetime.utcnow(), **fields}).returning(Team)
    return (await session.scalars(stmt)).one()
