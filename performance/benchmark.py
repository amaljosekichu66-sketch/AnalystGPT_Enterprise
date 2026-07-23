"""
Performance Benchmark Framework

Measures AnalystGPT Enterprise pipeline
performance over multiple executions.
"""

from __future__ import annotations

import csv
import statistics
import time
from datetime import datetime
from pathlib import Path

from src.application.app import Application
from src.core.config import DATABASE_ENGINE

# ==========================================================
# Paths
# ==========================================================

PERFORMANCE_DIR = Path(__file__).parent

DATASET = (
    PERFORMANCE_DIR
    / "datasets"
    / "customer_data_stress_test.csv"
)

RESULT_FILE = (
    PERFORMANCE_DIR
    / "benchmark_results.csv"
)

# ==========================================================
# Benchmark
# ==========================================================


class BenchmarkRunner:
    """
    Executes repeated benchmark runs.
    """

    def __init__(
        self,
        runs: int = 10,
    ) -> None:

        self.runs = runs

        self.results: list[dict] = []

    def execute(self) -> None:
        """
        Execute benchmark.
        """

        print("=" * 70)
        print("AnalystGPT Enterprise Benchmark")
        print("=" * 70)

        for run in range(
            1,
            self.runs + 1,
        ):

            print(
                f"Run {run}/{self.runs}"
            )

            application = Application()

            start_timestamp = datetime.now()

            start = time.perf_counter()

            result = application.run(
                str(DATASET)
            )

            execution = (
                time.perf_counter() - start
            )

            end_timestamp = datetime.now()

            report = (
                result.reporting_report.report
            )

            analytics = report.analytics

            descriptive = analytics[
                "descriptive_statistics"
            ]

            self.results.append(
                {
                    "Run": run,
                    "Database": DATABASE_ENGINE,
                    "Start": start_timestamp.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "End": end_timestamp.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "Rows": descriptive[
                        "total_rows"
                    ],
                    "Columns": descriptive[
                        "total_columns"
                    ],
                    "Memory(MB)": round(
                        descriptive[
                            "memory_usage_mb"
                        ],
                        2,
                    ),
                    "Execution(s)": round(
                        execution,
                        4,
                    ),
                    "Status": (
                        "SUCCESS"
                        if result.success
                        else "FAILED"
                    ),
                }
            )

            print(
                f"Completed in "
                f"{execution:.2f} sec"
            )

        self.export_csv()

        self.print_summary()

    # -----------------------------------------------------

    def export_csv(self) -> None:

        RESULT_FILE.parent.mkdir(
            exist_ok=True
        )

        with RESULT_FILE.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=self.results[
                    0
                ].keys(),
            )

            writer.writeheader()

            writer.writerows(
                self.results
            )

    # -----------------------------------------------------

    def print_summary(self) -> None:

        executions = [
            row["Execution(s)"]
            for row in self.results
        ]

        print()

        print("=" * 70)
        print("Benchmark Summary")
        print("=" * 70)

        print(
            f"Runs            : {self.runs}"
        )

        print(
            f"Database        : {DATABASE_ENGINE}"
        )

        print(
            f"Average         : "
            f"{statistics.mean(executions):.2f} s"
        )

        print(
            f"Fastest         : "
            f"{min(executions):.2f} s"
        )

        print(
            f"Slowest         : "
            f"{max(executions):.2f} s"
        )

        if len(executions) > 1:

            print(
                f"Std Dev         : "
                f"{statistics.stdev(executions):.2f} s"
            )

        print(
            f"CSV Report      : "
            f"{RESULT_FILE}"
        )

        print("=" * 70)


# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":

    BenchmarkRunner(
        runs=10,
    ).execute()