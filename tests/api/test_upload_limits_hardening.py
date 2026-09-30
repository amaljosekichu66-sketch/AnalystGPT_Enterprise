"""
Regression tests for the upload findings of the 2026-09-29 audit.

- M3: with no Content-Length the size pre-check was skipped, request.form()
  spooled the whole body before a byte was counted, accepted uploads were
  held in memory twice, and all of it happened before the job slot.
- M4: the zip-bomb check ran only for the `.xlsx` suffix; a 331:1 bomb
  renamed to `.xls` was parsed by openpyxl.
- I5: defusedxml was missing from the production lock.
- L14 (body limit part): JSON endpoints had no body limit.
"""

from __future__ import annotations

import io
import uuid
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.application_dependency import get_application
from src.api.server import app
from src.core import config
from src.core.exceptions import TooManyConcurrentJobsError
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService
from src.upload import upload_policy

_PASSWORD = "Password123!"
REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def headers() -> dict[str, str]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    name = f"m3_{uuid.uuid4().hex[:6]}"
    service.register_user(
        UserCreate(username=name, email=f"{name}@example.com", password=_PASSWORD, role=UserRole.ANALYST)
    )
    _, token, _ = service.login(UserLogin(username=name, password=_PASSWORD))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app)


def _zip_bomb(name: str = "xl/worksheets/sheet1.xml", size: int = 5 * 1024 * 1024) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, b"0" * size)
    return buffer.getvalue()


class TestBodyLimit:
    def test_chunked_upload_without_content_length_is_refused(self, client: TestClient, headers) -> None:
        def body():
            yield b'--x\r\nContent-Disposition: form-data; name="file"; filename="a.csv"\r\n\r\n'
            yield b"a,b\n1,2\n"
            yield b"\r\n--x--\r\n"

        res = client.post(
            "/api/datasets",
            content=body(),
            headers={**headers, "Content-Type": "multipart/form-data; boundary=x"},
        )
        assert res.status_code == 411

    def test_upload_over_the_limit_is_413(self, client: TestClient, headers, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_FILE_SIZE_MB", 1)
        res = client.post(
            "/api/datasets",
            headers=headers,
            files={"file": ("big.csv", b"a,b\n" + b"1,2\n" * 400_000, "text/csv")},
        )
        assert res.status_code == 413

    def test_json_body_over_the_limit_is_413(self, client: TestClient) -> None:
        res = client.post("/api/auth/login", content=b'{"username": "' + b"a" * (1100 * 1024) + b'"}')
        assert res.status_code == 413

    def test_chunked_json_body_over_the_limit_is_413(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_REQUEST_BODY_KB", 4)

        def body():
            yield b'{"username": "'
            for _ in range(10):
                yield b"a" * 1024
            yield b'", "password": "x"}'

        res = client.post("/api/auth/login", content=body(), headers={"Content-Type": "application/json"})
        assert res.status_code == 413

    def test_small_json_bodies_still_work(self, client: TestClient) -> None:
        res = client.post("/api/auth/login", json={"username": "nobody", "password": "whatever"})
        assert res.status_code == 401


def test_job_slot_is_taken_before_the_body_is_read(client: TestClient, headers, monkeypatch) -> None:
    application = get_application()
    reads: list[bool] = []

    def refuse(_context):
        raise TooManyConcurrentJobsError("busy")

    monkeypatch.setattr(application, "job_slot", refuse)
    monkeypatch.setattr("src.api.routes.datasets.read_bounded", lambda stream: reads.append(True) or b"")

    res = client.post("/api/datasets", headers=headers, files={"file": ("a.csv", b"a,b\n1,2\n", "text/csv")})

    assert res.status_code == 429
    assert reads == []


class TestReadBounded:
    def test_reads_once_into_one_buffer(self, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_FILE_SIZE_MB", 1)
        calls: list[int] = []

        class Stream(io.BytesIO):
            def read(self, size=-1):
                calls.append(size)
                return super().read(size)

        assert upload_policy.read_bounded(Stream(b"abc")) == b"abc"
        assert calls == [1024 * 1024 + 1]

    def test_oversize_stream_is_refused(self, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_FILE_SIZE_MB", 1)
        with pytest.raises(upload_policy.UploadTooLargeError):
            upload_policy.read_bounded(io.BytesIO(b"x" * (1024 * 1024 + 1)))


class TestArchiveCheckByContent:
    def test_xls_is_no_longer_accepted(self, client: TestClient, headers) -> None:
        res = client.post(
            "/api/datasets", headers=headers, files={"file": ("bomb.xls", _zip_bomb(), "application/vnd.ms-excel")}
        )
        assert res.status_code == 415

    @pytest.mark.parametrize("filename", ["bomb.csv", "bomb.json", "bomb.xlsx"])
    def test_zip_content_is_checked_whatever_its_name(self, client: TestClient, headers, filename: str) -> None:
        res = client.post("/api/datasets", headers=headers, files={"file": (filename, _zip_bomb(), "text/csv")})
        assert res.status_code == 413

    def test_check_runs_on_signature(self) -> None:
        with pytest.raises(upload_policy.UploadTooLargeError):
            upload_policy.check_archive_safety(_zip_bomb(), "renamed.csv")
        upload_policy.check_archive_safety(b"a,b\n1,2\n", "plain.csv")

    def test_excel_engine_is_pinned(self, monkeypatch) -> None:
        from src.upload import excel_reader

        seen: dict = {}
        monkeypatch.setattr(excel_reader.pd, "read_excel", lambda path, **kw: seen.update(kw) or None)
        excel_reader.ExcelReader().read("x.xlsx")
        assert seen.get("engine") == "openpyxl"


def test_defusedxml_is_in_the_production_lock() -> None:
    lock = (REPO / "requirements.lock").read_text(encoding="utf-8")
    assert "\ndefusedxml==" in lock
    assert "defusedxml" in (REPO / "requirements.txt").read_text(encoding="utf-8")
