"""
AnalystGPT Enterprise - command-line entry point.

Runs the full pipeline (upload, governed cleaning, quality, analytics,
reporting, AI job) on a dataset from the local filesystem.

    python main.py --owner alice data/sales.csv
    python main.py --ownerless sample_data/customer_data.csv
    python main.py --help

Who owns a CLI run (P2-26)
--------------------------
CLI runs used to have no owner (user_id NULL): nobody could see them in the
UI or API, and only the ownerless purge could remove them. A run now belongs
to the account named with --owner, which must exist, be ACTIVE and hold the
pipeline-execute permission, the same rule POST /api/pipeline applies. An
ownerless run needs an explicit --ownerless. Such rows are visible to nobody,
and scripts/purge_ownerless_data.py removes them.

Exit status: 0 success, 1 pipeline failure, 2 usage or ownership error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.application.app import Application
from src.application.pipeline_result import PipelineResult
from src.core.constants import APP_VERSION
from src.core.logger import logger
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.context import UserContext
from src.identity.models import UserStatus
from src.identity.permissions import Permission

EXIT_OK, EXIT_FAILED, EXIT_USAGE = 0, 1, 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Run the AnalystGPT Enterprise pipeline on a local CSV, XLSX or JSON dataset.",
        epilog="Exit status: 0 success, 1 pipeline failure, 2 usage or ownership error.",
    )
    parser.add_argument("dataset", type=Path, help="path to the dataset file")
    owner = parser.add_mutually_exclusive_group(required=True)
    owner.add_argument(
        "--owner",
        metavar="USERNAME",
        help="account that owns the run (must be ACTIVE with pipeline-execute permission)",
    )
    owner.add_argument(
        "--ownerless",
        action="store_true",
        help="record the run with no owner (invisible in the UI and API; see scripts/purge_ownerless_data.py)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {APP_VERSION}")
    return parser


def resolve_owner(username: str) -> UserContext:
    """The owner's context, or ValueError naming why the account cannot own a run."""
    conn = ConnectionFactory.create_connection()
    conn.connect()
    try:
        SchemaManager(conn).initialize_schema()
        user = UserRepository(conn).get_by_username(username)
    finally:
        conn.disconnect()
    if user is None:
        raise ValueError(f"no account named {username!r}")
    if user.status != UserStatus.ACTIVE:
        raise ValueError(f"account {username!r} is {user.status.value}, not ACTIVE")
    context = UserContext.from_user(user)
    if not context.has_permission(Permission.PIPELINE_EXECUTE):
        raise ValueError(f"account {username!r} ({user.role.value}) may not execute the pipeline")
    return context


def report(result: PipelineResult) -> int:
    if not result.success:
        logger.error("Pipeline failed: %s", type(result.error).__name__ if result.error else "unknown error")
        print(f"Pipeline failed ({type(result.error).__name__ if result.error else 'unknown error'}).", file=sys.stderr)
        return EXIT_FAILED
    print(f"Pipeline succeeded in {result.execution_time or 0.0:.2f}s.")
    print(f"  pipeline run : {result.pipeline_run_id}")
    print(f"  dataset      : {result.dataset_version_id}")
    if result.report_id is not None:
        print(f"  report       : {result.report_id}")
    if result.output_path:
        print(f"  report file  : {result.output_path}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    dataset: Path = args.dataset
    if not dataset.is_file():
        parser.error(f"dataset not found: {dataset}")

    if args.ownerless:
        context = UserContext.anonymous()
        logger.warning("CLI run requested with --ownerless: the run will have no owner.")
    else:
        try:
            context = resolve_owner(args.owner)
        except ValueError as exc:
            parser.error(f"--owner: {exc}")

    application = Application()
    try:
        return report(application.run(str(dataset), user_context=context))
    finally:
        application.shutdown()


if __name__ == "__main__":
    sys.exit(main())
