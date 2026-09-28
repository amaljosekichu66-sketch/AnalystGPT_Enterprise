"""
Regression tests for SEC-10: unbounded resource consumption on upload / run.

Reproduced before the fix: a 94 KB .xlsx expanding 406:1 to 37 MB was
accepted after ~57 s of parsing; a CSV of 1,000,001 rows was accepted; six
simultaneous pipeline runs by one user all ran.
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
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.context import UserContext
from src.identity.models import UserCreate, UserLogin, UserRole, UserStatus
from src.identity.user_service import UserService
from tests.fixtures.datasets import upload_dataset

SAMPLE_CSV = Path("sample_data/customer_data.csv")


def _xlsx(sheet_xml: str) -> bytes:
    parts = {
        "[Content_Types].xml": (
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
        ),
        "_rels/.rels": (
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
            'officeDocument" Target="xl/workbook.xml"/></Relationships>'
        ),
        "xl/workbook.xml": (
            '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
            '<sheet name="S" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
            'worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
        ),
        "xl/worksheets/sheet1.xml": sheet_xml,
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in parts.items():
            z.writestr(name, data)
    return buf.getvalue()


def _bomb(rows: int = 400_000) -> bytes:
    body = "<row><c><v>1</v></c></row>" * rows
    return _xlsx(
        '<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{body}</sheetData></worksheet>"
    )


@pytest.fixture(scope="module")
def users() -> dict[str, dict]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    out = {}
    for key in ("a", "b"):
        name = f"sec10_{key}_{uuid.uuid4().hex[:6]}"
        user = service.register_user(
            UserCreate(username=name, email=f"{name}@example.com", password="Str0ng-Passw0rd!", role=UserRole.ANALYST)
        )
        _, token, _ = service.login(UserLogin(username=name, password="Str0ng-Passw0rd!"))
        out[key] = {
            "headers": {"Authorization": f"Bearer {token}"},
            "context": UserContext(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=UserRole.ANALYST,
                status=UserStatus.ACTIVE,
                is_authenticated=True,
            ),
        }
    return out


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app)


def _raw_artifacts() -> set[Path]:
    return {p for p in get_application().artifact_store.raw_dir.rglob("*") if p.is_file()}


class TestArchiveSafety:
    def test_zip_bomb_workbook_rejected_before_parsing(self, client, users) -> None:
        bomb = _bomb()
        before = _raw_artifacts()

        res = client.post("/api/datasets", files={"file": ("bomb.xlsx", bomb)}, headers=users["a"]["headers"])

        assert res.status_code == 413
        assert "compression ratio" in res.json()["error"]
        assert _raw_artifacts() == before

    def test_expanded_size_cap(self, client, users, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_XLSX_COMPRESSION_RATIO", 10**9)
        monkeypatch.setattr(config, "MAX_XLSX_UNCOMPRESSED_MB", 1)

        res = client.post("/api/datasets", files={"file": ("big.xlsx", _bomb())}, headers=users["a"]["headers"])

        assert res.status_code == 413
        assert "expands beyond" in res.json()["error"]

    def test_not_a_zip_is_rejected(self, client, users) -> None:
        before = _raw_artifacts()

        res = client.post("/api/datasets", files={"file": ("fake.xlsx", b"a,b\n1,2\n")}, headers=users["a"]["headers"])

        assert res.status_code == 422
        assert _raw_artifacts() == before

    def test_real_workbook_still_accepted(self, client, users) -> None:
        res = client.post(
            "/api/datasets",
            files={"file": ("employees.xlsx", Path("sample_data/employees.xlsx").read_bytes())},
            headers=users["a"]["headers"],
        )
        assert res.status_code == 201, res.text


class TestShapeLimits:
    def test_row_limit(self, client, users, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_UPLOAD_ROWS", 100)
        before = _raw_artifacts()

        res = client.post(
            "/api/datasets",
            files={"file": ("rows.csv", ("v\n" + "1\n" * 101).encode())},
            headers=users["a"]["headers"],
        )

        assert res.status_code == 413
        assert _raw_artifacts() == before
        at_limit = client.post(
            "/api/datasets",
            files={"file": ("rows.csv", ("v\n" + "1\n" * 100).encode())},
            headers=users["a"]["headers"],
        )
        assert at_limit.status_code == 201

    def test_column_limit(self, client, users, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_UPLOAD_COLUMNS", 5)
        header = ",".join(f"c{i}" for i in range(6))

        res = client.post(
            "/api/datasets",
            files={"file": ("wide.csv", f"{header}\n{','.join('1' * 6)}\n".encode())},
            headers=users["a"]["headers"],
        )

        assert res.status_code == 413


class TestPerUserJobCap:
    def test_extra_jobs_are_refused_while_the_cap_is_held(self, client, users, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_CONCURRENT_JOBS_PER_USER", 1)
        dataset_id = upload_dataset(client, SAMPLE_CSV, users["a"]["headers"])
        application = get_application()

        with application._job_slot(users["a"]["context"]):
            run = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=users["a"]["headers"])
            upload = client.post(
                "/api/datasets", files={"file": ("d.csv", SAMPLE_CSV.read_bytes())}, headers=users["a"]["headers"]
            )
            other_user = client.post(
                "/api/datasets", files={"file": ("d.csv", SAMPLE_CSV.read_bytes())}, headers=users["b"]["headers"]
            )

        assert run.status_code == 429 and run.headers["Retry-After"]
        assert upload.status_code == 429
        assert other_user.status_code == 201

        released = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=users["a"]["headers"])
        assert released.status_code == 200 and released.json()["success"] is True

    def test_slot_is_released_when_a_job_fails(self, users, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_CONCURRENT_JOBS_PER_USER", 1)
        application = get_application()

        with pytest.raises(RuntimeError):
            with application._job_slot(users["a"]["context"]):
                raise RuntimeError("job crashed")

        with application._job_slot(users["a"]["context"]):
            pass
