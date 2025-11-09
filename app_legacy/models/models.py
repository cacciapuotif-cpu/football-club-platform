"""SQLAlchemy database models."""
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime, Text,
    ForeignKey, Enum, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
import uuid

from app.db.database import Base
from app.models.enums import (
    PlayerRole, DominantFoot, SessionType, PitchType,
    TimeOfDay, PlayerStatus
)


class Player(Base):
    """Player model - anagrafica giocatore."""
    __tablename__ = "players"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    category = Column(String(50), nullable=False)  # es. "U17"
    primary_role = Column(Enum(PlayerRole), nullable=False, default=PlayerRole.MF)
    secondary_role = Column(Enum(PlayerRole), nullable=True)
    dominant_foot = Column(Enum(DominantFoot), nullable=False, default=DominantFoot.RIGHT)
    shirt_number = Column(Integer, nullable=True)
    years_active = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions = relationship("Session", back_populates="player", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Player {self.code}: {self.first_name} {self.last_name}>"


class Session(Base):
    """Session model - sessione di allenamento/partita/test."""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    session_date = Column(Date, nullable=False)
    session_type = Column(Enum(SessionType), nullable=False)
    minutes_played = Column(Integer, nullable=False, default=0)
    coach_rating = Column(Numeric(3, 1), nullable=True)
    match_score = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=True)
    pitch_type = Column(Enum(PitchType), nullable=True)
    weather = Column(String(100), nullable=True)
    time_of_day = Column(Enum(TimeOfDay), nullable=True)
    status = Column(Enum(PlayerStatus), nullable=False, default=PlayerStatus.OK)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player = relationship("Player", back_populates="sessions")
    metrics_physical = relationship("MetricsPhysical", back_populates="session", uselist=False, cascade="all, delete-orphan")
    metrics_technical = relationship("MetricsTechnical", back_populates="session", uselist=False, cascade="all, delete-orphan")
    metrics_tactical = relationship("MetricsTactical", back_populates="session", uselist=False, cascade="all, delete-orphan")
    metrics_psych = relationship("MetricsPsych", back_populates="session", uselist=False, cascade="all, delete-orphan")
    analytics_outputs = relationship("AnalyticsOutputs", back_populates="session", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("coach_rating >= 0 AND coach_rating <= 10", name="check_coach_rating"),
        CheckConstraint("minutes_played >= 0", name="check_minutes_played"),
    )

    def __repr__(self):
        return f"<Session {self.session_date} - {self.session_type.value}>"


class MetricsPhysical(Base):
    """Physical metrics for a session."""
    __tablename__ = "metrics_physical"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)

    height_cm = Column(Numeric(5, 2), nullable=True)
    weight_kg = Column(Numeric(5, 2), nullable=True)
    bmi = Column(Numeric(5, 2), nullable=True)  # Calculated server-side
    body_fat_pct = Column(Numeric(4, 2), nullable=True)
    lean_mass_kg = Column(Numeric(5, 2), nullable=True)
    resting_hr_bpm = Column(Integer, nullable=False)
    max_speed_kmh = Column(Numeric(5, 2), nullable=True)
    accel_0_10m_s = Column(Numeric(4, 2), nullable=True)
    accel_0_20m_s = Column(Numeric(4, 2), nullable=True)
    distance_km = Column(Numeric(5, 2), nullable=False)
    sprints_over_25kmh = Column(Integer, nullable=False, default=0)
    vertical_jump_cm = Column(Numeric(5, 2), nullable=True)
    agility_illinois_s = Column(Numeric(5, 2), nullable=True)
    yoyo_level = Column(Numeric(5, 2), nullable=True)
    rpe = Column(Numeric(3, 1), nullable=False)  # 1-10
    sleep_hours = Column(Numeric(4, 2), nullable=True)  # 0-12

    # Relationship
    session = relationship("Session", back_populates="metrics_physical")

    __table_args__ = (
        CheckConstraint("rpe >= 1 AND rpe <= 10", name="check_rpe"),
        CheckConstraint("sleep_hours >= 0 AND sleep_hours <= 12", name="check_sleep_hours"),
    )


