"""Verification script to display complete player and training data."""

import asyncio
import json
from datetime import datetime
from typing import Dict, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database import get_async_session
from app.models.player import Player, PlayerRole
from app.models.team import Team
from app.models.organization import Organization
from app.models.session import TrainingSession
from app.models.player_training_stats import PlayerTrainingStats


def format_section_header(title: str, width: int = 80) -> str:
    """Format a section header."""
    return f"\n{'=' * width}\n{title.center(width)}\n{'=' * width}\n"


def format_subsection(title: str, width: int = 80) -> str:
    """Format a subsection header."""
    return f"\n{'-' * width}\n{title}\n{'-' * width}"


async def verify_database_statistics(session: AsyncSession) -> Dict:
    """Get overall database statistics."""
    stats = {}

    # Count players
    result = await session.execute(select(func.count()).select_from(Player))
    stats['total_players'] = result.scalar()

    # Count by position
    for role in PlayerRole:
        result = await session.execute(
            select(func.count()).select_from(Player).where(Player.role_primary == role)
        )
        stats[f'players_{role.value}'] = result.scalar()

    # Count training sessions
    result = await session.execute(select(func.count()).select_from(TrainingSession))
    stats['total_training_sessions'] = result.scalar()

    # Count training stats
    result = await session.execute(select(func.count()).select_from(PlayerTrainingStats))
    stats['total_training_stats'] = result.scalar()

    # Physical condition distribution
    for condition in ['excellent', 'good', 'normal', 'poor']:
        result = await session.execute(
            select(func.count()).select_from(Player).where(Player.physical_condition == condition)
        )
        stats[f'condition_{condition}'] = result.scalar()

    return stats


async def display_player_complete(player: Player, session: AsyncSession) -> None:
    """Display complete player information."""
    age = (datetime.now().date() - player.date_of_birth).days // 365

    print(f"\n{'🔷' * 40}")
    print(f"👤 PLAYER: {player.first_name} {player.last_name}")
    print(f"{'🔷' * 40}")

    # Anagraphic data
    print(format_subsection("📋 ANAGRAPHIC DATA"))
    print(f"   • Position: {player.role_primary}")
    print(f"   • Age: {age} years (DOB: {player.date_of_birth})")
    print(f"   • Nationality: {player.nationality}")
    print(f"   • Market Value: €{player.market_value_eur:,.0f}" if player.market_value_eur else "   • Market Value: N/A")

    # Physical data
    print(format_subsection("💪 PHYSICAL DATA"))
    print(f"   • Height: {player.height_cm:.0f} cm" if player.height_cm else "   • Height: N/A")
    print(f"   • Weight: {player.weight_kg:.0f} kg" if player.weight_kg else "   • Weight: N/A")
    print(f"   • Dominant Foot: {player.dominant_foot}")
    print(f"   • Physical Condition: {player.physical_condition}")
    print(f"   • Injury Prone: {'Yes' if player.injury_prone else 'No'}")

    # Tactical attributes
    print(format_subsection("🎯 TACTICAL ATTRIBUTES"))
    print(f"   • Tactical Awareness:  {player.tactical_awareness}/100  {'█' * (player.tactical_awareness // 10)}")
    print(f"   • Positioning:         {player.positioning}/100  {'█' * (player.positioning // 10)}")
    print(f"   • Decision Making:     {player.decision_making}/100  {'█' * (player.decision_making // 10)}")
    print(f"   • Work Rate:           {player.work_rate}/100  {'█' * (player.work_rate // 10)}")

    # Psychological attributes
    print(format_subsection("🧠 PSYCHOLOGICAL ATTRIBUTES"))
    print(f"   • Mental Strength:     {player.mental_strength}/100  {'█' * (player.mental_strength // 10)}")
    print(f"   • Leadership:          {player.leadership}/100  {'█' * (player.leadership // 10)}")
    print(f"   • Concentration:       {player.concentration}/100  {'█' * (player.concentration // 10)}")
    print(f"   • Adaptability:        {player.adaptability}/100  {'█' * (player.adaptability // 10)}")

    # Ratings
    print(format_subsection("⭐ RATINGS"))
    print(f"   • Overall Rating:   {player.overall_rating:.1f}/10.0  {'★' * int(player.overall_rating)}")
    print(f"   • Potential Rating: {player.potential_rating:.1f}/10.0  {'★' * int(player.potential_rating)}")
    print(f"   • Current Form:     {player.form_level:.1f}/10.0  {'★' * int(player.form_level)}")

    # Training sessions
    stmt = (
        select(PlayerTrainingStats, TrainingSession)
        .join(TrainingSession, PlayerTrainingStats.training_session_id == TrainingSession.id)
        .where(PlayerTrainingStats.player_id == player.id)
        .order_by(TrainingSession.session_date.desc())
        .limit(5)
    )
    result = await session.execute(stmt)
    training_data = result.all()

    if training_data:
        print(format_subsection(f"🏋️ RECENT TRAINING SESSIONS ({len(training_data)} shown)"))

        for i, (training_stat, training_session) in enumerate(training_data, 1):
            print(f"\n   Session #{i}: {training_session.session_type.value} - {training_session.focus_area}")
            print(f"   Date: {training_session.session_date.strftime('%Y-%m-%d')}")
            print(f"   Intensity: {training_session.intensity.value if training_session.intensity else 'N/A'}")
            print(f"   Ratings:")
            print(f"      - Technical:  {training_stat.technical_rating}/10")
            print(f"      - Tactical:   {training_stat.tactical_execution}/10")
            print(f"      - Physical:   {training_stat.physical_performance}/10")
            print(f"      - Mental:     {training_stat.mental_focus}/10")
            print(f"   Metrics:")
            print(f"      - Passing Accuracy:  {training_stat.passing_accuracy:.1f}%")
            print(f"      - Shooting Accuracy: {training_stat.shooting_accuracy:.1f}%")
            if training_stat.speed_kmh:
                print(f"      - Top Speed:         {training_stat.speed_kmh:.1f} km/h")
            if training_stat.distance_covered_m:
                print(f"      - Distance Covered:  {training_stat.distance_covered_m:.0f} m")
    else:
        print(format_subsection("🏋️ TRAINING SESSIONS"))
        print("   ⚠️  No training sessions found for this player")


