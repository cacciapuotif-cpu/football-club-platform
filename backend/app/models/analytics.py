"""Analytics models for ML training and predictions (sync SQLAlchemy)."""

from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db_sync import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    organization_id = Column(UUID(as_uuid=True), index=True)
    date = Column(Date, nullable=False)
    opponent = Column(String(100))
    competition = Column(String(100))
    home = Column(Boolean, nullable=False, server_default='true')
    minutes = Column(Integer)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    players_stats = relationship("PlayerMatchStat", back_populates="match", cascade="all, delete-orphan")


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True)
    organization_id = Column(UUID(as_uuid=True), index=True)
    date = Column(Date, nullable=False)
    session_type = Column(String(50))
    duration_min = Column(Integer)
    rpe = Column(Float)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    player_loads = relationship("PlayerTrainingLoad", back_populates="session", cascade="all, delete-orphan")


class PlayerMatchStat(Base):
    __tablename__ = "player_match_stats"
    __table_args__ = (UniqueConstraint('player_id', 'match_id', name='uq_player_match'),)

    id = Column(Integer, primary_key=True)
    organization_id = Column(UUID(as_uuid=True), index=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    minutes = Column(Integer)
    goals = Column(Integer, server_default='0')
    assists = Column(Integer, server_default='0')
    shots = Column(Integer, server_default='0')
    xg = Column(Float, server_default='0')
    key_passes = Column(Integer, server_default='0')
    duels_won = Column(Integer, server_default='0')
    sprints = Column(Integer, server_default='0')
    pressures = Column(Integer, server_default='0')
    def_actions = Column(Integer, server_default='0')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    match = relationship("Match", back_populates="players_stats")
    # Note: player relationship handled separately to avoid circular imports


class PlayerTrainingLoad(Base):
    __tablename__ = "player_training_load"
    __table_args__ = (UniqueConstraint('player_id', 'session_id', name='uq_player_session'),)

    id = Column(Integer, primary_key=True)
    organization_id = Column(UUID(as_uuid=True), index=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(Integer, ForeignKey("training_sessions.id", ondelete="CASCADE"), nullable=False)
    load_acute = Column(Float)
    load_chronic = Column(Float)
    monotony = Column(Float)
    strain = Column(Float)
    injury_history_flag = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    session = relationship("TrainingSession", back_populates="player_loads")


class PlayerFeatureDaily(Base):
    __tablename__ = "player_features_daily"
    __table_args__ = (UniqueConstraint('player_id', 'date', name='uq_player_date'),)

    id = Column(Integer, primary_key=True)
    organization_id = Column(UUID(as_uuid=True), index=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    rolling_7d_load = Column(Float)
    rolling_21d_load = Column(Float)
    form_score = Column(Float)
    injury_flag = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class PlayerPrediction(Base):
    __tablename__ = "player_predictions"
    __table_args__ = (UniqueConstraint('player_id', 'date', 'target', name='uq_player_date_target'),)

    id = Column(Integer, primary_key=True)
    organization_id = Column(UUID(as_uuid=True), index=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    target = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    y_pred = Column(Float)
    y_proba = Column(Float)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
