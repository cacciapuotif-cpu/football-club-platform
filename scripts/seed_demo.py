#!/usr/bin/env python3
"""
Unified Demo Data Seeder - Idempotent

Creates comprehensive demo data for Football Club Platform platform:
- 1 Organization ("Demo FC")
- 1 Active Season (2024/2025)
- 1 Team ("Prima Squadra")
- 15 Players (4 GK, 4 DF, 4 MF, 3 FW)
- 8 Training Sessions with KPIs
- Wellness data and physical tests
- 1 Demo admin user

IDEMPOTENT: Can be run multiple times without creating duplicates.
"""

import asyncio
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from sqlmodel import Session

# Use sync session for seeding
from sqlalchemy import create_engine
from app.config import settings
from app.models import (
    Organization,
    Season,
    Team,
    Player,
    TrainingSession,
    PhysicalTest,
    WellnessData,
    User,
    TechnicalStats,
    TacticalCognitive,
)
from app.models.player import PlayerRole, DominantFoot, DominantArm
from app.models.session import SessionType

# Convert async URL to sync for seeding
database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")
engine = create_engine(database_url, echo=False)


def get_or_create_organization(session: Session) -> Organization:
    """Get or create demo organization."""
    statement = select(Organization).where(Organization.name == "Demo FC")
    org = session.exec(statement).first()

    if org:
        print(f"✓ Organization exists: {org.name} ({org.id})")
        return org

    org = Organization(
        id=uuid4(),
        name="Demo FC",
        slug="demo-fc",
        tax_code="12345678901",
        email="info@demofc.local",
        phone="+39 0123456789",
        address="Via dello Stadio, 1 - 00100 Roma RM",
        website="https://demofc.local",
        is_active=True,
    )
    session.add(org)
    session.commit()
    session.refresh(org)
    print(f"✓ Created organization: {org.name} ({org.id})")
    return org


def get_or_create_user(session: Session, org_id: UUID) -> User:
    """Get or create demo admin user."""
    user = session.exec(select(User).where(User.email == "admin@demofc.local")).first()

    if user:
        print(f"✓ User exists: {user.email}")
        return user

    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        id=uuid4(),
        email="admin@demofc.local",
        hashed_password=pwd_context.hash("demo123"),  # Default password
        full_name="Demo Admin",
        is_active=True,
        is_superuser=True,
        organization_id=org_id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    print(f"✓ Created user: {user.email} (password: demo123)")
    return user


def get_or_create_season(session: Session, org_id: UUID) -> Season:
    """Get or create current season."""
    season = session.exec(
        select(Season).where(
            Season.organization_id == org_id,
            Season.name == "2024/2025"
        )
    ).first()

    if season:
        print(f"✓ Season exists: {season.name}")
        return season

    season = Season(
        id=uuid4(),
        organization_id=org_id,
        name="2024/2025",
        start_date=date(2024, 8, 1),
        end_date=date(2025, 6, 30),
        is_active=True,
    )
    session.add(season)
    session.commit()
    session.refresh(season)
    print(f"✓ Created season: {season.name}")
    return season


def get_or_create_team(session: Session, org_id: UUID, season_id: UUID) -> Team:
    """Get or create demo team."""
    team = session.exec(
        select(Team).where(
            Team.organization_id == org_id,
            Team.name == "Prima Squadra"
        )
    ).first()

    if team:
        print(f"✓ Team exists: {team.name}")
        return team

    team = Team(
        id=uuid4(),
        organization_id=org_id,
        season_id=season_id,
        name="Prima Squadra",
        category="Senior",
        is_active=True,
    )
    session.add(team)
    session.commit()
    session.refresh(team)
    print(f"✓ Created team: {team.name}")
    return team