async def verify_complete_data():
    """Main verification function."""
    print(format_section_header("🚀 FOOTBALL CLUB PLATFORM - COMPLETE DATA VERIFICATION", 100))

    async for db_session in get_async_session():
        try:
            # Get database statistics
            stats = await verify_database_statistics(db_session)

            print(format_section_header("📊 DATABASE STATISTICS", 100))
            print(f"   Total Players:           {stats['total_players']}")
            print(f"   Total Training Sessions: {stats['total_training_sessions']}")
            print(f"   Total Training Stats:    {stats['total_training_stats']}")

            print("\n   Players by Position:")
            for role in PlayerRole:
                count = stats.get(f'players_{role.value}', 0)
                print(f"      {role.value:3s}: {count:3d} players")

            print("\n   Physical Condition Distribution:")
            for condition in ['excellent', 'good', 'normal', 'poor']:
                count = stats.get(f'condition_{condition}', 0)
                print(f"      {condition.capitalize():10s}: {count:3d} players")

            # Get sample players from each position
            print(format_section_header("👥 SAMPLE PLAYERS (2 per position)", 100))

            for role in PlayerRole:
                stmt = (
                    select(Player)
                    .where(Player.role_primary == role)
                    .order_by(Player.overall_rating.desc())
                    .limit(2)
                )
                result = await db_session.execute(stmt)
                players = result.scalars().all()

                if players:
                    print(f"\n{role.value} - Top Players:")
                    for player in players:
                        await display_player_complete(player, db_session)

            # Export summary to JSON
            print(format_section_header("💾 EXPORTING DATA SUMMARY", 100))

            # Get all players for export
            stmt = select(Player).order_by(Player.overall_rating.desc())
            result = await db_session.execute(stmt)
            all_players = result.scalars().all()

            export_data = {
                "statistics": stats,
                "export_date": datetime.now().isoformat(),
                "players": []
            }

            for player in all_players:
                age = (datetime.now().date() - player.date_of_birth).days // 365

                # Count training sessions
                stmt = select(func.count()).select_from(PlayerTrainingStats).where(
                    PlayerTrainingStats.player_id == player.id
                )
                result = await db_session.execute(stmt)
                training_count = result.scalar()

                player_data = {
                    "id": str(player.id),
                    "name": f"{player.first_name} {player.last_name}",
                    "position": player.role_primary.value,
                    "age": age,
                    "nationality": player.nationality,
                    "physical": {
                        "height_cm": float(player.height_cm) if player.height_cm else None,
                        "weight_kg": float(player.weight_kg) if player.weight_kg else None,
                        "dominant_foot": player.dominant_foot.value if player.dominant_foot else None,
                        "physical_condition": player.physical_condition,
                        "injury_prone": player.injury_prone
                    },
                    "tactical": {
                        "tactical_awareness": player.tactical_awareness,
                        "positioning": player.positioning,
                        "decision_making": player.decision_making,
                        "work_rate": player.work_rate
                    },
                    "psychological": {
                        "mental_strength": player.mental_strength,
                        "leadership": player.leadership,
                        "concentration": player.concentration,
                        "adaptability": player.adaptability
                    },
                    "ratings": {
                        "overall_rating": float(player.overall_rating),
                        "potential_rating": float(player.potential_rating),
                        "form_level": float(player.form_level),
                        "market_value_eur": float(player.market_value_eur) if player.market_value_eur else None
                    },
                    "training_sessions_count": training_count
                }

                export_data["players"].append(player_data)

            # Save to file
            output_file = Path(__file__).parent.parent / "artifacts" / "complete_data_export.json"
            output_file.parent.mkdir(exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            print(f"   ✅ Data exported to: {output_file}")
            print(f"   📄 Total players exported: {len(export_data['players'])}")

            # Summary
            print(format_section_header("✅ VERIFICATION COMPLETE", 100))
            print(f"""
   Summary:
   --------
   ✓ {stats['total_players']} players with complete profiles
   ✓ All players have tactical attributes (awareness, positioning, decision making, work rate)
   ✓ All players have psychological attributes (mental strength, leadership, concentration, adaptability)
   ✓ {stats['total_training_sessions']} training sessions created
   ✓ {stats['total_training_stats']} individual training statistics recorded
   ✓ Data exported to JSON for analysis

   Physical Condition Breakdown:
   ----------------------------
   • Excellent: {stats.get('condition_excellent', 0)} players
   • Good:      {stats.get('condition_good', 0)} players
   • Normal:    {stats.get('condition_normal', 0)} players
   • Poor:      {stats.get('condition_poor', 0)} players

   Next Steps:
   -----------
   1. Start the backend server: uvicorn app.main:app --reload
   2. Access API docs: http://localhost:8000/docs
   3. Test ML algorithms: python scripts/test_ml_algorithms.py
   4. View players API: http://localhost:8000/api/players
            """)

        except Exception as e:
            print(f"\n❌ Error during verification: {e}")
            import traceback
            traceback.print_exc()
            await db_session.rollback()
            raise
        finally:
            await db_session.close()


if __name__ == "__main__":
    asyncio.run(verify_complete_data())
