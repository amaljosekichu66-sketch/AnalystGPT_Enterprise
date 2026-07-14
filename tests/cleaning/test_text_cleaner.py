import pandas as pd

from src.cleaning.text_cleaner import TextCleaner


def test_text_cleaner_formats_text_columns():
    df = pd.DataFrame({
        "name": [
            " amal ",
            "JOHN",
            "sArA"
        ],
        "city": [
            " kochi",
            "MUMBAI ",
            "deLHi"
        ]
    })

    cleaner = TextCleaner()
    result = cleaner.clean(df)

    assert result["name"].tolist() == [
        "Amal",
        "John",
        "Sara"
    ]

    assert result["city"].tolist() == [
        "Kochi",
        "Mumbai",
        "Delhi"
    ]