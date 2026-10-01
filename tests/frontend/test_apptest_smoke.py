"""
Streamlit AppTest smoke tests (P2-08, P2-21).

- With the API stopped, every page renders a readable message and raises
  nothing (no traceback reaches the browser).
- Against the real API (uvicorn in a background thread): a dataset uploaded
  and analysed over HTTP is shown by the Dashboard, Reports and AI Insights
  pages, which only read - opening them creates no pipeline run (P2-06).

The frontend used to be tested only through mocks.
"""

from __future__ import annotations

import socket
import threading
import time
import uuid
from pathlib import Path

import pytest
import uvicorn
from streamlit.testing.v1 import AppTest

from src.core import config
from src.database.connection_factory import ConnectionFactory
from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.frontend.services.api_client import APIClient
from src.identity.models import UserCreate, UserLogin, UserRole
from src.identity.user_service import UserService

APP = str(Path(__file__).resolve().parents[2] / "src" / "frontend" / "streamlit_app.py")
SAMPLE = Path(__file__).resolve().parents[2] / "sample_data" / "customer_data.csv"
PAGES = ["Dashboard", "Upload", "Reports", "AI Insights", "Admin", "About"]
_PASSWORD = "Password123!"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _point_frontend_at(monkeypatch: pytest.MonkeyPatch, base_url: str) -> None:
    defaults = APIClient.__init__.__defaults__
    monkeypatch.setattr(APIClient.__init__, "__defaults__", (base_url, *defaults[1:]))


def _app(page: str, user: dict, token: str = "t", **state) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["auth_token"] = token
    at.session_state["auth_user"] = user
    at.session_state["auth_authenticated"] = "AUTHENTICATED"
    at.session_state["_session_checked_at"] = 1e18  # skip /me revalidation
    at.session_state["current_page"] = page
    for key, value in state.items():
        at.session_state[key] = value
    return at


def _messages(at: AppTest) -> list[str]:
    return [m.value for m in (*at.error, *at.warning, *at.info, *at.success)]


@pytest.mark.parametrize("page", PAGES)
def test_every_page_degrades_readably_with_the_api_stopped(monkeypatch, page: str) -> None:
    _point_frontend_at(monkeypatch, f"http://127.0.0.1:{_free_port()}")
    user = {"id": 1, "username": "u", "role": "ADMIN"}

    at = _app(page, user, dataset_version_id="0b7c1f2e-3d4a-4b5c-8d9e-0f1a2b3c4d5e")
    at.run()

    assert not at.exception, [e.value for e in at.exception]
    assert not any("unexpected error" in m.lower() for m in _messages(at)), _messages(at)
    assert any("Backend Offline" in m for m in _messages(at))


def test_signed_out_visitor_gets_the_sign_in_page(monkeypatch) -> None:
    _point_frontend_at(monkeypatch, f"http://127.0.0.1:{_free_port()}")
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception
    assert any(button.label == "Sign In" for button in at.button)


# ==========================================================
# Against the real API
# ==========================================================


@pytest.fixture(scope="module")
def live_api():
    from src.api.server import app

    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 30
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.1)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture(scope="module")
def analysed(live_api):
    conn = ConnectionFactory.create_connection()
    conn.connect()
    SchemaManager(conn).initialize_schema()
    service = UserService(user_repository=UserRepository(conn))
    name = f"apptest_{uuid.uuid4().hex[:6]}"
    service.register_user(
        UserCreate(username=name, email=f"{name}@example.com", password=_PASSWORD, role=UserRole.ANALYST)
    )
    user, token, _ = service.login(UserLogin(username=name, password=_PASSWORD))

    with APIClient(base_url=live_api) as client:
        upload = client.upload_dataset(filename=SAMPLE.name, content=SAMPLE.read_bytes(), token=token)
        dataset_id = upload["dataset_version_id"]
        run = client._post("/api/pipeline", {"dataset_version_id": dataset_id}, token=token)
    assert run["success"]
    return {"token": token, "user": {"id": user.id, "username": name, "role": "ANALYST"}, "dataset": dataset_id}


