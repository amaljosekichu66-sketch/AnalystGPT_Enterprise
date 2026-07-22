"""
Request models for AnalystGPT Enterprise REST API.

Responsibilities
----------------
- Define standardized API request schemas.
- Validate incoming request payloads.
- Improve OpenAPI documentation.

This module intentionally contains no business logic.
"""

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Pipeline Request Model
# ==========================================================

class PipelineRequest(BaseModel):
    """
    Request model for pipeline execution.
    """

    model_config = ConfigDict(frozen=True)

    input_path: str = Field(
        ...,
        description="Path to the input dataset.",
        min_length=1,
    )