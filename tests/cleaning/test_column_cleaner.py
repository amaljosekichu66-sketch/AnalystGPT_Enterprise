import pandas as pd

from src.cleaning.column_cleaner import ColumnCleaner


def test_column_cleaner_standardizes_column_names():
    df = pd.DataFrame({
        " Customer Name ": ["Amal"],
        "AGE ": [27],
        " Phone Number ": ["9999999999"]
    })

    cleaner = ColumnCleaner()
    result = cleaner.clean(df)

    assert list(result.columns) == [
        "customer_name",
        "age",
        "phone_number",
    ]