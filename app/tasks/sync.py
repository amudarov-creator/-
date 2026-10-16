"""Explicit, idempotent import entrypoint. It never scrapes HLTV."""
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.data_sources.pandascore import PandaScoreSource
from app.database.models import IngestionRun
from app.database.repositories import upsert_team
from app.database.session import SessionLocal

log = logging.getLogger(__name__)


async def run() -> int:
    settings = get_settings()
    if not settings.pandascore_token:
        log.warning("No PANDASCORE_TOKEN: ingestion skipped; bot remains usable with imported data.")
        return 0
    source = PandaScoreSource(settings.pandascore_token, settings.pandascore_base_url)
    async with SessionLocal() as session:
        record = IngestionRun(source=source.name, status="running")
        session.add(record); await session.commit()
        try:
            async for match in source.past_matches():
                record.records_seen += 1
                for opponent in match.get("opponents", []):
                    team = opponent.get("opponent") or {}
                    if team.get("id"):
                        await upsert_team(session, source=source.name, source_id=str(team["id"]), name=team.get("name", "Unknown"), slug=team.get("slug"))
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