class MetricsTechnical(Base):
    """Technical metrics for a session."""
    __tablename__ = "metrics_technical"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)

    passes_attempted = Column(Integer, nullable=False, default=0)
    passes_completed = Column(Integer, nullable=False, default=0)
    pass_accuracy_pct = Column(Numeric(5, 2), nullable=True)  # Calculated
    progressive_passes = Column(Integer, nullable=False, default=0)
    long_pass_accuracy_pct = Column(Numeric(5, 2), nullable=True)
    shots = Column(Integer, nullable=False, default=0)
    shots_on_target = Column(Integer, nullable=False, default=0)
    shot_accuracy_pct = Column(Numeric(5, 2), nullable=True)  # Calculated
    crosses = Column(Integer, nullable=True, default=0)
    cross_accuracy_pct = Column(Numeric(5, 2), nullable=True)
    successful_dribbles = Column(Integer, nullable=False, default=0)
    failed_dribbles = Column(Integer, nullable=False, default=0)
    dribble_success_pct = Column(Numeric(5, 2), nullable=True)  # Calculated
    ball_losses = Column(Integer, nullable=False, default=0)
    ball_recoveries = Column(Integer, nullable=False, default=0)
    set_piece_accuracy_pct = Column(Numeric(5, 2), nullable=True)

    # Relationship
    session = relationship("Session", back_populates="metrics_technical")


class MetricsTactical(Base):
    """Tactical metrics for a session."""
    __tablename__ = "metrics_tactical"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)

    xg = Column(Numeric(5, 3), nullable=True)
    xa = Column(Numeric(5, 3), nullable=True)
    pressures = Column(Integer, nullable=True, default=0)
    interceptions = Column(Integer, nullable=False, default=0)
    heatmap_zone_json = Column(JSON, nullable=True)
    influence_zones_pct = Column(Numeric(5, 2), nullable=True)
    effective_off_ball_runs = Column(Integer, nullable=True, default=0)
    transition_reaction_time_s = Column(Numeric(5, 2), nullable=True)
    involvement_pct = Column(Numeric(5, 2), nullable=True)

    # Relationship
    session = relationship("Session", back_populates="metrics_tactical")


class MetricsPsych(Base):
    """Psychological metrics for a session."""
    __tablename__ = "metrics_psych"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)

    attention_score = Column(Integer, nullable=True)  # 0-100
    decision_making = Column(Integer, nullable=True)  # 1-10
    motivation = Column(Integer, nullable=True)  # 1-10
    stress_management = Column(Integer, nullable=True)  # 1-10
    self_esteem = Column(Integer, nullable=True)  # 1-10
    team_leadership = Column(Integer, nullable=True)  # 1-10
    sleep_quality = Column(Integer, nullable=True)  # 1-10
    mood_pre = Column(Integer, nullable=True)  # 1-10
    mood_post = Column(Integer, nullable=True)  # 1-10
    tactical_adaptability = Column(Integer, nullable=True)  # 1-10

    # Relationship
    session = relationship("Session", back_populates="metrics_psych")

    __table_args__ = (
        CheckConstraint("attention_score >= 0 AND attention_score <= 100", name="check_attention"),
        CheckConstraint("decision_making >= 1 AND decision_making <= 10", name="check_decision"),
        CheckConstraint("motivation >= 1 AND motivation <= 10", name="check_motivation"),
        CheckConstraint("stress_management >= 1 AND stress_management <= 10", name="check_stress"),
        CheckConstraint("self_esteem >= 1 AND self_esteem <= 10", name="check_esteem"),
        CheckConstraint("team_leadership >= 1 AND team_leadership <= 10", name="check_leadership"),
        CheckConstraint("sleep_quality >= 1 AND sleep_quality <= 10", name="check_sleep_quality"),
        CheckConstraint("mood_pre >= 1 AND mood_pre <= 10", name="check_mood_pre"),
        CheckConstraint("mood_post >= 1 AND mood_post <= 10", name="check_mood_post"),
        CheckConstraint("tactical_adaptability >= 1 AND tactical_adaptability <= 10", name="check_tactical_adapt"),
    )


class AnalyticsOutputs(Base):
    """Analytics outputs and calculated performance indices."""
    __tablename__ = "analytics_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)

    performance_index = Column(Numeric(6, 2), nullable=False)  # 0-100
    progress_index_rolling = Column(Numeric(6, 2), nullable=True)  # 4-week rolling avg
    zscore_vs_player_baseline = Column(Numeric(6, 3), nullable=True)
    cluster_label = Column(String(50), nullable=True)  # TECH/TACTIC/PHYSICAL/PSYCH
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    session = relationship("Session", back_populates="analytics_outputs")

    __table_args__ = (
        CheckConstraint("performance_index >= 0 AND performance_index <= 100", name="check_perf_index"),
    )
