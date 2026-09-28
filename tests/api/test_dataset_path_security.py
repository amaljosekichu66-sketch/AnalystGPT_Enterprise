"""
Regression tests for B-02 / SEC-02 / SEC-19: client-controlled server paths.

`POST /api/pipeline {"input_path": ...}` and `GET /api/powerbi/*?dataset=...`
used to accept any server path. The server copied that file into the artifact
store, and `POST /api/governance/preview` then returned its rows - an
arbitrary file read for any ANALYST. Responses also disclosed absolute
server paths (`storage_path`, `output_path`, `export_path`).

Clients now upload bytes to `POST /api/datasets` and reference the result by
`dataset_version_id` only; the server resolves it with ownership enforced.
"""

from __future__ import annotations

import io
import os
import re
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.application_dependency import get_application
from src.api.server import app
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService
from src.upload import upload_policy
from tests.fixtures.datasets import upload_dataset

SAMPLE_CSV = Path("sample_data/customer_data.csv")
CANARY_TOKEN = "CANARY-7f3a-do-not-disclose"
_PASSWORD = "Password123!"

# Absolute-path shapes that must never appear in a response body.
_ABSOLUTE_PATH = re.compile(r"(?:^|[\s\"'=(])(?:[A-Za-z]:[\\/]|\\\\[^\\]|/(?:app|etc|home|root|tmp|var|usr|Users)/)")


@pytest.fixture(scope="module")
def users() -> dict[str, dict[str, str]]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))

    tokens: dict[str, dict[str, str]] = {}
    suffix = uuid.uuid4().hex[:6]
    for key, role in (("a", UserRole.ANALYST), ("b", UserRole.ANALYST), ("admin", UserRole.ADMIN)):
        name = f"b02_{key}_{suffix}"
        service.register_user(UserCreate(username=name, email=f"{name}@example.com", password=_PASSWORD, role=role))
        _, token, _ = service.login(UserLogin(username=name, password=_PASSWORD))
        tokens[key] = {"Authorization": f"Bearer {token}"}
    return tokens


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # Production posture: identity comes from tokens only.
    monkeypatch.setattr("src.core.config.AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app)


@pytest.fixture
def canary(tmp_path: Path) -> Path:
    """A readable server file outside every managed directory."""
    path = tmp_path / "outside" / "canary_secret.csv"
    path.parent.mkdir()
    path.write_text(f"secret_key,value\n{CANARY_TOKEN},1\n", encoding="utf-8")
    return path


def _raw_artifacts() -> set[Path]:
    raw_dir = get_application().artifact_store.raw_dir
    return {p for p in raw_dir.rglob("*") if p.is_file()}


def _assert_no_absolute_paths(payload: object, where: str) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            _assert_no_absolute_paths(value, f"{where}.{key}")
    elif isinstance(payload, list):
        for i, value in enumerate(payload):
            _assert_no_absolute_paths(value, f"{where}[{i}]")
    elif isinstance(payload, str):
        assert not _ABSOLUTE_PATH.search(payload), f"absolute server path disclosed at {where}: {payload!r}"


# ==========================================================
# 1. Valid upload
# ==========================================================


class TestManagedUpload:
    def test_valid_upload_returns_id_and_no_path(self, client: TestClient, users) -> None:
        res = client.post("/api/datasets", files={"file": ("sales.csv", SAMPLE_CSV.read_bytes())}, headers=users["a"])

        assert res.status_code == 201, res.text
        body = res.json()
        uuid.UUID(body["dataset_version_id"])
        assert body["filename"] == "sales.csv"
        assert body["row_count"] > 0
        assert "storage_path" not in body
        _assert_no_absolute_paths(body, "upload")

    def test_uploaded_dataset_runs_through_pipeline(self, client: TestClient, users) -> None:
        dataset_id = upload_dataset(client, SAMPLE_CSV, users["a"])

        res = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=users["a"])

        assert res.status_code == 200, res.text
        body = res.json()
        assert body["success"] is True, body
        assert body["dataset_version_id"] == dataset_id
        assert body["output_path"] and "/" not in body["output_path"] and "\\" not in body["output_path"]

    def test_client_filename_cannot_steer_storage_location(self, client: TestClient, users) -> None:
        raw_dir = get_application().artifact_store.raw_dir.resolve()
        before = _raw_artifacts()

        res = client.post(
            "/api/datasets",
            files={"file": ("..\\..\\..\\evil.csv", SAMPLE_CSV.read_bytes())},
            headers=users["a"],
        )

        assert res.status_code == 201, res.text
        assert res.json()["filename"] == "evil.csv"
        new_files = _raw_artifacts() - before
        assert len(new_files) == 1
        assert new_files.pop().resolve().is_relative_to(raw_dir)

    def test_upload_requires_authentication(self, client: TestClient) -> None:
        res = client.post("/api/datasets", files={"file": ("sales.csv", SAMPLE_CSV.read_bytes())})
        assert res.status_code == 401


