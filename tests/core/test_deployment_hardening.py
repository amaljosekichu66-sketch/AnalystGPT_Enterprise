"""
Regression tests for the deployment and supply-chain findings:

- SEC-13: compose fell back to POSTGRES_PASSWORD=postgres.
- SEC-14: no lock file / hashes, dev tools in the runtime image, mutable base tag.
- SEC-17: /docs, /redoc and /openapi.json public in production; API bound to
  all interfaces by default and published on all host interfaces by compose.
- SEC-22: CI had no security scanning, tag-pinned actions, no permissions.
- SEC-23: setuptools 65.5.0 (known advisories) in the toolchain.
- SEC-24: committed test data used real email providers' domains.
"""

from __future__ import annotations

import csv
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]

DEV_ONLY = {"pytest", "pytest-cov", "black", "flake8", "isort", "mypy", "pre-commit", "bandit", "pip-audit", "psutil"}


def _names(requirements: str) -> set[str]:
    names = set()
    for line in requirements.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-", "--")):
            continue
        names.add(re.split(r"[\[<>=!~ ;]", line, maxsplit=1)[0].lower().replace("_", "-"))
    return names


def _compose() -> dict:
    return yaml.safe_load((REPO / "docker-compose.yml").read_text(encoding="utf-8"))


# ==========================================================
# SEC-13
# ==========================================================


def test_compose_requires_the_database_password() -> None:
    compose = _compose()
    for service in ("postgres", "api"):
        value = compose["services"][service]["environment"]["POSTGRES_PASSWORD"]
        assert value.startswith("${POSTGRES_PASSWORD:?"), (service, value)
    assert "POSTGRES_PASSWORD:-" not in (REPO / "docker-compose.yml").read_text(encoding="utf-8")


# ==========================================================
# SEC-14 / SEC-23
# ==========================================================


class TestSupplyChain:
    def test_runtime_requirements_exclude_dev_tools(self) -> None:
        runtime = _names((REPO / "requirements.txt").read_text(encoding="utf-8"))
        assert not (runtime & DEV_ONLY), runtime & DEV_ONLY

    def test_dev_requirements_extend_runtime(self) -> None:
        dev = (REPO / "requirements-dev.txt").read_text(encoding="utf-8")
        assert "-r requirements.txt" in dev
        assert DEV_ONLY <= _names(dev)

    def test_lock_pins_every_package_by_hash(self) -> None:
        lock = (REPO / "requirements.lock").read_text(encoding="utf-8")
        entries = re.findall(
            r"^([A-Za-z0-9_.\-]+)==([^\s\\]+)((?:\s*\\\s*\n\s*--hash=sha256:[0-9a-f]{64})+)", lock, re.M
        )
        declared = re.findall(r"^[A-Za-z0-9_.\-]+==", lock, re.M)

        assert entries and len(entries) == len(declared), "every pinned package must carry --hash lines"
        pinned = {name.lower().replace("_", "-") for name, _, _ in entries}
        assert not (pinned & DEV_ONLY), pinned & DEV_ONLY
        assert _names((REPO / "requirements.txt").read_text(encoding="utf-8")) <= pinned

    def test_lock_setuptools_is_past_the_advisories(self) -> None:
        lock = (REPO / "requirements.lock").read_text(encoding="utf-8")
        version = re.search(r"^setuptools==([\d.]+)", lock, re.M)
        assert version, "setuptools must be pinned in the lock"
        assert tuple(int(p) for p in version.group(1).split(".")[:2]) >= (83, 0)

    def test_dockerfile_uses_digest_and_hash_checked_install(self) -> None:
        dockerfile = (REPO / "Dockerfile").read_text(encoding="utf-8")
        froms = re.findall(r"^FROM\s+(\S+)", dockerfile, re.M)
        external = [f for f in froms if ":" in f or "@" in f]
        assert external and all(re.search(r"@sha256:[0-9a-f]{64}$", f) for f in external), external
        assert "--require-hashes -r requirements.lock" in dockerfile
        assert not re.search(r"^\s*(RUN|COPY).*requirements-dev", dockerfile, re.M)


# ==========================================================
# SEC-17
# ==========================================================


