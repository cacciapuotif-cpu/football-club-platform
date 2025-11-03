"""
Simple seed script to populate database with minimal data.
"""

import asyncio
from datetime import datetime, date
from uuid import uuid4

from sqlalchemy import text
from app.database import get_session_context


async def seed_simple():
    """Seed database with minimal required data."""

    print("=" * 80)
    print("🌱 SEEDING DATABASE - Simple Demo Data")
    print("=" * 80)

    async with get_session_context() as session:
        try:
            # Create organization
            print("\n🏢 Creating organization...")
            org_id = uuid4()
            await session.execute(
                text("""
                    INSERT INTO organizations (id, name, slug, created_at, updated_at)
                    VALUES (:id, :name, :slug, :created, :updated)
                    ON CONFLICT DO NOTHING
                """),
                {
                    "id": org_id,
                    "name": "Football Club Demo",
                    "slug": "football-club-demo",
                    "created": datetime.utcnow(),
                    "updated": datetime.utcnow()
                }
            )
            await session.commit()
            print(f"✅ Organization created: {org_id}")

            # Create admin user
            print("\n👤 Creating admin user...")
            user_id = uuid4()
            await session.execute(
                text("""
                    INSERT INTO users (id, email, hashed_password, role, full_name, is_active, organization_id, created_at, updated_at)
                    VALUES (:id, :email, :password, :role, :name, :active, :org_id, :created, :updated)
                    ON CONFLICT DO NOTHING
                """),
                {
                    "id": user_id,
                    "email": "admin@demo.com",
                    "password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyMK1U4L0ZG2",  # password: admin123
                    "role": "ADMIN",
                    "name": "Admin User",
                    "active": True,
                    "org_id": org_id,
                    "created": datetime.utcnow(),
                    "updated": datetime.utcnow()
                }
            )
            await session.commit()
            print(f"✅ Admin user created: admin@demo.com / admin123")

            # Create 5 simple players
            print("\n⚽ Creating 5 demo players...")
            players_data = [
                ("Marco", "Rossi", date(2008, 5, 15), "FW", 10),
                ("Luca", "Bianchi", date(2009, 3, 22), "MF", 8),
                ("Giovanni", "Verdi", date(2008, 11, 8), "DF", 5),
                ("Andrea", "Neri", date(2009, 7, 30), "MF", 6),
                ("Francesco", "Gialli", date(2008, 9, 12), "GK", 1),
            ]

            for first, last, dob, role, jersey in players_data:
                player_id = uuid4()
                await session.execute(
                    text("""
                        INSERT INTO players (
                            id, first_name, last_name, date_of_birth, role_primary,
                            jersey_number, is_active, organization_id, created_at, updated_at
                        )
                        VALUES (
                            :id, :first, :last, :dob, :role,
                            :jersey, :active, :org_id, :created, :updated
                        )
                    """),
                    {
                        "id": player_id,
                        "first": first,
                        "last": last,
                        "dob": dob,
                        "role": role,
                        "jersey": jersey,
                        "active": True,
                        "org_id": org_id,
                        "created": datetime.utcnow(),
                        "updated": datetime.utcnow()
                    }
                )
                print(f"   ✓ Created player: {first} {last} (#{jersey} - {role})")

            await session.commit()
            print("\n✅ All 5 players created successfully!")

            print("\n" + "=" * 80)
            print("🎉 DATABASE SEEDING COMPLETED!")
            print("=" * 80)
            print("\n📋 Login credentials:")
            print("   Email: admin@demo.com")
            print("   Password: admin123")
            print("\n")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_simple())
