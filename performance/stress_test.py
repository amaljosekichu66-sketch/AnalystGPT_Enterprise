"""
Enterprise Stress Testing Framework.

Repeatedly executes the complete
AnalystGPT Enterprise pipeline while
monitoring system resources.
"""

from __future__ import annotations

import csv
import statistics
import time
from datetime import datetime
from pathlib import Path

import psutil

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
    / "stress_results.csv"
)


class StressTestRunner:
    """
    Enterprise stress test runner.
    """

    def __init__(
        self,
        runs: int = 20,
    ) -> None:

        self.runs = runs

        self.process = psutil.Process()

        self.results: list[dict] = []

    # -----------------------------------------------------

    def execute(self) -> None:

        print("=" * 70)
        print("AnalystGPT Enterprise Stress Test")
        print("=" * 70)

        failures = 0

        for run in range(
            1,
            self.runs + 1,
        ):

            print(
                f"Run {run}/{self.runs}"
            )

            cpu_before = psutil.cpu_percent()

            memory_before = (
                self.process.memory_info().rss
                / 1024
                / 1024
            )

            start = time.perf_counter()

            start_time = datetime.now()

            try:

                application = Application()

                result = application.run(
                    str(DATASET)
                )

                status = (
                    "SUCCESS"
                    if result.success
                    else "FAILED"
                )

            except Exception:

                status = "FAILED"

                failures += 1

            execution = (
                time.perf_counter()
                - start
            )

            end_time = datetime.now()

            cpu_after = psutil.cpu_percent()

            memory_after = (
                self.process.memory_info().rss
                / 1024
                / 1024
            )

            self.results.append(
                {
                    "Run": run,
                    "Database": DATABASE_ENGINE,
                    "Start": start_time.strftime(
                        "%H:%M:%S"
                    ),
                    "End": end_time.strftime(
                        "%H:%M:%S"
                    ),
                    "Execution(s)": round(
                        execution,
                        4,
                    ),
                    "CPU Before": cpu_before,
                    "CPU After": cpu_after,
                    "Memory Before(MB)": round(
                        memory_before,
                        2,
                    ),
                    "Memory After(MB)": round(
                        memory_after,
                        2,
                    ),
                    "Status": status,
                }
            )

            print(
                f"{status} "
                f"{execution:.2f}s"
            )

        self.export_csv()

        self.summary(
            failures,
        )

    # -----------------------------------------------------

    def export_csv(self):

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

    def summary(
        self,
        failures: int,
    ):

        execution = [
            row["Execution(s)"]
            for row in self.results
        ]

        memory = [
            row["Memory After(MB)"]
            for row in self.results
        ]

        print()

        print("=" * 70)
        print("Stress Test Summary")
        print("=" * 70)

        print(
            f"Runs              : {self.runs}"
        )

        print(
            f"Database          : {DATABASE_ENGINE}"
        )

        print(
            f"Failures          : {failures}"
        )

        print(
            f"Average Runtime   : "
            f"{statistics.mean(execution):.2f}s"
        )

        print(
            f"Fastest           : "
            f"{min(execution):.2f}s"
        )

        print(
            f"Slowest           : "
            f"{max(execution):.2f}s"
        )

        print(
            f"Peak Memory       : "
            f"{max(memory):.2f} MB"
        )

        print(
            f"Average Memory    : "
            f"{statistics.mean(memory):.2f} MB"
        )

        print(
            f"CSV Saved         : "
            f"{RESULT_FILE}"
        )

        print("=" * 70)


if __name__ == "__main__":

    StressTestRunner(
        runs=20,
    ).execute()