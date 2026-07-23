"""
Power BI Distribution Model.
"""

from typing import Any

from pydantic import BaseModel


class DashboardDistribution(BaseModel):
    """
    Distribution analysis.
    """

    distribution_analysis: dict[str, Any]