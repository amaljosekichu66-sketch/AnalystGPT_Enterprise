"""
Regression tests for L11, L19 and I12 (audit 2026-09-29).

- L11: no TLS options or connect timeout for PostgreSQL; plain HTTP to any
  Ollama host, with no authentication.
- L19: postgres image pinned by tag only; the API connected as the superuser.
- I12: CI had no container image scan.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from src.core import config
from src.database import postgresql_connection
from src.llm.ollama_client import check_ollama_transport

REPO = Path(__file__).resolve().parents[2]
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}")


class TestOllamaTransport:
    @pytest.mark.parametrize(
        "host",
        [
            "http://localhost:11434",
            "http://127.0.0.1:11434",
            "http://host.docker.internal:11434",
            "https://llm.example.com",
        ],
    )
    def test_local_or_https_is_accepted(self, host: str) -> None:
        check_ollama_transport(host, allow_insecure=False)

    @pytest.mark.parametrize("host", ["http://10.0.0.8:11434", "http://llm.example.com", "llm.example.com:11434"])
    def test_remote_plain_http_is_refused(self, host: str) -> None:
        with pytest.raises(RuntimeError, match="plain-HTTP"):
            check_ollama_transport(host, allow_insecure=False)

    def test_refusal_can_be_acknowledged(self) -> None:
        check_ollama_transport("http://10.0.0.8:11434", allow_insecure=True)


def test_postgres_connection_passes_tls_and_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict = {}
    monkeypatch.setattr(postgresql_connection.psycopg, "connect", lambda **kw: seen.update(kw) or object())
    monkeypatch.setattr(config, "POSTGRES_SSLMODE", "verify-full")
    monkeypatch.setattr(config, "POSTGRES_SSLROOTCERT", "/etc/ssl/db-ca.pem")

    postgresql_connection.PostgreSQLConnection("db", 5432, "analystgpt", "app", "pw").connect()

    assert seen["sslmode"] == "verify-full"
    assert seen["sslrootcert"] == "/etc/ssl/db-ca.pem"
    assert seen["connect_timeout"] == config.POSTGRES_CONNECT_TIMEOUT


@pytest.fixture(scope="module")
def compose() -> dict:
    return yaml.safe_load((REPO / "docker-compose.yml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def workflow() -> str:
    return (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")


class TestCompose:

    def test_postgres_image_is_pinned_by_digest(self, compose) -> None:
        assert DIGEST.search(compose["services"]["postgres"]["image"])

    def test_api_connects_as_the_application_role(self, compose) -> None:
        env = compose["services"]["api"]["environment"]
        assert "APP_DB_USER" in env["POSTGRES_USER"] and "APP_DB_PASSWORD" in env["POSTGRES_PASSWORD"]

    def test_role_script_is_mounted_and_least_privilege(self, compose) -> None:
        volumes = " ".join(compose["services"]["postgres"]["volumes"])
        assert "init-app-role.sh:/docker-entrypoint-initdb.d/" in volumes
        script = (REPO / "docker" / "postgres" / "init-app-role.sh").read_bytes()
        assert b"\r\n" not in script
        text = script.decode("utf-8")
        assert "NOSUPERUSER NOCREATEDB NOCREATEROLE" in text
        assert "%L" in text and ":'app_password'" in text  # the password is quoted by psql, not the shell

    def test_shell_scripts_are_checked_out_with_lf(self) -> None:
        assert "*.sh text eol=lf" in (REPO / ".gitattributes").read_text(encoding="utf-8")


class TestCI:

    def test_images_are_scanned_with_a_pinned_trivy(self, workflow: str) -> None:
        assert re.search(r"aquasec/trivy@sha256:[0-9a-f]{64}", workflow)
        assert "--exit-code 1" in workflow and "analystgpt-api:ci" in workflow

    def test_compose_jobs_provide_the_app_db_password(self, workflow: str) -> None:
        assert workflow.count('echo "APP_DB_PASSWORD=$app" >> "$GITHUB_ENV"') == 2
