#!/usr/bin/env python3
"""
Football Club Platform - Unified Seed Entry Point
Supports SEED_PROFILE environment variable with profiles: DEMO_10x10, FULL_DEV
Maps to existing dataset system for compatibility.
"""

import os
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from seeds.runner import SeedRunner


# Profile to Dataset Mapping
PROFILE_TO_DATASET = {
    "DEMO_10x10": "demo",      # 10 players × 10+ sessions each
    "FULL_DEV": "staging",     # Full development dataset (60-90 days)
    "demo": "demo",            # Direct dataset names (backward compat)
    "staging": "staging",
    "minimal": "minimal",
}


def get_dataset_from_profile() -> str:
    """
    Resolve dataset name from SEED_PROFILE or DATASET env var.
    Priority: SEED_PROFILE > DATASET > default 'minimal'
    """
    # Check SEED_PROFILE first (new style)
    profile = os.getenv("SEED_PROFILE", "").strip()
    if profile:
        dataset = PROFILE_TO_DATASET.get(profile)
        if dataset:
            print(f"📌 Using SEED_PROFILE: {profile} → dataset: {dataset}")
            return dataset
        else:
            print(f"⚠️  Unknown SEED_PROFILE: {profile}")
            print(f"    Valid profiles: {', '.join(PROFILE_TO_DATASET.keys())}")
            sys.exit(1)

    # Fallback to DATASET (legacy style)
    dataset = os.getenv("DATASET", "minimal").strip()
    if dataset in PROFILE_TO_DATASET:
        print(f"📌 Using DATASET: {dataset}")
        return dataset
    else:
        print(f"⚠️  Unknown DATASET: {dataset}")
        print(f"    Valid datasets: minimal, staging, demo")
        sys.exit(1)


def main():
    """Main entry point for seeding."""
    print("\n" + "=" * 80)
    print("🌱 Football Club Platform - Database Seeding")
    print("=" * 80)

    # Resolve dataset
    dataset = get_dataset_from_profile()

    # Environment info
    app_env = os.getenv("APP_ENV", "development")
    database_url = os.getenv("DATABASE_URL", "")
    print(f"Environment:  {app_env}")
    print(f"Database:     {database_url[:60]}..." if len(database_url) > 60 else f"Database:     {database_url}")
    print(f"Dataset:      {dataset}")

    # Safety check for production
    if app_env == "production" and dataset in ["demo", "staging"]:
        allow_prod = os.getenv("SEED_ALLOW_PROD", "false").lower() == "true"
        if not allow_prod:
            print("\n" + "=" * 80)
            print("❌ BLOCKED: Cannot seed demo/staging data in production")
            print("=" * 80)
            print("Set SEED_ALLOW_PROD=true to override (NOT RECOMMENDED)")
            print("=" * 80)
            sys.exit(1)

    # Run seeder
    try:
        runner = SeedRunner(dataset=dataset)
        runner.run()
        print("\n✅ Seeding completed successfully!")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️  Seeding interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
