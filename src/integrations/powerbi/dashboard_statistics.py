"""
Power BI Statistics Model.
"""

from typing import Any

from pydantic import BaseModel


class DashboardStatistics(BaseModel):
    """
    Descriptive statistics.
    """

    descriptive_statistics: dict[str, Any]