def _run_count() -> int:
    conn = ConnectionFactory.create_connection()
    conn.connect()
    try:
        return int(conn.get_connection().execute("SELECT COUNT(*) FROM pipeline_runs").fetchone()[0])
    finally:
        conn.disconnect()


@pytest.mark.parametrize("page", ["Dashboard", "Reports", "AI Insights"])
def test_pages_show_real_api_data_without_running_the_pipeline(monkeypatch, live_api, analysed, page) -> None:
    import pandas as pd

    _point_frontend_at(monkeypatch, live_api)
    monkeypatch.setattr(config, "AUTH_ALLOW_HEADER_IDENTITY", False)
    runs_before = _run_count()

    at = _app(
        page,
        analysed["user"],
        token=analysed["token"],
        dataset_version_id=analysed["dataset"],
        dataframe=pd.read_csv(SAMPLE),
        uploaded_file=None,
    )
    at.run()

    assert not at.exception, [e.value for e in at.exception]
    assert not any(
        m.startswith(("The analytics service", "That item was not found")) for m in _messages(at)
    ), _messages(at)
    assert _run_count() == runs_before
    successes = [m.value for m in at.success]
    if page == "Dashboard":
        assert any("Active Dataset" in m for m in successes), successes
    elif page == "Reports":
        assert any("Export Centre" in h.value for h in at.subheader), [h.value for h in at.subheader]
    else:
        assert any("Current dataset" in m for m in successes), successes


def test_policy_chosen_in_the_ui_is_applied_and_recorded_in_lineage(monkeypatch, live_api, analysed, tmp_path) -> None:
    """P2-04 end to end: Upload page -> proposal -> approval -> run -> lineage."""
    from unittest.mock import MagicMock

    import pandas as pd

    from src.frontend.views import upload_page

    frame = pd.DataFrame({"id": range(40), "amount": [float(i) if i % 4 else None for i in range(40)]})
    path = tmp_path / "gaps.csv"
    frame.to_csv(path, index=False)
    with APIClient(base_url=live_api) as client:
        dataset_id = client.upload_dataset(filename=path.name, content=path.read_bytes(), token=analysed["token"])[
            "dataset_version_id"
        ]

    _point_frontend_at(monkeypatch, live_api)
    uploaded = MagicMock()
    uploaded.name = path.name
    monkeypatch.setattr(upload_page, "render_uploader", lambda: (uploaded, frame))

    at = _app("Upload", analysed["user"], token=analysed["token"], dataset_version_id=dataset_id)
    at.run()
    assert not at.exception, [e.value for e in at.exception]

    at.selectbox(key=f"policy_select_{dataset_id}").set_value("FILL_NUMERIC_MEDIAN").run()
    next(b for b in at.button if b.label.startswith("📨")).click().run()
    assert any("submitted" in m.value for m in at.success)

    at.run()  # re-list proposals
    next(b for b in at.button if b.label == "Approve").click().run()
    at.run()

    radio = at.radio(key=f"run_choice_{dataset_id}")
    approved = next(option for option in radio.options if option.startswith("Approved: FILL_NUMERIC_MEDIAN"))
    radio.set_value(approved).run()
    next(b for b in at.button if b.label.startswith("▶️")).click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("Analysis complete" in m.value for m in at.success), [m.value for m in at.error]

    run_id = at.session_state["pipeline_result"]["pipeline_run_id"]
    with APIClient(base_url=live_api) as client:
        lineage = client._get(f"/api/governance/lineage/run/{run_id}", token=analysed["token"])
    assert lineage["cleaning_config"]["missing_value_policy"] == "FILL_NUMERIC_MEDIAN"
    assert lineage["cleaning_config"]["proposal_id"]
    assert lineage["cleaning_execution"]["rows_removed"] == 0
