import pandas as pd

from src.quality.completeness_checker import CompletenessChecker


def test_completeness_checker_reports_missing_values():
    df = pd.DataFrame({
        "name": ["Amal", None],
        "age": [27, None],
    })

    checker = CompletenessChecker()
    result = checker.check(df)

    assert result["total_missing"] == 2
    assert result["missing_per_column"] == {
        "name": 1,
        "age": 1,
    }