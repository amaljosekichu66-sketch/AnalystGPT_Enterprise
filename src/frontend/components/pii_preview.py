"""
Dataset previews with personal-data columns masked (P2-15).
"""

from __future__ import annotations

import pandas as pd

from src.core.pii import MASK, is_pii_column


def masked_preview(dataframe: pd.DataFrame, rows: int = 20) -> pd.DataFrame:
    """The first `rows` rows, with every personal-data column (by name or values) masked."""
    preview = dataframe.head(rows).copy()
    for column in preview.columns:
        if is_pii_column(str(column), dataframe[column].dropna().head(200).tolist()):
            preview[column] = MASK
    return preview
