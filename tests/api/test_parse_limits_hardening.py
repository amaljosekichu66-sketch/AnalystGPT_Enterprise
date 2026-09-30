"""
Regression tests for M5, M8 and I8 (audit 2026-09-29).

- M5: the shape caps ran only after a full parse (a 200,000-column CSV took
  19 s); 500 MB CSV / JSON files were parsed fully in memory.
- M8: the Streamlit uploader parsed the file before sending it, with no
  archive check or shape caps, and cached every DataFrame without bound.
- I8: bidi / zero-width characters passed through filenames, and length was
  counted in characters, so long multibyte names answered 500.
"""

from __future__ import annotations

import io
import json
import uuid
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService
from src.upload import bounded_parse, upload_policy
from src.upload.csv_reader import CSVReader
from src.upload.upload_policy import UploadRejectedError, UploadTooLargeError

_PASSWORD = "Password123!"


@pytest.fixture(scope="module")
def headers() -> dict[str, str]:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    name = f"m5_{uuid.uuid4().hex[:6]}"
    service.register_user(
        UserCreate(username=name, email=f"{name}@example.com", password=_PASSWORD, role=UserRole.ANALYST)
    )
    _, token, _ = service.login(UserLogin(username=name, password=_PASSWORD))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    return TestClient(app)


def _csv(columns: int, rows: int) -> bytes:
    header = ",".join(f"c{i}" for i in range(columns))
    body = "\n".join(",".join("1" for _ in range(columns)) for _ in range(rows))
    return f"{header}\n{body}\n".encode()


class TestLimitsDuringParse:
    def test_wide_csv_is_refused_from_the_header(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_UPLOAD_COLUMNS", 10)
        path = tmp_path / "wide.csv"
        path.write_bytes(_csv(columns=50, rows=100))
        calls: list[dict] = []
        real = pd.read_csv
        monkeypatch.setattr(bounded_parse.pd, "read_csv", lambda *a, **k: calls.append(k) or real(*a, **k))

        with pytest.raises(UploadTooLargeError, match="columns"):
            CSVReader().read(path)
        assert calls == [{"nrows": 0}]

    def test_long_csv_is_read_only_past_the_limit(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_UPLOAD_ROWS", 5)
        path = tmp_path / "long.csv"
        path.write_bytes(_csv(columns=3, rows=1000))
        assert len(CSVReader().read(path)) == 6

    def test_excel_rows_are_capped(self, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_UPLOAD_ROWS", 5)
        buffer = io.BytesIO()
        pd.DataFrame({"a": range(100)}).to_excel(buffer, index=False)
        buffer.seek(0)
        assert len(bounded_parse.read_excel_bounded(buffer)) == 6

    def test_json_over_its_cap_is_refused_before_parsing(self, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_JSON_FILE_SIZE_MB", 1)
        payload = json.dumps([{"a": "x" * 100}] * 20_000).encode()
        with patch.object(bounded_parse.pd, "read_json") as read_json:
            with pytest.raises(UploadTooLargeError, match="JSON"):
                bounded_parse.read_json_bounded(io.BytesIO(payload))
        read_json.assert_not_called()

    def test_api_answers_413_not_422_for_wide_files(self, client: TestClient, headers, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_UPLOAD_COLUMNS", 10)
        res = client.post("/api/datasets", headers=headers, files={"file": ("wide.csv", _csv(50, 3), "text/csv")})
        assert res.status_code == 413

    def test_api_answers_413_for_long_files(self, client: TestClient, headers, monkeypatch) -> None:
        monkeypatch.setattr(config, "MAX_UPLOAD_ROWS", 5)
        res = client.post("/api/datasets", headers=headers, files={"file": ("long.csv", _csv(3, 50), "text/csv")})
        assert res.status_code == 413

    def test_default_limits_were_lowered(self) -> None:
        assert config.MAX_FILE_SIZE_MB <= 100
        assert config.MAX_XLSX_UNCOMPRESSED_MB <= 256


class TestFrontendUploader:
    def test_backend_validates_before_anything_is_parsed(self) -> None:
        from src.frontend.components import uploader

        uploaded = MagicMock(name="uploaded", size=10)
        uploaded.name = "a.csv"
        uploaded.getvalue.return_value = b"a,b\n1,2\n"

        with (
            patch.object(uploader.st, "file_uploader", return_value=uploaded),
            patch.object(uploader.st, "error") as error,
            patch.object(uploader, "upload_to_backend", side_effect=RuntimeError("Backend returned HTTP 413: big")),
            patch.object(uploader, "load_dataframe") as load,
        ):
            uploader.render_uploader()

        load.assert_not_called()
        error.assert_called_once_with("The dataset is too large.")

    def test_local_parse_applies_the_archive_check(self) -> None:
        from src.frontend.components import uploader

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("xl/worksheets/sheet1.xml", b"0" * (5 * 1024 * 1024))
        with pytest.raises(UploadRejectedError):
            uploader.load_dataframe.__wrapped__(buffer.getvalue(), "bomb.xlsx")

    def test_local_parse_applies_the_shape_limits(self, monkeypatch) -> None:
        from src.frontend.components import uploader

        monkeypatch.setattr(config, "MAX_UPLOAD_COLUMNS", 10)
        with pytest.raises(UploadTooLargeError):
            uploader.load_dataframe.__wrapped__(_csv(50, 3), "wide.csv")

    def test_streamlit_upload_size_matches_the_api(self) -> None:
        text = (Path(__file__).resolve().parents[2] / ".streamlit" / "config.toml").read_text(encoding="utf-8")
        assert f"maxUploadSize = {config.MAX_FILE_SIZE_MB}" in text


class TestFilenamePolicy:
    @pytest.mark.parametrize("raw", ["invoice‮xcs.csv", "re​port.csv", "﻿data.csv"])
    def test_format_characters_are_stripped(self, raw: str) -> None:
        name = upload_policy.safe_upload_filename(raw)
        assert all(ch not in name for ch in "‮​﻿")

    def test_length_is_counted_in_bytes(self) -> None:
        with pytest.raises(UploadRejectedError, match="too long"):
            upload_policy.safe_upload_filename("é" * 200 + ".csv")

    def test_multibyte_name_is_400_not_500(self, client: TestClient, headers) -> None:
        res = client.post("/api/datasets", headers=headers, files={"file": ("é" * 200 + ".csv", b"a\n1\n", "text/csv")})
        assert res.status_code == 400
