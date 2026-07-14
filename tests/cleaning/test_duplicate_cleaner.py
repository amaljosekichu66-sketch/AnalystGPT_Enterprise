import pandas as pd

from src.cleaning.duplicate_cleaner import DuplicateCleaner


def test_duplicate_cleaner_removes_duplicate_rows():
    df = pd.DataFrame({
        "name": [
            "Amal",
            "Amal",
            "John"
        ],
        "age": [
            27,
            27,
            31
        ]
    })

    cleaner = DuplicateCleaner()

    result = cleaner.clean(df)

    assert len(result) == 2

    assert result["name"].tolist() == [
        "Amal",
        "John"
    ]