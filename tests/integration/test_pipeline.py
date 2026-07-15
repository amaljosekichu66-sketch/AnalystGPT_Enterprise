"""
Integration test for the complete AnalystGPT Enterprise pipeline.
"""

from pandas import DataFrame

from src.upload.upload_manager import UploadManager
from src.cleaning.cleaning_manager import CleaningManager
from src.quality.quality_manager import QualityManager
from src.analytics.analytics_manager import AnalyticsManager


def test_complete_pipeline():
    """
    Verify the complete data processing pipeline executes successfully.
    """

    upload_manager = UploadManager()
    cleaning_manager = CleaningManager()
    quality_manager = QualityManager()
    analytics_manager = AnalyticsManager()

    # Upload

    dataframe = upload_manager.upload(
        "sample_data/customer_data.csv"
    )

    assert isinstance(dataframe, DataFrame)

    # Cleaning

    cleaned_dataframe = cleaning_manager.clean(dataframe)

    assert isinstance(cleaned_dataframe, DataFrame)

    # Quality

    quality_report = quality_manager.assess(cleaned_dataframe)

    assert isinstance(quality_report, dict)

    # Analytics

    analytics_report = analytics_manager.analyze(
        cleaned_dataframe
    )

    assert isinstance(analytics_report, dict)

    expected_sections = [
        "descriptive_statistics",
        "numerical_analysis",
        "categorical_analysis",
        "correlation_analysis",
        "distribution_analysis",
    ]

    for section in expected_sections:
        assert section in analytics_report