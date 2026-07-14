from core.constants import APP_NAME
from core.logger import logger
from upload.upload_manager import UploadManager


def main():
    """Application entry point."""

    logger.info("Application Started")
    print(f"Welcome to {APP_NAME}")

    uploader = UploadManager()

    file_path = input("\nEnter file path: ")

    dataframe = uploader.upload(file_path)

    print("\nData Loaded Successfully!\n")
    print(dataframe.head())


if __name__ == "__main__":
    main()