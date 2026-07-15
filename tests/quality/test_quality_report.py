from src.quality.quality_report import QualityReport


def test_quality_report_generates_report():
    results = {
        "completeness": {},
        "validity": {},
        "consistency": {},
        "uniqueness": {},
        "outliers": {},
    }

    report = QualityReport().generate(results)

    assert report == results