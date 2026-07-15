import pandas as pd

from src.quality.consistency_checker import ConsistencyChecker


def test_consistency_checker_detects_whitespace():
    df = pd.DataFrame({
        "city": [
            " Kochi",
            "Delhi ",
            "Mumbai",
        ]
    })

    checker = ConsistencyChecker()
    result = checker.check(df)

    assert result["city"]["leading_spaces"] == 1
    assert result["city"]["trailing_spaces"] == 1