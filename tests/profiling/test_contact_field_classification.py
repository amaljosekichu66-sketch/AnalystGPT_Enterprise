"""
Regression tests: a column name is a hypothesis, not a verdict.

The defect
----------
`classify_column` matched contact keywords as bare substrings against the
column name and returned immediately, never consulting the values. Measured on
the real 27,945-row dataset, with the fraction of values that are actually
email addresses:

    client_email            -> EMAIL    97.2% addresses, mean length  22   correct
    email_subject           -> EMAIL     0.2% addresses, mean length  48   wrong
    email_body_(outbound)   -> EMAIL     0.0% addresses, mean length 627   wrong
    ai_-_email_summary      -> EMAIL     0.0% addresses, mean length 432   wrong

The three wrong ones were then given `visualization: excluded` and masked out
of the AI prompt as contact identifiers - removing the only columns that
recorded what each ticket was about, while the model was still asked for
"business implications".

The fix is not a longer keyword list. It is that the values must agree.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.profiling.models import AnalyticalRole, SemanticType
from src.profiling.semantic_classifier import SemanticClassifier


@pytest.fixture()
def classifier() -> SemanticClassifier:
    return SemanticClassifier()


def _repeat(values: list[str], count: int = 400) -> pd.Series:
    return pd.Series([values[index % len(values)] for index in range(count)])


# ==========================================================
# Genuine contact columns still classify correctly
# ==========================================================


def test_real_email_column_is_an_email(classifier: SemanticClassifier) -> None:
    series = pd.Series([f"user{index}@example.com" for index in range(500)])

    semantic_type, role, *_ = classifier.classify_column("client_email", series, len(series))

    assert semantic_type is SemanticType.EMAIL
    assert role is AnalyticalRole.CONTACT_IDENTIFIER


def test_email_column_detected_without_a_helpful_name(
    classifier: SemanticClassifier,
) -> None:
    """Values alone are sufficient evidence."""
    series = pd.Series([f"user{index}@example.com" for index in range(500)])

    semantic_type, *_ = classifier.classify_column("contact", series, len(series))

    assert semantic_type is SemanticType.EMAIL


def test_real_phone_column_is_a_phone(classifier: SemanticClassifier) -> None:
    series = pd.Series([f"555-01{index:02d}-2000" for index in range(300)])

    semantic_type, role, *_ = classifier.classify_column("client_phone", series, len(series))

    assert semantic_type is SemanticType.PHONE
    assert role is AnalyticalRole.CONTACT_IDENTIFIER


# ==========================================================
# Content columns must not be captured by the keyword
# ==========================================================


def test_email_subject_is_not_an_email_address(
    classifier: SemanticClassifier,
) -> None:
    """Mean length 48, essentially no addresses."""
    series = _repeat(
        [
            "I rescheduled this for 10:00 am",
            "Following up on my submitted evidence",
            "Please confirm receipt of the retainer",
            "Question about my case status",
        ]
    )

    semantic_type, role, *_ = classifier.classify_column("email_subject", series, len(series))

    assert semantic_type is not SemanticType.EMAIL
    assert role is not AnalyticalRole.CONTACT_IDENTIFIER


def test_long_email_body_is_free_text(classifier: SemanticClassifier) -> None:
    """
    Mean length 627, 46.6% distinct. Length settles it: the old uniqueness gate
    of 0.80 left this classified as a CATEGORICAL_DIMENSION with roughly 13,000
    "categories", each a paragraph long.
    """
    body = (
        "Thank you for reaching out regarding your claim. Our team has reviewed "
        "the documentation you submitted and we are following up with the "
        "relevant department to confirm the next steps in your case. "
    ) * 3
    series = pd.Series([f"{body} Reference {index}." for index in range(500)])

    semantic_type, role, _, _, visual, _ = classifier.classify_column("email_body_(outbound)", series, len(series))

    assert semantic_type is SemanticType.FREE_TEXT
    assert role is AnalyticalRole.DESCRIPTIVE_ATTRIBUTE
    assert visual == "excluded"


def test_ai_email_summary_is_free_text(classifier: SemanticClassifier) -> None:
    """Mean length 432, fully distinct, zero addresses."""
    series = pd.Series(
        [
            "The client sent an SMS stating they rescheduled this for 10:00 am. "
            "There is no firm reply and the thread repeats the outreach content. "
            f"Case reference {index} requires manual follow-up before closure."
            for index in range(500)
        ]
    )

    semantic_type, *_ = classifier.classify_column("ai_-_email_summary", series, len(series))

    assert semantic_type is not SemanticType.EMAIL
    assert semantic_type is SemanticType.FREE_TEXT


@pytest.mark.parametrize(
    "column_name",
    ["email_notes", "phone_transcript", "zip_description", "mail_body"],
)
def test_long_prose_is_never_a_contact_identifier(
    classifier: SemanticClassifier,
    column_name: str,
) -> None:
    """A contact detail is short by construction."""
    series = pd.Series(
        [
            "This is a long narrative field describing what happened during the "
            f"interaction in considerable detail, entry number {index}."
            for index in range(300)
        ]
    )

    _, role, *_ = classifier.classify_column(column_name, series, len(series))

    assert role is not AnalyticalRole.CONTACT_IDENTIFIER


def test_short_categorical_named_like_a_contact_field_is_not_masked_away(
    classifier: SemanticClassifier,
) -> None:
    """Short values, but still not addresses - the values decide."""
    series = _repeat(["Delivered", "Bounced", "Opened", "Unsubscribed"])

    semantic_type, role, *_ = classifier.classify_column("email_status", series, len(series))

    assert semantic_type is SemanticType.CATEGORICAL
    assert role is AnalyticalRole.CATEGORICAL_DIMENSION
