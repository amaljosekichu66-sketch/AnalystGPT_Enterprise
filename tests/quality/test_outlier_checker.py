import pandas as pd

from src.quality.outlier_checker import OutlierChecker


def test_outlier_checker_detects_outliers():
    df = pd.DataFrame({
        "salary": [
            10,
            12,
            11,
            13,
            500,
        ]
    })

    checker = OutlierChecker()
    result = checker.check(df)

    assert result["salary"]["outlier_count"] == 1