# ==========================================================
# 2-4. Client-supplied server paths are refused
# ==========================================================

_PATH_PAYLOADS = {
    "absolute": lambda canary: str(canary),
    "traversal": lambda canary: os.path.relpath(canary, os.getcwd()),
    "dotdot_literal": lambda canary: "../../../../etc/passwd",
    "unc": lambda canary: r"\\127.0.0.1\c$\Windows\win.ini",
    "unc_forward": lambda canary: "//127.0.0.1/share/secret.csv",
}


@pytest.mark.parametrize("kind", sorted(_PATH_PAYLOADS))
class TestServerPathsRejected:
    def test_pipeline_rejects_input_path_field(self, client: TestClient, users, canary: Path, kind: str) -> None:
        before = _raw_artifacts()

        res = client.post("/api/pipeline", json={"input_path": _PATH_PAYLOADS[kind](canary)}, headers=users["a"])

        assert res.status_code == 422
        assert _raw_artifacts() == before
        assert CANARY_TOKEN not in res.text

    def test_pipeline_rejects_path_as_dataset_id(self, client: TestClient, users, canary: Path, kind: str) -> None:
        before = _raw_artifacts()

        res = client.post(
            "/api/pipeline", json={"dataset_version_id": _PATH_PAYLOADS[kind](canary)}, headers=users["a"]
        )

        assert res.status_code == 422
        assert _raw_artifacts() == before

    @pytest.mark.parametrize("endpoint", ["dashboard", "summary", "statistics", "report", "pipeline"])
    def test_powerbi_rejects_paths(self, client: TestClient, users, canary: Path, kind: str, endpoint: str) -> None:
        before = _raw_artifacts()
        path = _PATH_PAYLOADS[kind](canary)

        legacy = client.get(f"/api/powerbi/{endpoint}", params={"dataset": path}, headers=users["a"])
        as_id = client.get(f"/api/powerbi/{endpoint}", params={"dataset_version_id": path}, headers=users["a"])

        assert legacy.status_code == 422
        assert as_id.status_code == 422
        assert _raw_artifacts() == before
        assert CANARY_TOKEN not in legacy.text + as_id.text


def test_original_canary_poc_is_blocked(client: TestClient, users, canary: Path) -> None:
    """
    The original PoC end to end: point the pipeline at a canary file, then
    read it back through the governance preview.
    """
    client.post("/api/pipeline", json={"input_path": str(canary)}, headers=users["a"])
    client.get("/api/powerbi/dashboard", params={"dataset": str(canary)}, headers=users["a"])

    versions = client.get("/api/governance/dataset-versions", headers=users["a"])
    assert versions.status_code == 200
    for version in versions.json():
        assert "storage_path" not in version
        preview = client.post(
            "/api/governance/preview",
            json={"dataset_version_id": version["version_id"]},
            headers=users["a"],
        )
        assert CANARY_TOKEN not in preview.text

    stored = b"".join(p.read_bytes() for p in _raw_artifacts())
    assert CANARY_TOKEN.encode() not in stored


# ==========================================================
# 5-6. Dataset identifiers are ownership-checked
# ==========================================================


class TestDatasetOwnership:
    def test_unknown_dataset_id_is_404(self, client: TestClient, users) -> None:
        res = client.post("/api/pipeline", json={"dataset_version_id": str(uuid.uuid4())}, headers=users["a"])
        assert res.status_code == 404

    def test_user_b_cannot_use_user_a_dataset(self, client: TestClient, users) -> None:
        dataset_id = upload_dataset(client, SAMPLE_CSV, users["a"])

        run = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=users["b"])
        preview = client.post("/api/governance/preview", json={"dataset_version_id": dataset_id}, headers=users["b"])
        meta = client.get(f"/api/governance/dataset-versions/{dataset_id}", headers=users["b"])
        dashboard = client.get("/api/powerbi/dashboard", params={"dataset_version_id": dataset_id}, headers=users["b"])

        assert run.status_code == 404
        assert preview.status_code == 404
        assert meta.status_code == 404
        assert dashboard.status_code == 404
        listing = client.get("/api/governance/dataset-versions", headers=users["b"]).json()
        assert dataset_id not in {v["version_id"] for v in listing}

    def test_owner_and_admin_can_use_dataset(self, client: TestClient, users) -> None:
        dataset_id = upload_dataset(client, SAMPLE_CSV, users["a"])

        owner = client.post("/api/governance/preview", json={"dataset_version_id": dataset_id}, headers=users["a"])
        admin = client.post("/api/governance/preview", json={"dataset_version_id": dataset_id}, headers=users["admin"])

        assert owner.status_code == 200
        assert admin.status_code == 200

    def test_tampered_storage_path_outside_store_is_refused(self, client: TestClient, users, canary: Path) -> None:
        """Defense in depth: a DB row pointing outside the managed store is never read."""
        dataset_id = upload_dataset(client, SAMPLE_CSV, users["a"])
        conn = ConnectionFactory.create_connection()
        conn.connect()
        cursor = conn.get_connection().cursor()
        cursor.execute("UPDATE dataset_versions SET storage_path = ? WHERE version_id = ?", (str(canary), dataset_id))
        conn.commit()
        conn.disconnect()

        run = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=users["a"])
        preview = client.post("/api/governance/preview", json={"dataset_version_id": dataset_id}, headers=users["a"])

        assert run.status_code == 404
        assert preview.status_code == 404
        assert CANARY_TOKEN not in run.text + preview.text


