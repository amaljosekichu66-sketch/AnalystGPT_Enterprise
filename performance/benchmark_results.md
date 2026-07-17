# AnalystGPT Enterprise Performance Benchmark Results

**Version:** v5.0.0  
**Sprint:** 5 – Reporting Module  
**Test Date:** 16 July 2026

---

## Test Environment

- Python 3.11
- Windows 11
- Visual Studio Code

---

## Benchmark Results

| Dataset | Input Rows | Output Rows | Total Pipeline Time | Memory Usage |
|---------|-----------:|------------:|--------------------:|-------------:|
| customer_data.csv | 500 | 394 | ~0.08 s | 0.09 MB |
| customer_data_large.csv | 100,000 | 87,049 | ~1.10 s | 24.51 MB |
| customer_data_stress_test.csv | 1,000,000 | 869,917 | ~7.18 s | 194.27 MB |

---

## Observations

- Successfully processed datasets ranging from **500** to **1,000,000** rows.
- Pipeline completed without runtime errors or warnings.
- Memory usage scaled proportionally with dataset size.
- Reporting module exported reports successfully for all benchmark datasets.
- End-to-end pipeline remained stable under stress-test conditions.

---

## Conclusion

The current implementation demonstrates stable functional behavior and acceptable performance across small, medium, and large datasets, providing a solid baseline for future optimization and scalability improvements.

---

---

# Sprint 5.5 — Architecture Validation Benchmarks

**Version:** v5.5.0

**Date:** 17 July 2026

## Objective

Validate that the Sprint 5.5 enterprise architecture refactor
introduced no functional or measurable performance regressions.

The refactor modified pipeline orchestration only.
Business functionality remained unchanged.

---

# Test Environment

| Item | Value |
|------|-------|
| Python | 3.11 |
| Pandas | 3.x |
| Test Framework | Pytest |
| Platform | Windows 11 |
| IDE | Visual Studio Code |

---

# Validation Datasets

| Dataset | Records | Status |
|----------|---------|--------|
| customer_data.csv | 500 | ✅ Passed |
| customer_data_large.csv | 100,000 | ✅ Passed |
| customer_data_stress_test.csv | 1,000,000 | ✅ Passed |

---

# Validation Scope

The following components were validated after the architecture refactor:

- Upload
- Cleaning
- Quality
- Analytics
- Reporting
- Application Layer
- PipelineResult

---

# Functional Validation

Completed successfully:

- Dataset loading
- Cleaning pipeline
- Quality assessment
- Analytics generation
- Report generation
- Report export
- PipelineResult generation

---

# Regression Testing

Result:

```text
79 Tests Passed
0 Failed
0 Errors
0 Warnings
```

---

# Performance Result

No measurable regression was observed after introducing:

- Application Layer
- Application.run()
- PipelineResult
- Thin main.py

Pipeline behavior remained stable across all datasets.

---

# Conclusion

Sprint 5.5 successfully improved the internal architecture while
preserving existing functionality, automated test coverage, and
performance characteristics.

The repository is validated and ready for Sprint 6.