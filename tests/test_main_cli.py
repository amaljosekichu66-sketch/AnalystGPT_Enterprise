"""
Regression tests for P2-26 (Sprint 15 readiness gate): the CLI entry point.

main.py had no argument handling: `--help` was ignored and the full pipeline
ran on a hardcoded dataset, runs had no owner, and nothing tested it.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

import main as cli
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.models import UserCreate, UserRole
from src.identity.user_service import UserService

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE = REPO_ROOT / "sample_data" / "customer_data.csv"


def _run(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update(
        SQLITE_DATABASE_PATH=str(tmp_path / "cli.db"),
        ARTIFACT_STORE_DIRECTORY=str(tmp_path / "artifacts"),
        REPORT_OUTPUT_DIRECTORY=str(tmp_path / "reports"),
        DATABASE_ENGINE="sqlite",
        LOG_TO_FILE="false",
        PYTHONPATH=str(REPO_ROOT),
    )
    return subprocess.run(
        [sys.executable, "main.py", *args], cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=120
    )


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_help_prints_usage_without_running(tmp_path: Path, flag: str) -> None:
    proc = _run(tmp_path, flag)

    assert proc.returncode == 0
    assert "usage: python main.py" in proc.stdout and "--owner" in proc.stdout
    assert not (tmp_path / "cli.db").exists()
    assert not (tmp_path / "artifacts").exists()


def test_no_arguments_is_a_usage_error(tmp_path: Path) -> None:
    proc = _run(tmp_path)

    assert proc.returncode == cli.EXIT_USAGE
    assert "usage:" in proc.stderr
    assert not (tmp_path / "cli.db").exists()


def test_owner_is_required_unless_ownerless_is_explicit(tmp_path: Path) -> None:
    proc = _run(tmp_path, str(SAMPLE))

    assert proc.returncode == cli.EXIT_USAGE
    assert "--owner" in proc.stderr and "--ownerless" in proc.stderr


def test_missing_dataset_is_a_usage_error(tmp_path: Path) -> None:
    proc = _run(tmp_path, "--ownerless", str(tmp_path / "nope.csv"))

    assert proc.returncode == cli.EXIT_USAGE
    assert "dataset not found" in proc.stderr


# ==========================================================
# Real runs (in-process, throwaway database)
# ==========================================================


@pytest.fixture
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db = tmp_path / "cli.db"
    monkeypatch.setattr(config, "SQLITE_DATABASE_PATH", db)
    monkeypatch.setattr(config, "ARTIFACT_STORE_DIRECTORY", tmp_path / "artifacts")
    monkeypatch.setattr(config, "REPORT_OUTPUT_DIRECTORY", tmp_path / "reports")
    (tmp_path / "reports").mkdir()
    return db


def _user(role: UserRole) -> tuple[int, str]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    name = f"cli_{role.value.lower()}_{uuid.uuid4().hex[:6]}"
    user = UserService(user_repository=UserRepository(conn)).register_user(
        UserCreate(username=name, email=f"{name}@example.com", password="Password123!", role=role)
    )
    if role != UserRole.VIEWER:  # self-registration yields VIEWER; promote as an admin would
        conn.get_connection().execute("UPDATE users SET role = ? WHERE id = ?", (role.value, user.id))
        conn.commit()
    conn.disconnect()
    return user.id, name


def _run_owners(db: Path) -> list:
    with sqlite3.connect(db) as raw:
        return [r[0] for r in raw.execute("SELECT user_id FROM pipeline_runs")]


def test_run_is_owned_by_the_named_analyst(isolated: Path, tmp_path: Path, capsys) -> None:
    user_id, name = _user(UserRole.ANALYST)

    assert cli.main(["--owner", name, str(SAMPLE)]) == cli.EXIT_OK

    assert _run_owners(isolated) == [user_id]
    out = capsys.readouterr().out
    assert "Pipeline succeeded" in out and "pipeline run" in out
    # One report file per run; the shared analystgpt_report.txt mirror is gone.
    assert not (tmp_path / "reports" / "analystgpt_report.txt").exists()


@pytest.mark.parametrize("role", [UserRole.VIEWER])
def test_an_account_without_pipeline_permission_cannot_own_a_run(isolated: Path, role: UserRole) -> None:
    _, name = _user(role)

    with pytest.raises(SystemExit) as exc:
        cli.main(["--owner", name, str(SAMPLE)])

    assert exc.value.code == cli.EXIT_USAGE
    assert not isolated.exists() or _run_owners(isolated) == []


def test_unknown_owner_is_refused(isolated: Path, capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["--owner", "nobody-" + uuid.uuid4().hex[:6], str(SAMPLE)])

    assert exc.value.code == cli.EXIT_USAGE
    assert "no account named" in capsys.readouterr().err


def test_ownerless_run_must_be_asked_for(isolated: Path) -> None:
    assert cli.main(["--ownerless", str(SAMPLE)]) == cli.EXIT_OK

    assert _run_owners(isolated) == [None]