def _run_api(code: str, tmp_path: Path, **env: str) -> subprocess.CompletedProcess:
    child = {k: v for k, v in os.environ.items() if k not in ("APP_ENVIRONMENT", "API_DOCS_ENABLED", "AUTH_SECRET_KEY")}
    child.update(
        AUTH_SECRET_KEY=secrets.token_urlsafe(48),
        SQLITE_DATABASE_PATH=str(tmp_path / "x.db"),
        ARTIFACT_STORE_DIRECTORY=str(tmp_path / "a"),
        REPORT_OUTPUT_DIRECTORY=str(tmp_path / "r"),
        LOG_LEVEL="CRITICAL",
        LOG_TO_FILE="false",
        OLLAMA_HOST="http://127.0.0.1:9",
        PYTHONPATH=str(REPO),
        **env,
    )
    return subprocess.run(
        [sys.executable, "-c", code], cwd=REPO, env=child, capture_output=True, text=True, timeout=120
    )


_PROBE = (
    "import json; from fastapi.testclient import TestClient; from src.api.server import app; "
    "c = TestClient(app); print(json.dumps({p: c.get(p).status_code for p in ('/docs', '/redoc', '/openapi.json')}))"
)


class TestExposure:
    def test_docs_are_off_in_production(self, tmp_path: Path) -> None:
        proc = _run_api(_PROBE, tmp_path, APP_ENVIRONMENT="production")
        assert proc.returncode == 0, proc.stderr[-1500:]
        assert json.loads(proc.stdout.strip().splitlines()[-1]) == {"/docs": 404, "/redoc": 404, "/openapi.json": 404}

    def test_docs_can_be_enabled_explicitly(self, tmp_path: Path) -> None:
        proc = _run_api(_PROBE, tmp_path, APP_ENVIRONMENT="production", API_DOCS_ENABLED="true")
        assert json.loads(proc.stdout.strip().splitlines()[-1])["/openapi.json"] == 200

    def test_docs_on_in_development(self, tmp_path: Path) -> None:
        proc = _run_api(_PROBE, tmp_path, APP_ENVIRONMENT="development")
        assert json.loads(proc.stdout.strip().splitlines()[-1])["/docs"] == 200

    def test_default_bind_is_loopback(self, monkeypatch) -> None:
        import importlib

        from src.core import config

        monkeypatch.delenv("API_HOST", raising=False)
        try:
            assert importlib.reload(config).API_HOST == "127.0.0.1"
        finally:
            monkeypatch.undo()
            importlib.reload(config)

    @pytest.mark.parametrize("service", ["api", "frontend"])
    def test_compose_publishes_on_loopback_by_default(self, service: str) -> None:
        (port,) = _compose()["services"][service]["ports"]
        assert port.startswith("${") and ":-127.0.0.1}:" in port, port


# ==========================================================
# SEC-22
# ==========================================================


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load((REPO / ".github/workflows/ci.yml").read_text(encoding="utf-8"))


class TestCI:
    def test_least_privilege_permissions(self, workflow) -> None:
        assert workflow["permissions"] == {"contents": "read"}

    def test_every_action_is_pinned_to_a_commit(self, workflow) -> None:
        uses = [step["uses"] for job in workflow["jobs"].values() for step in job["steps"] if "uses" in step]
        assert uses and all(re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", u) for u in uses), uses

    def test_security_job_runs_all_scanners(self, workflow) -> None:
        script = " ".join(step.get("run", "") for step in workflow["jobs"]["security"]["steps"])
        assert "gitleaks" in script and "@sha256:" in script
        assert "pip-audit" in script and "bandit" in script
        assert "security" in workflow["jobs"]["test"]["needs"]


# ==========================================================
# SEC-24
# ==========================================================

_RESERVED = re.compile(r"@(?:[a-z0-9-]+\.)*(?:example\.(?:com|org|net)|test|invalid|localhost)$", re.I)


@pytest.mark.parametrize(
    "path",
    sorted(
        str(p.relative_to(REPO)) for p in [*REPO.glob("performance/datasets/*.csv"), *REPO.glob("sample_data/*.csv")]
    ),
)
def test_committed_datasets_use_reserved_email_domains(path: str) -> None:
    with open(REPO / path, newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            for value in row:
                if "@" in value and "." in value.split("@")[-1]:
                    assert _RESERVED.search(value.strip()), f"{path}: {value}"
