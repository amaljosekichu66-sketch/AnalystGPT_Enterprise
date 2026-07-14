"""
AnalystGPT Enterprise

Application entry point.
Coordinates the complete data processing pipeline.
"""

from src.cleaning.cleaning_manager import CleaningManager
from src.core.logger import logger
from src.upload.upload_manager import UploadManager


def main() -> None:
    """
    Execute the complete data processing pipeline.
    """

    logger.info("Starting AnalystGPT Enterprise...")

    upload_manager = UploadManager()
    cleaning_manager = CleaningManager()

    dataframe = upload_manager.upload("sample_data/customer_data.csv")

    logger.info("Data Preview Before Cleaning:")
    logger.info("\n%s", dataframe.head())

    dataframe = cleaning_manager.clean(dataframe)

    logger.info("Data Preview After Cleaning:")
    logger.info("\n%s", dataframe.head())

    logger.info("AnalystGPT Enterprise completed successfully.")


if __name__ == "__main__":
    main()