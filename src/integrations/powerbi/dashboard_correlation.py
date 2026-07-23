"""
Power BI Correlation Model.
"""

from typing import Any

from pydantic import BaseModel


class DashboardCorrelation(BaseModel):
    """
    Correlation analysis.
    """

    correlation_analysis: dict[str, Any]