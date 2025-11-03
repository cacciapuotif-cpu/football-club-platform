"""
Final seed script using SQLModel models directly.
"""

import asyncio
from datetime import datetime, date
from uuid import uuid4

from app.database import get_session_context
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.player import Player, PlayerRole, DominantFoot


async def seed_final():
    """Seed database with demo data using models."""

    print("=" * 80)
    print("🌱 SEEDING DATABASE - Football Club Platform")
    print("=" * 80)

    async with get_session_context() as session:
        try:
            # Create organization
            print("\n🏢 Creating organization...")
            org = Organization(
                name="Football Club Demo",
                slug="football-club-demo",
                email="contact@demo.com",
                country="IT"
            )
            session.add(org)
            await session.flush()
            print(f"✅ Organization created: {org.name} ({org.id})")

            # Create admin user
            print("\n👤 Creating admin user...")
            admin = User(
                email="admin@demo.com",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyMK1U4L0ZG2",  # password: admin123
                role=UserRole.ADMIN,
                full_name="Admin User",
                is_active=True,
                organization_id=org.id
            )
            session.add(admin)
            await session.flush()
            print(f"✅ Admin user created: {admin.email}")

            # Create 5 demo players
            print("\n⚽ Creating 5 demo players...")
            players_data = [
                ("Marco", "Rossi", date(2008, 5, 15), PlayerRole.FW, 10),
                ("Luca", "Bianchi", date(2009, 3, 22), PlayerRole.MF, 8),
                ("Giovanni", "Verdi", date(2008, 11, 8), PlayerRole.DF, 5),
                ("Andrea", "Neri", date(2009, 7, 30), PlayerRole.MF, 6),
                ("Francesco", "Gialli", date(2008, 9, 12), PlayerRole.GK, 1),
            ]

            for first, last, dob, role, jersey in players_data:
                player = Player(
                    first_name=first,
                    last_name=last,
                    date_of_birth=dob,
                    role_primary=role,
                    jersey_number=jersey,
                    dominant_foot=DominantFoot.RIGHT,
                    is_active=True,
                    organization_id=org.id
                )
                session.add(player)
                await session.flush()
                print(f"   ✓ Created player: {first} {last} (#{jersey} - {role.value})")

            await session.commit()
            print("\n✅ All data created successfully!")

            print("\n" + "=" * 80)
            print("🎉 DATABASE SEEDING COMPLETED!")
            print("=" * 80)
            print("\n📋 Login credentials:")
            print("   Email: admin@demo.com")
            print("   Password: admin123")
            print("\n✅ 5 players created and ready to use!")
            print("\n")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_final())
