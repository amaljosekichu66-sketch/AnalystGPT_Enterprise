import pandas as pd

from src.cleaning.missing_value_cleaner import MissingValueCleaner


def test_missing_value_cleaner_removes_rows_with_missing_values():
    df = pd.DataFrame({
        "name": [
            "Amal",
            None,
            "John"
        ],
        "age": [
            27,
            30,
            None
        ]
    })

    cleaner = MissingValueCleaner()

    result = cleaner.clean(df)

    assert len(result) == 1

    assert result.iloc[0]["name"] == "Amal"

    assert result.iloc[0]["age"] == 27