"""
Shared sample dataset used across all unit tests.
"""

import pandas as pd


def sample_dataframe() -> pd.DataFrame:
    """
    Return a reusable sample DataFrame for testing.

    Returns
    -------
    pd.DataFrame
        Representative dataset containing numerical,
        categorical, boolean, datetime, missing values,
        duplicates, and an outlier.
    """

    return pd.DataFrame(
        {
            "Age": [21, 25, 30, 40, 45, 45],
            "Salary": [30000, 35000, 50000, 70000, 90000, 900000],
            "Gender": ["M", "F", "F", "M", "F", "F"],
            "Department": [
                "IT",
                "HR",
                "IT",
                "Sales",
                "HR",
                "HR",
            ],
            "Active": [True, True, False, True, False, False],
            "Joining_Date": pd.to_datetime(
                [
                    "2020-01-01",
                    "2021-02-15",
                    "2022-03-10",
                    "2023-04-20",
                    "2024-05-25",
                    "2024-05-25",
                ]
            ),
            "Bonus": [1000, 1500, None, 2000, 2500, 2500],
        }
    )