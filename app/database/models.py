from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class SourceEntityMixin:
    source: Mapped[str] = mapped_column(String(32), default="pandascore")
    source_id: Mapped[str] = mapped_column(String(80))


class Player(SourceEntityMixin, Base):
    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("source", "source_id"), Index("ix_players_nickname", "nickname"))
    id: Mapped[int] = mapped_column(primary_key=True)
    nickname: Mapped[str] = mapped_column(String(80))
    full_name: Mapped[str | None] = mapped_column(String(160))
    country: Mapped[str | None] = mapped_column(String(4))
    profile_url: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Team(SourceEntityMixin, Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("source", "source_id"), Index("ix_teams_name", "name"))
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(4))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Tournament(SourceEntityMixin, Base):
    __tablename__ = "tournaments"
    __table_args__ = (UniqueConstraint("source", "source_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    tier: Mapped[str | None] = mapped_column(String(32))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Match(SourceEntityMixin, Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("source", "source_id"), Index("ix_matches_begin_at", "begin_at"))
    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int | None] = mapped_column(ForeignKey("tournaments.id"))
    begin_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    best_of: Mapped[int | None] = mapped_column(Integer)
    team_a_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    team_b_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    winner_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    status: Mapped[str] = mapped_column(String(32), default="finished")


class MapResult(SourceEntityMixin, Base):
    __tablename__ = "map_results"
    __table_args__ = (UniqueConstraint("source", "source_id"), Index("ix_map_results_match", "match_id"))
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    map_name: Mapped[str] = mapped_column(String(48))
    sequence: Mapped[int] = mapped_column(Integer)
    team_a_score: Mapped[int | None] = mapped_column(Integer)
    team_b_score: Mapped[int | None] = mapped_column(Integer)
    winner_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))


class PlayerMapStat(Base):
    __tablename__ = "player_map_stats"
    __table_args__ = (UniqueConstraint("player_id", "map_result_id"), Index("ix_pms_player_map", "player_id", "map_result_id"))
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    opponent_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    map_result_id: Mapped[int] = mapped_column(ForeignKey("map_results.id"))
    kills: Mapped[int | None] = mapped_column(Integer)
    deaths: Mapped[int | None] = mapped_column(Integer)
    assists: Mapped[int | None] = mapped_column(Integer)
    damage: Mapped[float | None] = mapped_column(Float)
    rounds_played: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[float | None] = mapped_column(Float)
    kast: Mapped[float | None] = mapped_column(Float)
    impact: Mapped[float | None] = mapped_column(Float)
    first_kills: Mapped[int | None] = mapped_column(Integer)
    first_deaths: Mapped[int | None] = mapped_column(Integer)
    clutches_won: Mapped[int | None] = mapped_column(Integer)
    clutch_attempts: Mapped[int | None] = mapped_column(Integer)
    rating_version: Mapped[str | None] = mapped_column(String(32))


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(24))
    records_seen: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
