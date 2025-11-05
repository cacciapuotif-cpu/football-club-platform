"""
Seed Configuration with Port Guard-Rails
Ensures Football Club Platform never conflicts with pythonpro on port 3001.
"""

import os
import sys
from pathlib import Path
from typing import Literal

# ============================================================================
# PORT GUARD-RAILS (CRITICAL)
# ============================================================================

RESERVED_PORT = 3001  # Reserved for pythonpro - DO NOT USE
PYTHONPRO_PROJECT = "pythonpro"

FCP_WEB_PORT = int(os.getenv("FCP_WEB_PORT", "3000"))
FCP_API_PORT = int(os.getenv("FCP_API_PORT", "8000"))
FCP_API_PORT_ALT = int(os.getenv("FCP_API_PORT_ALT", "8001"))
FCP_DB_PORT = int(os.getenv("FCP_DB_PORT", "5434"))
FCP_REDIS_PORT = int(os.getenv("FCP_REDIS_PORT", "6381"))

# Validate ports at import time
def _validate_ports():
    """Abort immediately if any FCP port conflicts with reserved port 3001."""
    fcp_ports = {
        "FCP_WEB_PORT": FCP_WEB_PORT,
        "FCP_API_PORT": FCP_API_PORT,
        "FCP_API_PORT_ALT": FCP_API_PORT_ALT,
        "FCP_DB_PORT": FCP_DB_PORT,
        "FCP_REDIS_PORT": FCP_REDIS_PORT,
    }

    for var_name, port in fcp_ports.items():
        if port == RESERVED_PORT:
            sys.stderr.write(
                f"\n{'='*80}\n"
                f"❌ FATAL ERROR: Port Conflict Detected\n"
                f"{'='*80}\n"
                f"Variable: {var_name}={port}\n"
                f"Port {RESERVED_PORT} is RESERVED for {PYTHONPRO_PROJECT}.\n"
                f"Football Club Platform cannot use this port.\n\n"
                f"Fix: Set {var_name} to a different port (e.g., 3000, 8000, etc.)\n"
                f"{'='*80}\n"
            )
            sys.exit(1)

_validate_ports()

# ============================================================================
# SEED CONFIGURATION
# ============================================================================

DATASET_TYPE = Literal["minimal", "staging", "demo"]

# Get dataset from environment or CLI
DATASET: DATASET_TYPE = os.getenv("DATASET", "minimal")  # type: ignore

# Project paths
# Inside Docker container, backend is at /app, so seeds is at /app/seeds
PROJECT_ROOT = Path(__file__).parent.parent  # /app
SEEDS_DIR = PROJECT_ROOT / "seeds"            # /app/seeds
DATASETS_DIR = SEEDS_DIR / "datasets"         # /app/seeds/datasets
STEPS_DIR = SEEDS_DIR / "steps"               # /app/seeds/steps

# Database URL (from environment)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://app:changeme@localhost:{FCP_DB_PORT}/football_club_platform"
)

# Convert async URL to sync for seeding if needed
if "asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")
elif "postgresql://" in DATABASE_URL and "+psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")

# Production safety
SEED_ALLOW_PROD = os.getenv("SEED_ALLOW_PROD", "false").lower() == "true"
APP_ENV = os.getenv("APP_ENV", "development")

if APP_ENV == "production" and DATASET == "demo" and not SEED_ALLOW_PROD:
    sys.stderr.write(
        f"\n{'='*80}\n"
        f"❌ BLOCKED: Demo Seed in Production\n"
        f"{'='*80}\n"
        f"Cannot run 'demo' dataset in production environment.\n"
        f"Set SEED_ALLOW_PROD=true to override (not recommended).\n"
        f"{'='*80}\n"
    )
    sys.exit(1)

# Logging
SEED_VERBOSE = os.getenv("SEED_VERBOSE", "true").lower() == "true"

# ============================================================================
# DATASET CONFIGURATION
# ============================================================================

DATASET_FILES = {
    "minimal": DATASETS_DIR / "minimal.yaml",
    "staging": DATASETS_DIR / "staging.yaml",
    "demo": DATASETS_DIR / "demo.yaml",
}

# Step execution order (topological order based on FK dependencies)
SEED_STEPS = [
    "01_organizations",
    "02_seasons",
    "03_teams",
    "04_users",
    "05_players",
    "99_relations",  # N-N relationships and late FK bindings
]

# ============================================================================
# DISPLAY CONFIGURATION
# ============================================================================

def display_config():
    """Display current seed configuration."""
    print("=" * 80)
    print("⚙️  SEED CONFIGURATION")
    print("=" * 80)
    print(f"Dataset:       {DATASET}")
    print(f"Environment:   {APP_ENV}")
    print(f"Database:      {DATABASE_URL[:50]}...")
    print(f"Project Root:  {PROJECT_ROOT}")
    print("-" * 80)
    print("🔒 PORT CONFIGURATION (Guard-Rails Active)")
    print("-" * 80)
    print(f"FCP Web Port:      {FCP_WEB_PORT}")
    print(f"FCP API Port:      {FCP_API_PORT}")
    print(f"FCP API Alt Port:  {FCP_API_PORT_ALT}")
    print(f"FCP DB Port:       {FCP_DB_PORT}")
    print(f"FCP Redis Port:    {FCP_REDIS_PORT}")
    print(f"Reserved Port:     {RESERVED_PORT} (pythonpro - DO NOT USE)")
    print("=" * 80)

if __name__ == "__main__":
    display_config()
