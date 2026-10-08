"""
Regression tests for B-05 / SEC-03 and SEC-04: the token signing key.

- B-05: Docker Compose set no APP_ENVIRONMENT, which defaulted to
  "development", so the stack signed tokens with the key published in this
  repository. Anyone could forge an ADMIN token.
- SEC-04: `AUTH_SECRET_KEY=` (empty, exactly as `.env.example` ships it) was
  accepted in production, because the guard only compared against the
  published default. An empty HMAC key is just as forgeable.

The key is now validated where it is used: the API refuses to start, and a
TokenService cannot be built from an unsafe configuration. The Streamlit
frontend imports `src.core.config` too but never signs tokens, so config
import itself must not fail.
"""

from __future__ import annotations

import importlib
import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from src.core import config

REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_KEY = "k" * config.AUTH_SECRET_KEY_MIN_LENGTH
SHORT_KEY = "s" * (config.AUTH_SECRET_KEY_MIN_LENGTH - 1)


# ==========================================================
# Pure validation
# ==========================================================


class TestValidateAuthSecretKey:
    @pytest.mark.parametrize("environment", ["production", "staging", "prod", "test"])
    @pytest.mark.parametrize(
        "raw, reason",
        [
            (None, "missing"),
            ("", "empty"),
            ("   ", "empty"),
            (SHORT_KEY, "shorter than"),
            (config.INSECURE_DEFAULT_AUTH_SECRET_KEY, "built-in development key"),
        ],
    )
    def test_unsafe_keys_are_refused_outside_development(self, environment: str, raw, reason: str) -> None:
        with pytest.raises(RuntimeError, match=reason):
            config.validate_auth_secret_key(environment, raw)

    def test_minimum_length_is_256_bits(self) -> None:
        assert config.AUTH_SECRET_KEY_MIN_LENGTH == 32

    def test_valid_production_key_is_accepted(self) -> None:
        assert config.validate_auth_secret_key("production", VALID_KEY) == VALID_KEY
        assert config.validate_auth_secret_key("production", f"  {VALID_KEY}\n") == VALID_KEY

    def test_multibyte_key_length_is_measured_in_bytes(self) -> None:
        eleven_chars_33_bytes = "€" * 11
        assert config.validate_auth_secret_key("production", eleven_chars_33_bytes) == eleven_chars_33_bytes

    @pytest.mark.parametrize("raw", [None, "", "  "])
    def test_explicit_development_falls_back_to_builtin_key(self, raw) -> None:
        assert config.validate_auth_secret_key("development", raw) == config.INSECURE_DEFAULT_AUTH_SECRET_KEY

    def test_explicit_development_honours_a_provided_key(self) -> None:
        assert config.validate_auth_secret_key("development", SHORT_KEY) == SHORT_KEY

    def test_error_never_echoes_the_key(self) -> None:
        with pytest.raises(RuntimeError) as exc:
            config.validate_auth_secret_key("production", SHORT_KEY)
        assert SHORT_KEY not in str(exc.value)


# ==========================================================
# Module configuration
# ==========================================================


@pytest.fixture
def reload_config(monkeypatch: pytest.MonkeyPatch):
    def _reload(**env: str | None):
        for name, value in env.items():
            if value is None:
                monkeypatch.delenv(name, raising=False)
            else:
                monkeypatch.setenv(name, value)
        return importlib.reload(config)

    yield _reload
    monkeypatch.undo()
    importlib.reload(config)


def test_unset_environment_fails_closed_to_production(reload_config) -> None:
    reloaded = reload_config(APP_ENVIRONMENT=None, AUTH_SECRET_KEY=None)

    assert reloaded.APP_ENVIRONMENT == "production"
    assert reloaded.IS_DEVELOPMENT is False
    with pytest.raises(RuntimeError, match="missing"):
        reloaded.require_auth_secret_key()