def create_players(session: Session, org_id: UUID, team_id: UUID) -> list[Player]:
    """Create demo players if they don't exist."""
    # Check if players already exist
    existing_count = session.exec(
        select(Player).where(Player.organization_id == org_id)
    ).all()

    if len(existing_count) >= 10:
        print(f"✓ Players already exist ({len(existing_count)} found)")
        return existing_count

    players_data = [
        # Goalkeepers
        ("Mario", "Rossi", PlayerRole.GK, 1, 185, 78, date(1995, 3, 15)),
        ("Luca", "Bianchi", PlayerRole.GK, 12, 188, 82, date(2000, 7, 22)),
        ("Alessandro", "Verdi", PlayerRole.GK, 22, 183, 76, date(1998, 11, 5)),
        ("Francesco", "Neri", PlayerRole.GK, 77, 190, 85, date(1996, 1, 30)),
        # Defenders
        ("Giuseppe", "Ferrari", PlayerRole.DF, 3, 180, 75, date(1997, 5, 10)),
        ("Antonio", "Russo", PlayerRole.DF, 4, 182, 77, date(1999, 9, 18)),
        ("Marco", "Romano", PlayerRole.DF, 5, 178, 73, date(1998, 2, 25)),
        ("Davide", "Marino", PlayerRole.DF, 13, 184, 79, date(1996, 12, 8)),
        # Midfielders
        ("Stefano", "Greco", PlayerRole.MF, 6, 176, 71, date(1999, 4, 12)),
        ("Andrea", "Bruno", PlayerRole.MF, 8, 175, 70, date(2000, 6, 7)),
        ("Matteo", "Gallo", PlayerRole.MF, 10, 177, 72, date(1997, 10, 20)),
        ("Lorenzo", "Conti", PlayerRole.MF, 14, 174, 69, date(1998, 8, 15)),
        # Forwards
        ("Simone", "Leone", PlayerRole.FW, 9, 181, 76, date(1996, 11, 28)),
        ("Riccardo", "Costa", PlayerRole.FW, 11, 179, 74, date(1999, 1, 5)),
        ("Paolo", "Serra", PlayerRole.FW, 18, 183, 78, date(1997, 7, 11)),
    ]

    players = []
    for first, last, role, jersey, height, weight, dob in players_data:
        player = Player(
            id=uuid4(),
            organization_id=org_id,
            team_id=team_id,
            first_name=first,
            last_name=last,
            date_of_birth=dob,
            place_of_birth="Roma, IT",
            nationality="IT",
            role_primary=role,
            jersey_number=jersey,
            height_cm=height,
            weight_kg=weight,
            bmi=round(weight / ((height / 100) ** 2), 1),
            dominant_foot=DominantFoot.RIGHT if jersey % 2 == 0 else DominantFoot.LEFT,
            dominant_arm=DominantArm.RIGHT,
            consent_given=True,
            consent_date=datetime.now(),
            medical_clearance=True,
            medical_clearance_expiry=date.today() + timedelta(days=365),
            is_active=True,
            is_injured=False,
        )
        session.add(player)
        session.flush()  # Flush each player individually
        players.append(player)

    session.commit()
    print(f"✓ Created {len(players)} players")
    return players


def create_young_players_with_tracking(session: Session, org_id: UUID, team_id: UUID) -> tuple[Player, Player]:
    """Create two young players (16 and 18 years old) with detailed tracking."""
    # Check if these players already exist
    young_player_16 = session.exec(
        select(Player).where(
            Player.organization_id == org_id,
            Player.first_name == "Giovanni",
            Player.last_name == "Giovani"
        )
    ).first()

    young_player_18 = session.exec(
        select(Player).where(
            Player.organization_id == org_id,
            Player.first_name == "Tommaso",
            Player.last_name == "Talenti"
        )
    ).first()

    if young_player_16 and young_player_18:
        print(f"✓ Young tracked players already exist")
        return young_player_16, young_player_18

    # Create 16-year-old player (MINOR - requires guardian)
    today = date.today()
    dob_16 = date(today.year - 16, 3, 15)  # 16 years old

    player_16 = Player(
        id=uuid4(),
        organization_id=org_id,
        team_id=team_id,
        first_name="Giovanni",
        last_name="Giovani",
        date_of_birth=dob_16,
        place_of_birth="Milano, IT",
        nationality="IT",
        is_minor=True,
        guardian_name="Marco Giovani",
        guardian_email="marco.giovani@example.com",
        guardian_phone="+39 333 1234567",
        role_primary=PlayerRole.MF,
        jersey_number=20,
        height_cm=172,
        weight_kg=65,
        bmi=22.0,
        dominant_foot=DominantFoot.RIGHT,
        dominant_arm=DominantArm.RIGHT,
        consent_given=True,
        consent_date=datetime.now(),
        consent_parent_given=True,
        medical_clearance=True,
        medical_clearance_expiry=date.today() + timedelta(days=365),
        is_active=True,
        notes="Giovane talento - monitoraggio intensivo progressi",
    )
    session.add(player_16)

    # Create 18-year-old player
    dob_18 = date(today.year - 18, 7, 22)  # 18 years old

    player_18 = Player(
        id=uuid4(),
        organization_id=org_id,
        team_id=team_id,
        first_name="Tommaso",
        last_name="Talenti",
        date_of_birth=dob_18,
        place_of_birth="Torino, IT",
        nationality="IT",
        is_minor=False,
        email="tommaso.talenti@example.com",
        phone="+39 345 7654321",
        role_primary=PlayerRole.FW,
        jersey_number=19,
        height_cm=178,
        weight_kg=71,
        bmi=22.4,
        dominant_foot=DominantFoot.LEFT,
        dominant_arm=DominantArm.LEFT,
        consent_given=True,
        consent_date=datetime.now(),
        medical_clearance=True,
        medical_clearance_expiry=date.today() + timedelta(days=365),
        is_active=True,
        notes="Giovane attaccante - monitoraggio progressi tecnici",
    )
    session.add(player_18)

    session.commit()
    session.refresh(player_16)
    session.refresh(player_18)

    print(f"✓ Created young tracked players: {player_16.first_name} (16yo) and {player_18.first_name} (18yo)")

    # Create 10 training sessions for each player with progress tracking
    create_individual_sessions_with_reports(session, org_id, team_id, player_16, "16yo midfielder")
    create_individual_sessions_with_reports(session, org_id, team_id, player_18, "18yo forward")

    return player_16, player_18


