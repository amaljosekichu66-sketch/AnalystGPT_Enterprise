import pandas as pd

from src.quality.uniqueness_checker import UniquenessChecker


def test_uniqueness_checker_detects_duplicate_rows():
    df = pd.DataFrame({
        "name": [
            "Amal",
            "Amal",
        ],
        "age": [
            27,
            27,
        ],
    })

    checker = UniquenessChecker()
    result = checker.check(df)

    assert result["duplicate_rows"] == 1