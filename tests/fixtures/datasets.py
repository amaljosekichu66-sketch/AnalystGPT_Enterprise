"""
HTTP helpers for the managed-dataset flow.

Clients no longer pass server paths to `/api/pipeline`: they upload bytes to
`/api/datasets` and use the returned `dataset_version_id`.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from httpx import Response


def upload_dataset(client: TestClient, path: str | Path, headers: dict[str, str]) -> str:
    """Upload a local file through the API and return its dataset_version_id."""
    path = Path(path)
    res = client.post(
        "/api/datasets",
        files={"file": (path.name, path.read_bytes())},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    return res.json()["dataset_version_id"]


def run_pipeline_on_file(client: TestClient, path: str | Path, headers: dict[str, str]) -> Response:
    """Upload a local file, then execute the pipeline on it."""
    dataset_version_id = upload_dataset(client, path, headers)
    return client.post(
        "/api/pipeline",
        json={"dataset_version_id": dataset_version_id},
        headers=headers,
    )
