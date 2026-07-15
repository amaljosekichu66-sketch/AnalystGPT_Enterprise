import pandas as pd

from src.quality.quality_manager import QualityManager


def test_quality_manager_assesses_dataset():
    df = pd.DataFrame({
        "name": [
            "Amal",
            " Amal",
            None,
            "Amal",
        ],
        "age": [
            27,
            27,
            30,
            500,
        ],
    })

    manager = QualityManager()
    result = manager.assess(df)

    assert "completeness" in result
    assert "validity" in result
    assert "consistency" in result
    assert "uniqueness" in result
    assert "outliers" in result