"""Utility to run Great Expectations checkpoint."""

from __future__ import annotations

import sys

from great_expectations.checkpoint import SimpleCheckpoint
from great_expectations.data_context import BaseDataContext


def main(name: str) -> int:
    context = BaseDataContext()
    checkpoint: SimpleCheckpoint = context.get_checkpoint(name)
    results = checkpoint.run()
    if not results["success"]:
        print(f"Checkpoint {name} failed")
        return 1
    print(f"Checkpoint {name} succeeded")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: poetry run python scripts/run_ge_checkpoint.py <checkpoint-name>")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))

