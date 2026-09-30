"""
Regression tests for test-suite persistence isolation.

Context
-------
Before this was fixed, a single `pytest -q` wrote into the developer's live
state: 11 new users, 19 AI jobs, 19 report rows, 20 pipeline runs and 38
dataset versions in `analystgpt.db`; 19 new files and 47 artifact directories
on disk; and it overwrote `reports/analystgpt_report.txt` and `.pdf`.

Only six test modules monkeypatched `SQLITE_DATABASE_PATH`. Everything else
used the real database, because the path was a hard-coded module constant with
no environment override.

These tests pin the three roots so the regression cannot return silently.
"""

from __future__ import annotations

from pathlib import Path

from src.core import config


def _is_under_project_root(path: Path) -> bool:
    try:
        Path(path).resolve().relative_to(config.PROJECT_ROOT.resolve())
    except ValueError:
        return False
    return True


# ==========================================================
# The three persistence roots
# ==========================================================


def test_database_is_not_the_development_database() -> None:
    """The live analystgpt.db must never be opened by a test run."""
    assert Path(config.SQLITE_DATABASE_PATH).resolve() != (config.PROJECT_ROOT / "analystgpt.db").resolve()
    assert not _is_under_project_root(config.SQLITE_DATABASE_PATH)


def test_report_output_is_not_the_repository_reports_directory() -> None:
    """Generated reports must not land in the working `reports/` directory."""
    assert Path(config.REPORT_OUTPUT_DIRECTORY).resolve() != (config.PROJECT_ROOT / "reports").resolve()
    assert not _is_under_project_root(config.REPORT_OUTPUT_DIRECTORY)


def test_artifact_store_is_not_the_repository_artifact_store() -> None:
    """Dataset artifacts must not accumulate in `data/artifacts/`."""
    assert Path(config.ARTIFACT_STORE_DIRECTORY).resolve() != (config.PROJECT_ROOT / "data" / "artifacts").resolve()
    assert not _is_under_project_root(config.ARTIFACT_STORE_DIRECTORY)


# ==========================================================
# The components that consume them
# ==========================================================


def test_connection_factory_opens_the_isolated_database() -> None:
    """`ConnectionFactory` reads the path through `config`, not a snapshot."""
    from src.database.connection_factory import ConnectionFactory

    connection = ConnectionFactory.create_connection()
    try:
        assert not _is_under_project_root(Path(connection._database_path))
    finally:
        connection.close()


def test_artifact_store_defaults_to_the_isolated_root() -> None:
    """A store constructed with no explicit base_dir must be redirected."""
    from src.storage.artifact_store import LocalArtifactStore

    store = LocalArtifactStore()

    assert not _is_under_project_root(store.base_dir)


def test_frontend_export_writes_no_file(tmp_path: Path) -> None:
    """
    The frontend used to write every export to a shared filename under the
    report directory (first the repository's own `reports/`, which a test run
    clobbered; later REPORT_OUTPUT_DIRECTORY). Exports now stay in memory (L16).
    """
    from unittest.mock import MagicMock, patch

    from src.frontend.services import report_service

    real_report = config.PROJECT_ROOT / "reports" / "analystgpt_report.txt"
    before = real_report.read_bytes() if real_report.exists() else None
    report_dir = Path(config.REPORT_OUTPUT_DIRECTORY)
    files_before = set(report_dir.rglob("*")) if report_dir.exists() else set()

    client = MagicMock()
    client.__enter__.return_value.export_text_report.return_value = b"isolated export"
    with patch.object(report_service, "APIClient", return_value=client):
        result = report_service.export_text_report()

    assert result["success"] is True and result["data"] == b"isolated export"
    assert "path" not in result
    assert (set(report_dir.rglob("*")) if report_dir.exists() else set()) == files_before
    after = real_report.read_bytes() if real_report.exists() else None
    assert after == before
