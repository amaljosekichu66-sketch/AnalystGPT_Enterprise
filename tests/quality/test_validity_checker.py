import pandas as pd

from src.quality.validity_checker import ValidityChecker


def test_validity_checker_reports_column_information():
    df = pd.DataFrame({
        "name": ["Amal", "John"],
        "age": [27, 30],
    })

    checker = ValidityChecker()
    result = checker.check(df)

    assert result["name"]["data_type"] in (
        "object",
        "string",
        "str",
    )

    assert result["age"]["data_type"] in (
        "int64",
        "Int64",
    )