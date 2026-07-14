import pandas as pd

from src.cleaning.datatype_cleaner import DataTypeCleaner


def test_datatype_cleaner_converts_column_types():
    df = pd.DataFrame({
        "age": ["27", "31"],
        "salary": ["50000.5", "65000.8"]
    })

    cleaner = DataTypeCleaner(
        {
            "age": "int",
            "salary": "float"
        }
    )

    result = cleaner.clean(df)

    assert str(result["age"].dtype).startswith("int")

    assert str(result["salary"].dtype).startswith("float")