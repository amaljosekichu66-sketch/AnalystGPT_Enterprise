"""
AI Insight Engine API routes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.application_dependency import (
    get_application,
)
from src.api.models.response_models import AIReportResponse
from src.application.app import Application


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post(
    "/insights",
    response_model=AIReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI Insights",
    description=(
        "Generate AI insights from the reporting result of "
        "the latest successful pipeline execution."
    ),
)
def generate_ai_insights(
    application: Application = Depends(
        get_application,
    ),
) -> AIReportResponse:
    """
    Generate AI insights from the latest reporting result.

    Raises
    ------
    HTTPException
        If no completed pipeline result is available or AI
        insight generation fails.
    """
    pipeline_result = application.get_last_result()

    if (
        pipeline_result is None
        or pipeline_result.pipeline_report is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No completed pipeline result is available. "
                "Run the pipeline before requesting AI insights."
            ),
        )

    reporting_report = (
        pipeline_result.pipeline_report.reporting_report
    )

    ai_result = application.ai_manager.generate_ai_report(
        reporting_report,
    )

    if not ai_result.success or ai_result.ai_report is None:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "AI insight generation failed: "
                f"{ai_result.error or 'Unknown error'}"
            ),
        )

    ai_report = ai_result.ai_report

    return AIReportResponse(
        executive_summary=ai_report.executive_summary,
        recommendations=ai_report.recommendations,
        explanations=ai_report.explanations,
        narrative=ai_report.narrative,
        model=ai_report.model,
        provider=ai_report.provider,
        execution_time=ai_report.execution_time,
    )