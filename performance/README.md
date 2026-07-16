# Performance Testing

## Purpose

This directory contains resources related to performance testing and benchmarking for AnalystGPT Enterprise.

Performance testing is separate from automated unit and integration testing.

Its purpose is to evaluate how the application behaves under larger workloads and to identify scalability bottlenecks as the project evolves.

---

## Directory Structure

performance/

├── datasets/
│   └── customer_data_stress_test.csv
│
├── benchmark_results.md
│
└── README.md

---

## Datasets

### customer_data_stress_test.csv

Large dataset used for stress testing.

Current size:

- Approximately 1,000,000 rows
- Used to evaluate:
  - Upload performance
  - Cleaning performance
  - Quality assessment performance
  - Analytics performance
  - Reporting performance
  - Memory usage
  - Overall pipeline execution time

---

## Benchmarking

Benchmark results for each major release should be recorded in:

benchmark_results.md

This allows performance comparisons between releases and helps identify regressions over time.