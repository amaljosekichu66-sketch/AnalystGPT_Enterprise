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