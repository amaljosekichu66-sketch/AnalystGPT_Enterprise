"""
Power BI Dashboard Summary Model.
"""

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    """
    Executive dashboard summary.
    """

    success: bool
    execution_time: float
    total_rows: int
    total_columns: int
    numeric_columns: int
    categorical_columns: int
    datetime_columns: int
    memory_usage_mb: float