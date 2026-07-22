"""
AnalystGPT Enterprise

Application entry point.
"""

from pathlib import Path

from src.application.app import Application
from src.core.logger import logger


def main() -> None:
    """
    Launch the AnalystGPT Enterprise application.
    """

    application = Application()

    sample_file = (
    Path("performance")
    / "datasets"
    / "customer_data_stress_test.csv"
)

    result = application.run(
        str(sample_file)
    )

    if not result.success:

        logger.error(
            "Application failed."
        )

        if result.error is not None:
            raise result.error


if __name__ == "__main__":
    main()