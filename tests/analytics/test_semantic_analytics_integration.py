"""
Integration test for semantic column typing and analytics governance.

Tests that a 13-column dataset containing names, phone numbers, postal codes,
identifiers, constant columns, addresses, and true numerical measures
correctly segregates columns so that contact info/IDs/constants are not
treated as categorical dimensions or numeric measures.

Sprint 14 Remediation — AI Insights E2E Fix.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.analytics.analytics_manager import AnalyticsManager
from src.analytics.visualization_planner import VisualizationPlanner
from src.profiling.data_profiler import DataProfiler
from src.profiling.models import AnalyticalRole, SemanticType


@pytest.fixture
def enterprise_13_col_df():
    """Create a 13-column enterprise dataset with mixed semantic types."""
    return pd.DataFrame(
        {
            "customer_id": [f"CUST_{i:04d}" for i in range(1, 61)],
            "first_name": ["Alice", "Bob", "Charlie", "Diana"] * 15,
            "last_name": ["Smith", "Jones", "Taylor", "Brown"] * 15,
            "email": [f"user_{i}@enterprise.com" for i in range(1, 61)],
            "phone_number": [f"+1-555-01{i:02d}" for i in range(1, 61)],
            "street_address": [f"{100 + i} Main St" for i in range(1, 61)],
            "city": ["New York", "London", "Tokyo", "Paris"] * 15,
            "state_region": ["NY", "Greater London", "Kanto", "IDF"] * 15,
            "postal_code": [f"{10001 + i}" for i in range(60)],
            "system_status": ["ACTIVE"] * 60,  # Constant attribute
            "subscription_tier": ["Enterprise", "Mid-Market", "SMB"] * 20,
            "contract_value": [f"${10000 + i * 250:,.2f}" for i in range(60)],  # String-encoded numeric
            "churn_risk_score": [0.05 + (i % 10) * 0.08 for i in range(60)],  # Float numeric measure
        }
    )


def test_semantic_profiling_13_columns(enterprise_13_col_df):
    profiler = DataProfiler()
    profile = profiler.profile_dataset(enterprise_13_col_df)

    assert profile.column_count == 13
    assert profile.row_count == 60

    # Verify semantic types
    cp = profile.column_profiles
    assert cp["customer_id"].semantic_type == SemanticType.IDENTIFIER
    assert cp["email"].semantic_type == SemanticType.EMAIL
    assert cp["phone_number"].semantic_type == SemanticType.PHONE
    assert cp["postal_code"].semantic_type == SemanticType.POSTAL_CODE
    assert cp["system_status"].semantic_type == SemanticType.CONSTANT
    assert cp["subscription_tier"].semantic_type == SemanticType.CATEGORICAL
    assert cp["contract_value"].semantic_type in {SemanticType.NUMERIC_MEASURE, SemanticType.NUMERIC_DISCRETE}
    assert cp["churn_risk_score"].semantic_type == SemanticType.NUMERIC_MEASURE


def test_analytics_manager_segregates_semantic_roles(enterprise_13_col_df):
    manager = AnalyticsManager()
    report = manager.analyze(enterprise_13_col_df).report

    desc = report["descriptive_statistics"]
    # Numeric columns should include contract_value and churn_risk_score, NOT phone or postal_code
    assert "contract_value" in desc["numeric_columns"]
    assert "churn_risk_score" in desc["numeric_columns"]
    assert "phone_number" not in desc["numeric_columns"]
    assert "postal_code" not in desc["numeric_columns"]
    assert "customer_id" not in desc["numeric_columns"]

    # Categorical columns should include dimensions (city, state_region, subscription_tier)
    # NOT email, phone, postal_code, customer_id, or constant status
    cat_cols = desc["categorical_columns"]
    assert "subscription_tier" in cat_cols
    assert "city" in cat_cols
    assert "state_region" in cat_cols
    assert "phone_number" not in cat_cols
    assert "email" not in cat_cols
    assert "customer_id" not in cat_cols
    assert "system_status" not in cat_cols

    # Numerical analysis should have analyzed the 2 numerical columns
    num_analysis = report["numerical_analysis"]
    assert "contract_value" in num_analysis
    assert "churn_risk_score" in num_analysis
    assert num_analysis["contract_value"]["mean"] > 10000

    # Categorical analysis should not have analyzed customer_id or phone
    cat_analysis = report["categorical_analysis"]
    assert "customer_id" not in cat_analysis
    assert "phone_number" not in cat_analysis
    assert "email" not in cat_analysis
    assert "subscription_tier" in cat_analysis


def test_visualization_planner_excludes_identifiers_and_contacts(enterprise_13_col_df):
    profiler = DataProfiler()
    profile = profiler.profile_dataset(enterprise_13_col_df)

    planner = VisualizationPlanner()
    plan = planner.plan_visualizations(enterprise_13_col_df, profile)

    # Excluded columns should include customer_id, phone_number, email, street_address, system_status
    excluded_str = " ".join(plan.excluded_columns)
    assert "customer_id" in excluded_str
    assert "phone_number" in excluded_str
    assert "email" in excluded_str
    assert "system_status" in excluded_str

    # Charts should not plot customer_id or phone_number as primary
    for chart in plan.charts:
        assert chart.primary_column not in {"customer_id", "phone_number", "email", "system_status"}
