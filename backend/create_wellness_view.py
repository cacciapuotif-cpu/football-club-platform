"""
Create vw_wellness_summary view for wellness summary endpoint.
"""

import asyncio
from sqlalchemy import text
from app.database import get_session_context


async def create_wellness_view():
    """Create wellness summary view."""

    async with get_session_context() as session:
        try:
            # Drop view if exists
            await session.execute(text("DROP VIEW IF EXISTS vw_wellness_summary"))
            print("✅ Dropped existing view (if any)")

            # Create view
            create_view_sql = text("""
                CREATE VIEW vw_wellness_summary AS
                SELECT
                    p.id AS player_id,
                    p.last_name AS cognome,
                    p.first_name AS nome,
                    p.role_primary AS ruolo,
                    COUNT(w.date) AS wellness_sessions_count,
                    MAX(w.date) AS last_entry_date
                FROM players p
                LEFT JOIN wellness_data w ON p.id = w.player_id
                GROUP BY p.id, p.last_name, p.first_name, p.role_primary
            """)

            await session.execute(create_view_sql)
            await session.commit()

            print("✅ Created vw_wellness_summary view")

            # Verify view works
            result = await session.execute(text("SELECT COUNT(*) FROM vw_wellness_summary"))
            count = result.scalar()
            print(f"📊 View contains {count} player records")

            # Show sample data
            result = await session.execute(text("""
                SELECT
                    cognome,
                    nome,
                    ruolo,
                    wellness_sessions_count,
                    last_entry_date
                FROM vw_wellness_summary
                ORDER BY cognome
                LIMIT 5
            """))

            print("\n📋 Sample data from view:")
            for row in result:
                print(f"  - {row.cognome} {row.nome} ({row.ruolo}): {row.wellness_sessions_count} sessions, last: {row.last_entry_date}")

        except Exception as e:
            print(f"❌ Error creating view: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_wellness_view())
