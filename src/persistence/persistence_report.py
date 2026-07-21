from dataclasses import dataclass


@dataclass(frozen=True)
class PersistenceReport:
    """
    Summary of persistence operations completed
    during a pipeline execution.
    """

    pipeline_run_id: int

    dataset_id: int

    quality_report_id: int

    analytics_report_id: int

    report_id: int

    saved_records: int

    status: str