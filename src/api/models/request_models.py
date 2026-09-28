"""
Request models for AnalystGPT Enterprise REST API.

Responsibilities
----------------
- Define standardized API request schemas.
- Validate incoming request payloads.
- Improve OpenAPI documentation.

This module intentionally contains no business logic.
"""

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

# ==========================================================
# Pipeline Request Model
# ==========================================================


#: Canonical UUID text form, as issued by POST /api/datasets.
DATASET_VERSION_ID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


class PipelineRequest(BaseModel):
    """
    Request model for pipeline execution.

    The dataset is referenced ONLY by the server-issued identifier returned
    from `POST /api/datasets`. There is no path field, and unknown fields are
    rejected: the previous `input_path` let a client make the server read any
    file it could reach.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        extra="forbid",
    )

    dataset_version_id: str = Field(
        ...,
        pattern=DATASET_VERSION_ID_PATTERN,
        description="Identifier returned by POST /api/datasets.",
        examples=[
            "0b7c1f2e-3d4a-4b5c-8d9e-0f1a2b3c4d5e",
        ],
    )
