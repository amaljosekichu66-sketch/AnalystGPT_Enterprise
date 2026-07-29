"""
AnalystGPT Enterprise.

Application entry point.
"""

from __future__ import annotations

from pathlib import Path

from src.application.app import Application
from src.application.pipeline_result import PipelineResult
from src.core.logger import logger


# ==========================================================
# Configuration
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DEFAULT_DATASET = (
    PROJECT_ROOT
    / "sample_data"
    / "customer_data.csv"
)


# ==========================================================
# Helpers
# ==========================================================

def _create_application() -> Application:
    """Create the application instance."""
    logger.info("Creating application instance...")
    return Application()


def _resolve_dataset() -> Path:
    """
    Resolve the default dataset path.

    Raises
    ------
    FileNotFoundError
        If the dataset does not exist.
    """
    if not DEFAULT_DATASET.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {DEFAULT_DATASET}"
        )

    return DEFAULT_DATASET


def _handle_result(
    result: PipelineResult,
) -> None:
    """Handle the application result."""
    if not result.success:
        logger.error("Application failed.")

        if result.error is not None:
            raise result.error

        raise RuntimeError("Pipeline failed without an error.")

    logger.info("Application completed successfully.")
    logger.info(
        "Execution Time : %.2f seconds",
        result.execution_time or 0.0,
    )

    if result.output_path:
        logger.info(
            "Report Export : %s",
            result.output_path,
        )


# ==========================================================
# Main
# ==========================================================

def main() -> None:
    """Launch AnalystGPT Enterprise."""
    logger.info("=" * 60)
    logger.info("ANALYSTGPT ENTERPRISE")
    logger.info("=" * 60)

    application = _create_application()
    dataset = _resolve_dataset()

    result = application.run(str(dataset))
    _handle_result(result)


if __name__ == "__main__":
    main()