def create_individual_sessions_with_reports(
    session: Session,
    org_id: UUID,
    team_id: UUID,
    player: Player,
    player_desc: str
):
    """Create 10 individual training sessions with progress evaluation reports."""
    # Check if sessions already exist
    existing = session.exec(
        select(TechnicalStats).where(TechnicalStats.player_id == player.id)
    ).all()

    if len(existing) >= 10:
        print(f"  ✓ Sessions for {player.first_name} already exist ({len(existing)} found)")
        return

    base_date = datetime.now() - timedelta(days=90)  # Start 90 days ago

    # Progressive improvement data
    for session_num in range(1, 11):
        session_date = base_date + timedelta(days=session_num * 9)  # Every 9 days

        # Create training session
        training = TrainingSession(
            id=uuid4(),
            organization_id=org_id,
            team_id=team_id,
            session_date=session_date,
            session_type=SessionType.TRAINING,
            focus=f"Sessione {session_num}/10 - Sviluppo tecnico {player_desc}",
            duration_min=90,
            planned_intensity=6 + (session_num % 3),
            actual_intensity_avg=6.5 + (session_num % 3),
            distance_m=5000 + (session_num * 100),
            hi_distance_m=800 + (session_num * 30),
            sprints_count=12 + session_num,
            top_speed_ms=7.5 + (session_num * 0.1),
            hr_avg_bpm=150 + session_num,
            hr_max_bpm=180 + session_num,
            description=f"Sessione di allenamento individuale - Focus su miglioramento tecnico e tattico",
        )
        session.add(training)
        session.flush()  # Get ID for linking

        # Create technical stats (progress report)
        # Progressive improvement over sessions
        progress_factor = session_num / 10.0  # 0.1 to 1.0

        if player.role_primary == PlayerRole.MF:
            # Midfielder stats
            passes_total = 45 + int(session_num * 5)
            passes_acc = int(passes_total * (0.70 + progress_factor * 0.15))  # 70% -> 85%
            dribbles = 8 + session_num
            dribbles_succ = int(dribbles * (0.50 + progress_factor * 0.25))  # 50% -> 75%
            shots = 3 + (session_num // 2)
            shots_on_target = int(shots * (0.40 + progress_factor * 0.30))  # 40% -> 70%
        else:  # Forward
            passes_total = 30 + int(session_num * 3)
            passes_acc = int(passes_total * (0.65 + progress_factor * 0.20))  # 65% -> 85%
            dribbles = 10 + session_num
            dribbles_succ = int(dribbles * (0.55 + progress_factor * 0.25))  # 55% -> 80%
            shots = 6 + session_num
            shots_on_target = int(shots * (0.45 + progress_factor * 0.30))  # 45% -> 75%

        technical = TechnicalStats(
            id=uuid4(),
            organization_id=org_id,
            player_id=player.id,
            session_id=training.id,
            date=session_date.date(),
            passes_attempted=passes_total,
            passes_completed=passes_acc,
            pass_accuracy_pct=round((passes_acc / passes_total) * 100, 1),
            dribbles_attempted=dribbles,
            dribbles_successful=dribbles_succ,
            dribble_success_pct=round((dribbles_succ / dribbles) * 100, 1),
            shots_total=shots,
            shots_on_target=shots_on_target,
            shot_accuracy_pct=round((shots_on_target / shots) * 100, 1) if shots > 0 else 0,
            crosses_attempted=5 + session_num // 2,
            crosses_successful=2 + session_num // 3,
            touches=80 + session_num * 8,
            progressive_passes=8 + session_num,
            key_passes=2 + session_num // 3,
            notes=f"Sessione {session_num}/10 - Progressi evidenti in precisione e decision-making",
        )
        session.add(technical)

        # Create tactical/cognitive evaluation
        tactical = TacticalCognitive(
            id=uuid4(),
            organization_id=org_id,
            player_id=player.id,
            session_id=training.id,
            date=session_date.date(),
            positioning_rating=6.0 + progress_factor * 2.5,  # 6.0 -> 8.5
            decision_making_rating=5.5 + progress_factor * 3.0,  # 5.5 -> 8.5
            game_reading_rating=6.0 + progress_factor * 2.5,  # 6.0 -> 8.5
            reaction_time_ms=int(350 - progress_factor * 50),  # 350ms -> 300ms
            anticipation_rating=6.0 + progress_factor * 2.0,  # 6.0 -> 8.0
            spatial_awareness_rating=6.5 + progress_factor * 2.0,  # 6.5 -> 8.5
            tactical_adherence_pct=70 + progress_factor * 20,  # 70% -> 90%
            notes=f"Sessione {session_num}/10 - Miglioramento costante nella lettura del gioco",
        )
        session.add(tactical)

    session.commit()
    print(f"  ✓ Created 10 training sessions with progress reports for {player.first_name} {player.last_name}")


def create_training_sessions(session: Session, org_id: UUID, team_id: UUID) -> list[TrainingSession]:
    """Create demo training sessions."""
    # Check if sessions already exist
    existing = session.exec(
        select(TrainingSession).where(TrainingSession.organization_id == org_id)
    ).all()

    if len(existing) >= 6:
        print(f"✓ Training sessions already exist ({len(existing)} found)")
        return existing

    sessions_data = [
        (datetime.now() - timedelta(days=7), SessionType.TRAINING, "Tecnico", 90, 7),
        (datetime.now() - timedelta(days=6), SessionType.TACTICAL, "Tattico", 75, 6),
        (datetime.now() - timedelta(days=5), SessionType.GYM, "Fisico", 60, 8),
        (datetime.now() - timedelta(days=4), SessionType.TRAINING, "Tecnico", 90, 6),
        (datetime.now() - timedelta(days=3), SessionType.RECOVERY, "Recupero", 45, 4),
        (datetime.now() - timedelta(days=2), SessionType.TACTICAL, "Tattico", 80, 7),
        (datetime.now() - timedelta(days=1), SessionType.TRAINING, "Possesso palla", 85, 7),
        (datetime.now(), SessionType.TRAINING, "Partitella", 90, 8),
    ]

    sessions = []
    for session_date, session_type, focus, duration, intensity in sessions_data:
        training_session = TrainingSession(
            id=uuid4(),
            organization_id=org_id,
            team_id=team_id,
            session_date=session_date,
            session_type=session_type,
            focus=focus,
            duration_min=duration,
            planned_intensity=intensity,
            actual_intensity_avg=intensity + 0.5,
            distance_m=4500 + (intensity * 200),
            hi_distance_m=800 + (intensity * 50),
            sprints_count=15 + intensity,
            top_speed_ms=8.5 + (intensity * 0.2),
            hr_avg_bpm=145 + (intensity * 5),
            hr_max_bpm=175 + (intensity * 3),
        )
        session.add(training_session)
        sessions.append(training_session)

    session.commit()
    print(f"✓ Created {len(sessions)} training sessions")
    return sessions


def create_wellness_data(session: Session, org_id: UUID, players: list[Player]):
    """Create wellness data for players."""
    existing = session.exec(
        select(WellnessData).where(WellnessData.organization_id == org_id)
    ).all()

    if len(existing) > 0:
        print(f"✓ Wellness data already exists ({len(existing)} records)")
        return

    # Create wellness data for the last 7 days for a few players
    for player in players[:5]:  # First 5 players
        for days_ago in range(7):
            wellness = WellnessData(
                id=uuid4(),
                organization_id=org_id,
                player_id=player.id,
                date=date.today() - timedelta(days=days_ago),
                sleep_hours=7.0 + (days_ago % 2),
                sleep_quality=7 + (days_ago % 4),
                fatigue_level=4 + (days_ago % 3),
                muscle_soreness=3 + (days_ago % 4),
                stress_level=4 + (days_ago % 3),
                mood=7 + (days_ago % 4),
                readiness=7 + (days_ago % 4),
                notes=f"Wellness check - Day {days_ago}",
            )
            session.add(wellness)

    session.commit()
    print(f"✓ Created wellness data for 5 players (35 records)")


def create_physical_tests(session: Session, org_id: UUID, players: list[Player]):
    """Create physical test results."""
    existing = session.exec(
        select(PhysicalTest).where(PhysicalTest.organization_id == org_id)
    ).all()

    if len(existing) > 0:
        print(f"✓ Physical tests already exist ({len(existing)} records)")
        return

    test_date = date.today() - timedelta(days=10)

    for player in players:
        # Different tests based on role
        if player.role_primary == PlayerRole.GK:
            vo2max, sprint_10m, sprint_30m = 52, 1.95, 4.5
        elif player.role_primary == PlayerRole.DF:
            vo2max, sprint_10m, sprint_30m = 56, 1.85, 4.2
        elif player.role_primary == PlayerRole.MF:
            vo2max, sprint_10m, sprint_30m = 60, 1.80, 4.0
        else:  # FW
            vo2max, sprint_10m, sprint_30m = 58, 1.75, 3.9

        test = PhysicalTest(
            id=uuid4(),
            organization_id=org_id,
            player_id=player.id,
            test_date=test_date,
            test_type="Preseason Assessment",
            vo2max=vo2max,
            sprint_10m=sprint_10m,
            sprint_30m=sprint_30m,
            jump_height_cm=45 + (player.jersey_number % 10),
            agility_test_sec=10.5 - (player.jersey_number % 5) * 0.2,
            notes="Preseason physical assessment",
        )
        session.add(test)

    session.commit()
    print(f"✓ Created physical tests for {len(players)} players")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("Football Club Platform Demo Data Seeder (Idempotent)")
    print("=" * 60)
    print()

    try:
        with Session(engine) as session:
            # 1. Organization
            org = get_or_create_organization(session)

            # 2. User
            user = get_or_create_user(session, org.id)

            # 3. Season
            season = get_or_create_season(session, org.id)

            # 4. Team
            team = get_or_create_team(session, org.id, season.id)

            # 5. Players
            players = create_players(session, org.id, team.id)

            # 6. Young Players with Detailed Tracking (16 and 18 years old)
            young_16, young_18 = create_young_players_with_tracking(session, org.id, team.id)

            # 7. Training Sessions (general team sessions)
            sessions = create_training_sessions(session, org.id, team.id)

            # 8. Wellness Data
            create_wellness_data(session, org.id, players)

            # 8. Physical Tests
            create_physical_tests(session, org.id, players)

        print()
        print("=" * 60)
        print("✅ SEED COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("📊 Summary:")
        print(f"   Organization: {org.name}")
        print(f"   Season: {season.name}")
        print(f"   Team: {team.name}")
        print(f"   Players: {len(players)}")
        print(f"   Young Tracked Players: {young_16.first_name} (16yo) + {young_18.first_name} (18yo)")
        print(f"   Training Sessions (team): {len(sessions)}")
        print(f"   Individual Sessions (young players): 20 (10 each)")
        print(f"   Progress Reports: 20 (technical + tactical)")
        print(f"   User: {user.email} / demo123")
        print()
        print("🌐 Test the API:")
        print("   curl http://localhost:8000/api/v1/players")
        print("   curl http://localhost:8000/api/v1/sessions")
        print(f"   curl http://localhost:8000/api/v1/players/{young_16.id}")
        print(f"   curl http://localhost:8000/api/v1/players/{young_18.id}")
        print()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
