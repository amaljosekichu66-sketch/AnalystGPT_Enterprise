import pandas as pd

from src.quality.quality_manager import QualityManager
from src.quality.quality_report import QualityReport


def test_quality_manager_assesses_dataset():

    df = pd.DataFrame(
        {
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
        }
    )

    manager = QualityManager()

    result = manager.assess(df)

    assert isinstance(result, QualityReport)

    assert "completeness" in result.report
    assert "validity" in result.report
    assert "consistency" in result.report
    assert "uniqueness" in result.report
    assert "outliers" in result.report