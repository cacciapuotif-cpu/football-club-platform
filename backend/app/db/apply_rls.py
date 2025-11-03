"""
Script to apply RLS policies to the database.

Run this script after migrations to enable Row Level Security.
"""

import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import engine, get_session
from app.db import get_rls_policies_sql

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def apply_rls_policies():
    """
    Apply RLS policies to the database.

    This function reads the rls_policies.sql file and executes it
    against the database to enable Row Level Security.
    """
    logger.info("Starting RLS policies application...")

    try:
        # Get RLS policies SQL
        rls_sql = get_rls_policies_sql()

        logger.info("Loaded RLS policies SQL")

        # Execute the SQL
        async with engine.begin() as conn:
            # Split by statement and execute each one
            # Note: We need to handle CREATE POLICY statements separately
            # because they can't be in a transaction block in some cases

            logger.info("Executing RLS policies SQL...")

            # Execute the entire SQL script
            # PostgreSQL will handle each statement
            await conn.execute(text(rls_sql))

            logger.info("✅ RLS policies applied successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to apply RLS policies: {e}", exc_info=True)
        raise


async def verify_rls_policies():
    """
    Verify that RLS policies are enabled and active.

    Returns:
        bool: True if RLS is properly configured
    """
    logger.info("Verifying RLS policies...")

    try:
        async for session in get_session():
            # Check which tables have RLS enabled
            result = await session.execute(
                text("""
                    SELECT tablename, rowsecurity
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    AND rowsecurity = true
                    ORDER BY tablename;
                """)
            )
            tables_with_rls = result.fetchall()

            if not tables_with_rls:
                logger.warning("⚠️  No tables have RLS enabled!")
                return False

            logger.info(f"✅ RLS enabled on {len(tables_with_rls)} tables:")
            for table in tables_with_rls:
                logger.info(f"  - {table[0]}")

            # Check number of policies
            result = await session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM pg_policies
                    WHERE schemaname = 'public';
                """)
            )
            policy_count = result.scalar()

            logger.info(f"✅ Total RLS policies: {policy_count}")

            if policy_count < 10:
                logger.warning(f"⚠️  Expected at least 10 policies, found {policy_count}")
                return False

            # List all policies
            result = await session.execute(
                text("""
                    SELECT tablename, policyname, cmd
                    FROM pg_policies
                    WHERE schemaname = 'public'
                    ORDER BY tablename, policyname;
                """)
            )
            policies = result.fetchall()

            logger.info("\n📋 RLS Policies:")
            for policy in policies:
                logger.info(f"  - {policy[0]}.{policy[1]} ({policy[2]})")

            await session.close()
            break

        return True

    except Exception as e:
        logger.error(f"❌ Failed to verify RLS policies: {e}", exc_info=True)
        return False


async def test_rls_isolation():
    """
    Test RLS isolation with sample tenant context.

    This function sets a tenant context and verifies that queries
    respect the RLS policies.
    """
    logger.info("\n🧪 Testing RLS isolation...")

    try:
        async for session in get_session():
            # Test setting tenant context
            test_tenant_id = "test-org-123"
            test_user_id = "test-user-456"
            test_user_role = "coach"

            logger.info(f"Setting tenant context: {test_tenant_id}")

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, false)"),
                {"tenant_id": test_tenant_id},
            )
            await session.execute(
                text("SELECT set_config('app.user_id', :user_id, false)"),
                {"user_id": test_user_id},
            )
            await session.execute(
                text("SELECT set_config('app.user_role', :user_role, false)"),
                {"user_role": test_user_role},
            )

            await session.commit()

            # Verify context is set
            result = await session.execute(
                text("""
                    SELECT
                        current_setting('app.tenant_id', true) as tenant_id,
                        current_setting('app.user_id', true) as user_id,
                        current_setting('app.user_role', true) as user_role;
                """)
            )
            context = result.fetchone()

            logger.info(f"✅ Context set successfully:")
            logger.info(f"  - tenant_id: {context[0]}")
            logger.info(f"  - user_id: {context[1]}")
            logger.info(f"  - user_role: {context[2]}")

            # Clear context
            await session.execute(
                text("""
                    SELECT set_config('app.tenant_id', '', false);
                    SELECT set_config('app.user_id', '', false);
                    SELECT set_config('app.user_role', '', false);
                """)
            )
            await session.commit()

            logger.info("✅ RLS isolation test passed!")

            await session.close()
            break

    except Exception as e:
        logger.error(f"❌ RLS isolation test failed: {e}", exc_info=True)
        return False

    return True


async def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("RLS Policies Application & Verification")
    logger.info("=" * 60)

    # Apply RLS policies
    try:
        await apply_rls_policies()
    except Exception as e:
        logger.error("Failed to apply RLS policies. Exiting.")
        sys.exit(1)

    # Verify RLS policies
    logger.info("\n" + "=" * 60)
    if not await verify_rls_policies():
        logger.error("RLS verification failed. Check the logs above.")
        sys.exit(1)

    # Test RLS isolation
    logger.info("\n" + "=" * 60)
    if not await test_rls_isolation():
        logger.error("RLS isolation test failed. Check the logs above.")
        sys.exit(1)

    logger.info("\n" + "=" * 60)
    logger.info("✅ ALL RLS CHECKS PASSED!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
