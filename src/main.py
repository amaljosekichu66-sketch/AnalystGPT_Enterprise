from core.constants import APP_NAME
from core.logger import logger


def main():
    """Application entry point."""
    logger.info("Application Started")
    print(f"Welcome to {APP_NAME}")


if __name__ == "__main__":
    main()