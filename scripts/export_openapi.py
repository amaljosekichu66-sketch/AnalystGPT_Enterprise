"""
Write the live OpenAPI schema to docs/api/openapi.json.

    python scripts/export_openapi.py          # regenerate the committed contract
    python scripts/export_openapi.py --check  # exit 1 if it is out of date

tests/api/test_openapi_contract.py compares the committed file with the live
schema; run this after changing a route or a response model.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "docs" / "api" / "openapi.json"


def render() -> str:
    # Import-time side effects (database, artifact store) go to a throwaway tree.
    scratch = Path(tempfile.mkdtemp(prefix="openapi-export-"))
    os.environ.setdefault("APP_ENVIRONMENT", "development")
    os.environ.setdefault("SQLITE_DATABASE_PATH", str(scratch / "openapi.db"))
    os.environ.setdefault("REPORT_OUTPUT_DIRECTORY", str(scratch / "reports"))
    os.environ.setdefault("ARTIFACT_STORE_DIRECTORY", str(scratch / "artifacts"))
    os.environ.setdefault("LOG_LEVEL", "CRITICAL")
    sys.path.insert(0, str(REPO))

    from src.api.server import app

    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if docs/api/openapi.json is out of date")
    args = parser.parse_args(argv)

    schema = render()
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != schema:
            print("docs/api/openapi.json is out of date: run python scripts/export_openapi.py", file=sys.stderr)
            return 1
        return 0
    TARGET.write_bytes(schema.encode("utf-8"))
    print(f"wrote {TARGET.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
