"""
Seed Runner - Orchestrates idempotent database seeding
Executes steps in topological order with transaction safety.
"""

import importlib
import sys
import time
from pathlib import Path
from typing import Any, Dict

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from seeds.config import (
    DATABASE_URL,
    DATASET,
    DATASET_FILES,
    SEED_STEPS,
    SEED_VERBOSE,
    display_config,
)
from seeds.utils import tx


class SeedRunner:
    """Orchestrates the seeding process."""

    def __init__(self, dataset: str = DATASET):
        self.dataset = dataset
        self.dataset_file = DATASET_FILES.get(dataset)

        if not self.dataset_file or not self.dataset_file.exists():
            raise FileNotFoundError(
                f"Dataset '{dataset}' not found. "
                f"Expected: {self.dataset_file}"
            )

        self.data = self._load_dataset()
        self.engine = create_engine(DATABASE_URL, echo=SEED_VERBOSE)
        self.stats = {step: {} for step in SEED_STEPS}

    def _load_dataset(self) -> Dict[str, Any]:
        """Load YAML dataset file."""
        with open(self.dataset_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def run(self):
        """Execute all seed steps in order."""
        start_time = time.time()

        print("\n" + "=" * 80)
        print("🌱 FOOTBALL CLUB PLATFORM - DATABASE SEEDING")
        print("=" * 80)
        display_config()
        print()

        with Session(self.engine) as session:
            for step_name in SEED_STEPS:
                self._run_step(session, step_name)

        elapsed = time.time() - start_time
        self._print_summary(elapsed)

    def _run_step(self, session: Session, step_name: str):
        """Execute a single seed step."""
        print(f"\n📦 Step: {step_name}")
        print("-" * 80)

        # Import step module dynamically
        try:
            module = importlib.import_module(f"seeds.steps.{step_name}")
        except ImportError as e:
            print(f"⚠️  Skipping {step_name}: module not found ({e})")
            return

        # Check if step function exists
        if not hasattr(module, "seed"):
            print(f"⚠️  Skipping {step_name}: 'seed()' function not found")
            return

        # Execute step with transaction
        try:
            with tx(session):
                step_data = self.data.get(step_name.replace("_", "-"), {})
                stats = module.seed(session, step_data)
                self.stats[step_name] = stats

                # Print step stats
                if stats:
                    for entity, counts in stats.items():
                        if isinstance(counts, dict):
                            print(
                                f"   ✅ {entity}: "
                                f"{counts.get('create', 0)} created, "
                                f"{counts.get('update', 0)} updated, "
                                f"{counts.get('skip', 0)} skipped"
                            )
                        else:
                            print(f"   ✅ {entity}: {counts}")
                else:
                    print(f"   ✅ {step_name}: completed (no stats)")

        except Exception as e:
            print(f"❌ Error in {step_name}: {e}")
            raise

    def _print_summary(self, elapsed: float):
        """Print final summary."""
        print("\n" + "=" * 80)
        print("📊 SEEDING SUMMARY")
        print("=" * 80)

        total_created = 0
        total_updated = 0
        total_skipped = 0

        for step_name, stats in self.stats.items():
            if stats:
                for entity, counts in stats.items():
                    if isinstance(counts, dict):
                        total_created += counts.get("create", 0)
                        total_updated += counts.get("update", 0)
                        total_skipped += counts.get("skip", 0)

        print(f"Total Created:  {total_created}")
        print(f"Total Updated:  {total_updated}")
        print(f"Total Skipped:  {total_skipped}")
        print(f"Time Elapsed:   {elapsed:.2f}s")
        print("=" * 80)
        print("🎉 SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 80)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed Football Club Platform database")
    parser.add_argument(
        "--dataset",
        type=str,
        choices=["minimal", "staging", "demo"],
        default=DATASET,
        help="Dataset to seed (default: from env DATASET or 'minimal')"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=SEED_VERBOSE,
        help="Enable verbose SQL logging"
    )

    args = parser.parse_args()

    try:
        runner = SeedRunner(dataset=args.dataset)
        runner.run()
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
