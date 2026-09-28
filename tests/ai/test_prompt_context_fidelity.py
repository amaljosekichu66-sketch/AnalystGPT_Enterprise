"""
Regression tests for what the deterministic layer actually hands the model.

Governing principle
-------------------
The LLM explains validated analytical facts; it does not decide what the facts
are. That only holds if the facts genuinely reach it - completely, exactly, and
without content being masked away by accident.

Three measured failures of that contract:

1. `numerical_analysis` - the per-column mean, median, quartiles and standard
   deviation - was computed, persisted, and never serialised. The prompt asked
   the model to "explain the analytical findings" for measures whose figures it
   had never seen.

2. Section text was truncated mid-string (`summary[:600] + "..."`), so a mean
   of 289428.78 could arrive as "28942". A wrong number is worse than a missing
   one, because nothing marks it as wrong.

3. PII masking matched substrings, so `email_subject`,
   `email_body_(outbound)` and `ai_-_email_summary` - the columns describing
   what each ticket was about - were replaced with
   `<masked identifier column>`, while `client_email` needed to be.
"""

from __future__ import annotations

from src.core.pii import is_contact_pii_column
from src.llm.report_serializer import ReportSerializer

# ==========================================================
# 1. Numerical statistics must reach the prompt
# ==========================================================


_NUMERICAL_ANALYSIS = {
    "revenue": {
        "count": 477,
        "mean": 42.1509,
        "median": 42.0,
        "mode": 60.0,
        "minimum": 18.0,
        "maximum": 65.0,
        "range": 47.0,
        "variance": 187.7335,
        "standard_deviation": 13.7016,
        "first_quartile": 31.0,
        "third_quartile": 54.0,
        "interquartile_range": 23.0,
    }
}


def _numerical_section() -> str:
    return "\n".join(
        ReportSerializer._mapping_section(
            "NUMERICAL MEASURE STATISTICS",
            _NUMERICAL_ANALYSIS,
            max_chars=ReportSerializer.ANALYTICS_SECTION_MAX_LENGTH,
            max_items=ReportSerializer.ANALYTICS_SECTION_MAX_ITEMS,
        )
    )


def test_every_numeric_statistic_reaches_the_prompt() -> None:
    """A nested cap of 4 previously dropped everything after the mode."""
    section = _numerical_section()

    for statistic in _NUMERICAL_ANALYSIS["revenue"]:
        assert statistic in section, f"{statistic} was dropped from the prompt"


def test_numeric_values_are_rendered_exactly() -> None:
    section = _numerical_section()

    assert "42.1509" in section
    assert "13.7016" in section
    assert "187.7335" in section


def test_numerical_analysis_is_a_serialised_section() -> None:
    """Guards the section wiring itself, not just the formatter."""
    import inspect

    source = inspect.getsource(ReportSerializer.serialize)

    assert '"numerical_analysis"' in source


# ==========================================================
# 2. Truncation must never split a value
# ==========================================================


def test_truncation_drops_whole_lines_only() -> None:
    text = "- mean: 289428.78\n- median: 289428.00\n- std_dev: 8075.44"

    truncated = ReportSerializer._truncate_on_line_boundary(text, 25)

    assert "- mean: 289428.78" in truncated
    # The surviving figure is complete, and nothing partial follows it.
    for line in truncated.splitlines():
        assert line == "- mean: 289428.78" or line.startswith("- ...")


def test_truncation_announces_what_it_dropped() -> None:
    text = "\n".join(f"- metric_{index}: {index}" for index in range(30))

    truncated = ReportSerializer._truncate_on_line_boundary(text, 100)

    assert "further entries omitted" in truncated


def test_text_within_budget_is_untouched() -> None:
    text = "- mean: 42.0\n- median: 41.0"

    assert ReportSerializer._truncate_on_line_boundary(text, 500) == text


def test_no_partial_number_can_be_emitted() -> None:
    """Every rendered line must survive intact at any budget."""
    text = "\n".join(f"- value_{index}: {index}.123456" for index in range(40))

    for budget in range(20, 400, 17):
        for line in ReportSerializer._truncate_on_line_boundary(text, budget).splitlines():
            assert line.startswith("- ...") or line.endswith(".123456")


# ==========================================================
# 3. Masking must target contact data, not any mention of it
# ==========================================================


def test_real_contact_columns_are_masked() -> None:
    for column in ("client_email", "client_phone", "email", "ssn", "customer_mobile"):
        assert is_contact_pii_column(column), column


def test_ticket_content_columns_are_not_masked() -> None:
    """These are the columns that say what each ticket was actually about."""
    for column in ("email_subject", "email_body_(outbound)", "ai_-_email_summary"):
        assert not is_contact_pii_column(column), column


def test_confidence_column_is_not_treated_as_an_identifier() -> None:
    """
    The text exporter's keyword set contained "id", matched as a substring, so
    `ai_-_classification_confidence` rendered as "Masked identifier field"
    because "confidence" contains "id".
    """
    assert not is_contact_pii_column("ai_-_classification_confidence")
    assert not is_contact_pii_column("confidence")
    assert not is_contact_pii_column("valid_account")


def test_serializer_masking_uses_the_shared_rule() -> None:
    assert ReportSerializer._is_pii_field("client_email") is True
    assert ReportSerializer._is_pii_field("email_subject") is False


def test_categorical_section_keeps_content_columns_visible() -> None:
    categorical = {
        "client_email": {"count": 100, "unique_values": 95, "top_value": "a@b.com", "top_frequency": 2},
        "email_subject": {"count": 100, "unique_values": 30, "top_value": "Rescheduled", "top_frequency": 12},
    }

    section = "\n".join(ReportSerializer._categorical_section("CATEGORICAL ANALYSIS", categorical, total_rows=100))

    assert "masked" in section.lower()
    assert "client_email" in section
    assert "Rescheduled" in section
