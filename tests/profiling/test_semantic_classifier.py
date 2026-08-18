"""
Unit and Property Tests for SemanticClassifier.

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.profiling.models import AnalyticalRole, SemanticType
from src.profiling.semantic_classifier import SemanticClassifier


@pytest.fixture
def classifier() -> SemanticClassifier:
    return SemanticClassifier()


def test_classify_phone_numbers(classifier: SemanticClassifier):
    series = pd.Series(["+16474107503", "846-213-0121", "555-123-4567", "415-888-9999"])
    sem_type, role, conf, card, vis, rec = classifier.classify_column("Phone Number", series, 4)
    assert sem_type == SemanticType.PHONE
    assert role == AnalyticalRole.CONTACT_IDENTIFIER
    assert vis == "excluded"
    assert rec == "preserve_nulls"


def test_classify_postal_codes_preserves_leading_zeros(classifier: SemanticClassifier):
    series = pd.Series(["06857", "02396", "73973", "59185", "06857"])
    sem_type, role, conf, card, vis, rec = classifier.classify_column("Zip Code", series, 5)
    assert sem_type == SemanticType.POSTAL_CODE
    assert role == AnalyticalRole.GEOGRAPHIC_IDENTIFIER
    assert rec == "preserve_nulls"


def test_classify_emails(classifier: SemanticClassifier):
    series = pd.Series(["user1@company.com", "admin@domain.org", "test.dev@sub.io"])
    sem_type, role, conf, card, vis, rec = classifier.classify_column("User Email", series, 3)
    assert sem_type == SemanticType.EMAIL
    assert role == AnalyticalRole.CONTACT_IDENTIFIER
    assert vis == "excluded"


def test_classify_person_names(classifier: SemanticClassifier):
    series = pd.Series(["Alice", "Bob", "Charlie", "David", "Eve"])
    sem_type, role, conf, card, vis, rec = classifier.classify_column("First Name", series, 5)
    assert sem_type == SemanticType.PERSON_NAME
    assert role == AnalyticalRole.DESCRIPTIVE_ATTRIBUTE
    assert vis == "excluded"


def test_classify_street_addresses(classifier: SemanticClassifier):
    series = pd.Series(["123 Main St", "456 Elm Ave", "789 Oak Rd"])
    sem_type, role, conf, card, vis, rec = classifier.classify_column("Street Address", series, 3)
    assert sem_type == SemanticType.ADDRESS
    assert role == AnalyticalRole.DESCRIPTIVE_ATTRIBUTE
    assert vis == "excluded"


def test_classify_geographic_dimensions(classifier: SemanticClassifier):
    series_city = pd.Series(["New York", "Chicago", "Houston", "Phoenix", "New York"])
    sem_type, role, conf, card, vis, rec = classifier.classify_column("City", series_city, 5)
    assert sem_type == SemanticType.CITY
    assert role == AnalyticalRole.GEOGRAPHIC_DIMENSION
    assert vis == "categories"

    series_state = pd.Series(["NY", "IL", "TX", "AZ", "NY"])
    sem_type, role, conf, card, vis, rec = classifier.classify_column("State", series_state, 5)
    assert sem_type == SemanticType.STATE_REGION
    assert role == AnalyticalRole.GEOGRAPHIC_DIMENSION


def test_classify_constants(classifier: SemanticClassifier):
    series = pd.Series(["Summer_2026", "Summer_2026", "Summer_2026", "Summer_2026"])
    sem_type, role, conf, card, vis, rec = classifier.classify_column("Campaign", series, 4)
    assert sem_type == SemanticType.CONSTANT
    assert role == AnalyticalRole.CONSTANT_ATTRIBUTE
    assert card == "constant"
    assert vis == "excluded"


def test_classify_unique_identifiers(classifier: SemanticClassifier):
    series = pd.Series(["UQ-001", "UQ-002", "UQ-003", "UQ-004", "UQ-005"])
    sem_type, role, conf, card, vis, rec = classifier.classify_column("Unique_Data", series, 5)
    assert sem_type == SemanticType.IDENTIFIER
    assert role == AnalyticalRole.IDENTIFIER
    assert vis == "excluded"


def test_classify_string_encoded_currency_measures(classifier: SemanticClassifier):
    series = pd.Series(["$12,500.50", "$4,500.00", "$8,900.25", "$15,200.00"])
    sem_type, role, conf, card, vis, rec = classifier.classify_column("Revenue", series, 4)
    assert sem_type == SemanticType.NUMERIC_MEASURE
    assert role == AnalyticalRole.MEASURE
    assert vis == "distribution"
    assert rec == "impute_median"


def test_classify_discrete_numeric_counters(classifier: SemanticClassifier):
    series = pd.Series(["29", "45", "33", "52", "24", "41"])
    sem_type, role, conf, card, vis, rec = classifier.classify_column("Age", series, 6)
    assert sem_type == SemanticType.NUMERIC_DISCRETE
    assert role == AnalyticalRole.DEMOGRAPHIC_MEASURE
    assert vis == "distribution"
    assert rec == "impute_median"


def test_classify_boolean_strings(classifier: SemanticClassifier):
    series = pd.Series(["yes", "no", "yes", "yes", "no"])
    sem_type, role, conf, card, vis, rec = classifier.classify_column("Is_Active", series, 5)
    assert sem_type == SemanticType.BOOLEAN
    assert role == AnalyticalRole.CATEGORICAL_DIMENSION
    assert card == "binary"
