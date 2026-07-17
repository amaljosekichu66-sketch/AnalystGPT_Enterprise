"""
AnalystGPT Enterprise

Application entry point.
"""

from src.application.app import Application
from src.core.logger import logger


def main() -> None:
    """
    Launch the AnalystGPT Enterprise application.
    """

    application = Application()

    result = application.run(
        "sample_data/customer_data.csv"
    )

    if not result.success:

        logger.error(
            "Application failed."
        )

        if result.error is not None:
            raise result.error


if __name__ == "__main__":
    main()