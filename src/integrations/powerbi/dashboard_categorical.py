"""
Power BI Categorical Model.
"""

from typing import Any

from pydantic import BaseModel


class DashboardCategorical(BaseModel):
    """
    Categorical analysis.
    """

    categorical_analysis: dict[str, Any]