@pytest.mark.parametrize("raw", [None, "", SHORT_KEY, config.INSECURE_DEFAULT_AUTH_SECRET_KEY])
def test_production_config_import_does_not_raise_but_key_is_unusable(reload_config, raw) -> None:
    """Import stays safe for the frontend; every signing path refuses."""
    from src.identity.token_service import TokenService

    reloaded = reload_config(APP_ENVIRONMENT="production", AUTH_SECRET_KEY=raw)

    assert reloaded.AUTH_SECRET_KEY == ""
    assert reloaded.AUTH_SECRET_KEY != config.INSECURE_DEFAULT_AUTH_SECRET_KEY
    with pytest.raises(RuntimeError, match="AUTH_SECRET_KEY"):
        reloaded.require_auth_secret_key()
    with pytest.raises(RuntimeError, match="AUTH_SECRET_KEY"):
        TokenService()


def test_valid_production_key_is_used(reload_config) -> None:
    reloaded = reload_config(APP_ENVIRONMENT="production", AUTH_SECRET_KEY=VALID_KEY)

    assert reloaded.require_auth_secret_key() == VALID_KEY
    assert reloaded.IS_DEVELOPMENT is False


def test_explicit_development_mode_uses_builtin_key(reload_config) -> None:
    reloaded = reload_config(APP_ENVIRONMENT="development", AUTH_SECRET_KEY=None)

    assert reloaded.require_auth_secret_key() == config.INSECURE_DEFAULT_AUTH_SECRET_KEY


# ==========================================================
# Real process startup
# ==========================================================


def _run(code: str, tmp_path: Path, **env: str | None) -> subprocess.CompletedProcess:
    child_env = {k: v for k, v in os.environ.items() if k not in ("APP_ENVIRONMENT", "AUTH_SECRET_KEY")}
    child_env.update(
        SQLITE_DATABASE_PATH=str(tmp_path / "startup.db"),
        ARTIFACT_STORE_DIRECTORY=str(tmp_path / "artifacts"),
        REPORT_OUTPUT_DIRECTORY=str(tmp_path / "reports"),
        DATABASE_ENGINE="sqlite",
        LOG_TO_FILE="false",
        LOG_LEVEL="ERROR",
        OLLAMA_HOST="http://127.0.0.1:9",
        PYTHONPATH=str(REPO_ROOT),
    )
    for name, value in env.items():
        if value is None:
            child_env.pop(name, None)
        else:
            child_env[name] = value
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=child_env,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.parametrize(
    "raw",
    [None, "", "   ", SHORT_KEY, config.INSECURE_DEFAULT_AUTH_SECRET_KEY],
    ids=["missing", "empty", "blank", "short", "published-default"],
)
def test_api_refuses_to_start_in_production_with_unsafe_key(tmp_path: Path, raw) -> None:
    proc = _run("import src.api.server", tmp_path, APP_ENVIRONMENT="production", AUTH_SECRET_KEY=raw)

    assert proc.returncode != 0
    assert "AUTH_SECRET_KEY" in proc.stderr
    if raw and raw.strip():
        assert raw not in proc.stderr + proc.stdout


def test_api_starts_in_production_with_valid_key(tmp_path: Path) -> None:
    key = secrets.token_urlsafe(48)
    proc = _run(
        "import src.api.server; print('API_STARTED')", tmp_path, APP_ENVIRONMENT="production", AUTH_SECRET_KEY=key
    )

    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "API_STARTED" in proc.stdout
    assert key not in proc.stderr + proc.stdout


def test_api_refuses_unset_environment_without_key(tmp_path: Path) -> None:
    proc = _run("import src.api.server", tmp_path, APP_ENVIRONMENT=None, AUTH_SECRET_KEY=None)

    assert proc.returncode != 0
    assert "APP_ENVIRONMENT='production'" in proc.stderr


def test_frontend_imports_in_production_without_the_key(tmp_path: Path) -> None:
    code = (
        "import src.frontend.services.api_client, src.frontend.services.dashboard_service, "
        "src.frontend.services.upload_service; print('FRONTEND_OK')"
    )
    proc = _run(code, tmp_path, APP_ENVIRONMENT="production", AUTH_SECRET_KEY=None)

    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "FRONTEND_OK" in proc.stdout


# ==========================================================
# Forged-token PoC
# ==========================================================


