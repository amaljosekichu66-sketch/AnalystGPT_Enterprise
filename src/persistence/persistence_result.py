from dataclasses import dataclass


@dataclass(frozen=True)
class PersistenceResult:
    """
    Represents the outcome of all persistence operations
    performed during a pipeline execution.
    """

    pipeline_run_id: int

    dataset_id: int

    quality_report_id: int

    analytics_report_id: int

    report_id: int

    success: bool