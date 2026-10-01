"""
Regression tests for P2-15 (Sprint 15 readiness gate).

Names, addresses, dates of birth, IP addresses and SSNs read as safe; camelCase
names were not split; nothing looked at values; and the dashboard, report and
Power BI analytics returned such columns' top values as-is.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.core.pii import MASK, is_contact_pii_column, is_pii_column, mask_pii_columns, values_look_like_pii
from src.core.redaction import public_report_dict
from src.frontend.components.pii_preview import masked_preview


@pytest.mark.parametrize(
    "name",
    [
        "full_name",
        "first_name",
        "last_name",
        "name",
        "customer_name",
        "address",
        "street_address",
        "date_of_birth",
        "dob",
        "ip_address",
        "social_security_number",
        "EmailAddress",
        "phoneNumber",
        "client_email",
    ],
)
def test_personal_data_names_are_pii(name: str) -> None:
    assert is_contact_pii_column(name)


@pytest.mark.parametrize(
    "name",
    [
        "email_subject",
        "ai_-_email_summary",
        "product_name",
        "company_name",
        "mac_address",
        "classification_confidence",
        "order_date",
        "revenue",
    ],
)
def test_analytical_names_stay_visible(name: str) -> None:
    assert not is_contact_pii_column(name)


@pytest.mark.parametrize(
    "values",
    [
        ["a@example.com", "b@example.org", "c@test.co.uk"],
        ["+1 (555) 123-4567", "555-987-6543", "+44 20 7946 0958"],
        ["123-45-6789", "987-65-4321", "111-22-3333"],
        ["10.0.0.1", "192.168.1.20", "8.8.8.8"],
    ],
)
def test_values_reveal_pii_under_innocent_names(values) -> None:
    assert values_look_like_pii(values)
    assert is_pii_column("contact", values)


def test_numbers_and_prose_are_not_pii() -> None:
    assert not values_look_like_pii([5551234567, 5559876543, 5550001111])
    assert not values_look_like_pii(["refund request", "late delivery", "billing issue"])


def test_report_analytics_are_masked() -> None:
    report = {
        "export_path": "/srv/reports/x.txt",
        "report": {"analytics": {"categorical": {"full_name": {"top": ["Ada Lovelace"]}, "region": {"top": ["EU"]}}}},
    }
    public = public_report_dict(report)
    categorical = public["report"]["analytics"]["categorical"]
    assert categorical["full_name"] == MASK
    assert categorical["region"] == {"top": ["EU"]}
    assert report["report"]["analytics"]["categorical"]["full_name"] == {"top": ["Ada Lovelace"]}  # not mutated
    assert mask_pii_columns([{"dob": "1990-01-01"}]) == [{"dob": MASK}]


def test_streamlit_preview_masks_by_name_and_value() -> None:
    frame = pd.DataFrame(
        {
            "full_name": ["Ada", "Alan", "Grace"],
            "contact": ["a@x.com", "b@y.com", "c@z.com"],
            "region": ["EU", "US", "EU"],
        }
    )
    preview = masked_preview(frame)
    assert set(preview["full_name"]) == {MASK} and set(preview["contact"]) == {MASK}
    assert list(preview["region"]) == ["EU", "US", "EU"]