# ==========================================================
# 7-8. Type and size are enforced before persistence
# ==========================================================


class TestUploadValidation:
    @pytest.mark.parametrize("name", ["payload.exe", "script.py", "data.parquet", "noextension", "archive.csv.zip"])
    def test_unsupported_type_rejected_before_persistence(self, client: TestClient, users, name: str) -> None:
        before = _raw_artifacts()

        res = client.post("/api/datasets", files={"file": (name, b"a,b\n1,2\n")}, headers=users["a"])

        assert res.status_code == 415
        assert _raw_artifacts() == before

    def test_oversized_upload_rejected_before_persistence(
        self, client: TestClient, users, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(upload_policy, "max_upload_bytes", lambda: 1024)
        before = _raw_artifacts()

        res = client.post("/api/datasets", files={"file": ("big.csv", b"a,b\n" + b"1,2\n" * 1000)}, headers=users["a"])

        assert res.status_code == 413
        assert _raw_artifacts() == before

    def test_size_limit_counts_actual_bytes_not_declared_size(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(upload_policy, "max_upload_bytes", lambda: 10)

        with pytest.raises(upload_policy.UploadTooLargeError):
            upload_policy.read_bounded(io.BytesIO(b"x" * 11))
        assert upload_policy.read_bounded(io.BytesIO(b"x" * 10)) == b"x" * 10

    def test_empty_upload_rejected(self, client: TestClient, users) -> None:
        res = client.post("/api/datasets", files={"file": ("empty.csv", b"")}, headers=users["a"])
        assert res.status_code == 400

    def test_unparseable_upload_rejected_and_discarded(self, client: TestClient, users) -> None:
        before = _raw_artifacts()

        res = client.post("/api/datasets", files={"file": ("broken.json", b"{not json")}, headers=users["a"])

        assert res.status_code == 422
        assert _raw_artifacts() == before
        _assert_no_absolute_paths(res.json(), "error")

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("..\\..\\x.csv", "x.csv"),
            ("/etc/x.csv", "x.csv"),
            ("\\\\host\\share\\x.csv", "x.csv"),
            ("C:\\Windows\\x.csv", "x.csv"),
        ],
    )
    def test_filename_is_reduced_to_bare_name(self, raw: str, expected: str) -> None:
        assert upload_policy.validate_upload_filename(raw) == expected


# ==========================================================
# 9. No absolute server paths in responses
# ==========================================================


def test_no_absolute_server_paths_in_any_response(client: TestClient, users) -> None:
    dataset_id = upload_dataset(client, SAMPLE_CSV, users["a"])
    run = client.post("/api/pipeline", json={"dataset_version_id": dataset_id}, headers=users["a"])
    assert run.status_code == 200 and run.json()["success"] is True

    responses = {
        "pipeline": run,
        "dataset_versions": client.get("/api/governance/dataset-versions", headers=users["a"]),
        "dataset_version": client.get(f"/api/governance/dataset-versions/{dataset_id}", headers=users["a"]),
        "reports": client.get("/api/reports", headers=users["a"]),
    }
    for endpoint in ("dashboard", "summary", "report", "pipeline"):
        responses[f"powerbi/{endpoint}"] = client.get(
            f"/api/powerbi/{endpoint}", params={"dataset_version_id": dataset_id}, headers=users["a"]
        )

    for name, res in responses.items():
        assert res.status_code == 200, (name, res.text)
        _assert_no_absolute_paths(res.json(), name)


def test_error_messages_redact_server_paths() -> None:
    from src.core.redaction import REDACTED_PATH, redact_server_paths

    for text in (
        r"File not found: C:\Users\me\secret.csv",
        r"cannot open \\fileserver\share\x.csv",
        "No such file: /etc/passwd",
        "missing /app/data/artifacts/raw/ab/x.csv",
    ):
        redacted = redact_server_paths(text)
        assert REDACTED_PATH in redacted
        assert not _ABSOLUTE_PATH.search(redacted), redacted