def test_token_forged_with_published_key_is_rejected_under_production_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The original PoC: sign an ADMIN token with the key published in the
    repository. Under a private production key the API rejects it.
    """
    from src.api.dependencies.auth_dependencies import set_user_service_instance
    from src.api.server import app
    from src.identity.in_memory_user_repository import InMemoryUserRepository
    from src.identity.models import UserCreate, UserLogin, UserRole
    from src.identity.token_service import TokenService
    from src.identity.user_service import UserService

    monkeypatch.setattr("src.core.config.AUTH_ALLOW_HEADER_IDENTITY", False)
    production_service = UserService(
        user_repository=InMemoryUserRepository(),
        token_service=TokenService(secret_key=secrets.token_urlsafe(48)),
    )
    admin = production_service.register_user(
        UserCreate(username="real_admin", email="real_admin@example.com", password="Password123!", role=UserRole.ADMIN)
    )
    forged = TokenService(secret_key=config.INSECURE_DEFAULT_AUTH_SECRET_KEY).create_access_token(admin)

    set_user_service_instance(production_service)
    try:
        client = TestClient(app)
        forged_res = client.get("/api/admin/users", headers={"Authorization": f"Bearer {forged}"})
        _, genuine, _ = production_service.login(UserLogin(username="real_admin", password="Password123!"))
        genuine_res = client.get("/api/admin/users", headers={"Authorization": f"Bearer {genuine}"})
    finally:
        set_user_service_instance(None)

    assert forged_res.status_code == 401
    assert genuine_res.status_code == 200


# ==========================================================
# Deployment artifacts
# ==========================================================


def _compose() -> dict:
    return yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8"))


def test_compose_runs_api_in_production_and_requires_the_key() -> None:
    api_env = _compose()["services"]["api"]["environment"]

    assert api_env["APP_ENVIRONMENT"] == "production"
    # `${VAR:?message}` makes `docker compose` fail when unset or empty;
    # `${VAR:-default}` or `${VAR}` would silently fall back.
    assert api_env["AUTH_SECRET_KEY"].startswith("${AUTH_SECRET_KEY:?")
    assert config.INSECURE_DEFAULT_AUTH_SECRET_KEY not in (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")


def test_compose_does_not_hand_the_key_to_the_frontend() -> None:
    frontend_env = _compose()["services"]["frontend"]["environment"]

    assert frontend_env["APP_ENVIRONMENT"] == "production"
    assert "AUTH_SECRET_KEY" not in frontend_env


def test_env_example_ships_no_key_and_documents_the_rules() -> None:
    content = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "\nAPP_ENVIRONMENT=production\n" in content
    assert "\nAUTH_SECRET_KEY=CHANGE_ME" in content
    assert "32 bytes" in content
    assert "REFUSES TO START" in content
    assert "treats itself as 'production'" in content


# ==========================================================
# P2-18: the templates
# ==========================================================


def _template_env(name: str) -> dict[str, str]:
    from dotenv import dotenv_values

    return {k: v for k, v in dotenv_values(REPO_ROOT / name).items() if v is not None}


@pytest.mark.parametrize("environment", ["production", "development", "staging"])
def test_the_template_placeholder_is_refused_everywhere(environment: str) -> None:
    placeholder = _template_env(".env.example")["AUTH_SECRET_KEY"]
    with pytest.raises(RuntimeError, match="placeholder"):
        config.validate_auth_secret_key(environment, placeholder)


def test_a_copied_env_example_cannot_start_the_api(tmp_path: Path) -> None:
    template = _template_env(".env.example")
    proc = _run(
        "import src.api.server",
        tmp_path,
        APP_ENVIRONMENT=template["APP_ENVIRONMENT"],
        AUTH_SECRET_KEY=template["AUTH_SECRET_KEY"],
    )

    assert template["APP_ENVIRONMENT"] == "production"
    assert proc.returncode != 0
    assert "placeholder" in proc.stderr


def test_the_development_template_starts_on_loopback(tmp_path: Path) -> None:
    template = _template_env(".env.development.example")
    proc = _run(
        "import src.api.server; print('API_STARTED')",
        tmp_path,
        APP_ENVIRONMENT=template["APP_ENVIRONMENT"],
        AUTH_SECRET_KEY=template["AUTH_SECRET_KEY"],
        API_HOST=template["API_HOST"],
    )

    assert template["APP_ENVIRONMENT"] == "development"
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "API_STARTED" in proc.stdout
