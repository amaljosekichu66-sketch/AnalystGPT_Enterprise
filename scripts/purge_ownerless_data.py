"""
Count, then optionally delete, rows that have no owning user (P2-14).

Such rows predate per-user ownership; no account purge can reach them.

    python scripts/purge_ownerless_data.py            # counts only
    python scripts/purge_ownerless_data.py --delete   # deletes them
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--delete", action="store_true", help="delete the rows (default: only count them)")
    args = parser.parse_args(argv)

    from src.persistence.user_data_purge import UserDataPurger
    from src.storage.artifact_store import LocalArtifactStore

    counts = UserDataPurger(LocalArtifactStore()).purge_ownerless(dry_run=not args.delete)
    verb = "deleted" if args.delete else "found"
    for table, count in counts.items():
        print(f"{table:22} {count:>8} ownerless rows {verb}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
