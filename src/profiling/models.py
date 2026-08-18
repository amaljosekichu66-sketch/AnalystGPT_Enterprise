"""
Domain models for Column Semantic Profiling and Analytical Role Classification.

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class SemanticType(str, Enum):
    """
    Controlled semantic data type taxonomy for analytical columns.
    """

    NUMERIC_MEASURE = "numeric_measure"  # Continuous quantitative measure (e.g. Revenue, Price)
    NUMERIC_DISCRETE = "numeric_discrete"  # Integer count / discrete quantity (e.g. Age, Units, Quantity)
    CATEGORICAL = "categorical"  # Discrete category / dimension (e.g. Lead Status, Department)
    BINARY = "binary"  # Two-state boolean / binary category (e.g. Yes/No, Active/Inactive)
    ORDINAL = "ordinal"  # Ordered category (e.g. Low/Medium/High, Tier 1/2/3)
    DATETIME = "datetime"  # Full timestamp (e.g. 2026-08-16 10:30:00)
    DATE = "date"  # Date only (e.g. 2026-08-16)
    TIME = "time"  # Time only (e.g. 14:30:00)
    BOOLEAN = "boolean"  # True/False boolean
    IDENTIFIER = "identifier"  # Unique system key, UUID, record ID, or hash
    PERSON_NAME = "person_name"  # First Name, Last Name, Full Name
    EMAIL = "email"  # Email address
    PHONE = "phone"  # Phone number (E.164, formatted contact)
    ADDRESS = "address"  # Street address / physical location
    CITY = "city"  # City name
    STATE_REGION = "state_region"  # State, province, or region
    COUNTRY = "country"  # Country name or ISO code
    POSTAL_CODE = "postal_code"  # Postal / Zip code (preserves leading zeroes)
    FREE_TEXT = "free_text"  # Unstructured narrative, comments, descriptions
    CONSTANT = "constant"  # Single-value constant across all rows
    UNKNOWN = "unknown"  # Unclassified data


class AnalyticalRole(str, Enum):
    """
    Analytical role determining how a column should be used in modeling and visualizations.
    """

    MEASURE = "measure"  # Quantitative value suitable for aggregation (sum, mean, distribution)
    DEMOGRAPHIC_MEASURE = "demographic_measure"  # Numeric attribute describing an entity (e.g. age, experience)
    CATEGORICAL_DIMENSION = "categorical_dimension"  # Low-to-medium cardinality grouping attribute
    TEMPORAL_DIMENSION = "temporal_dimension"  # Time axis for trend and time-series analysis
    GEOGRAPHIC_DIMENSION = "geographic_dimension"  # Spatial location category (city, state, country)
    GEOGRAPHIC_IDENTIFIER = "geographic_identifier"  # Precise location code (postal code)
    CONTACT_IDENTIFIER = "contact_identifier"  # Communication detail (phone, email)
    IDENTIFIER = "identifier"  # Record-level unique key (excluded from aggregate charts)
    DESCRIPTIVE_ATTRIBUTE = "descriptive_attribute"  # Entity description (person name, street address, remarks)
    CONSTANT_ATTRIBUTE = "constant_attribute"  # Zero-variance column (excluded from charts)
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ColumnProfile:
    """
    Authoritative profile describing physical, semantic, and analytical attributes of a column.
    """

    column_name: str
    physical_dtype: str
    semantic_type: SemanticType
    analytical_role: AnalyticalRole
    missing_count: int
    missing_percentage: float
    non_null_count: int
    unique_count: int
    uniqueness_percentage: float
    cardinality_classification: str  # "constant", "binary", "low", "medium", "high", "unique"
    inference_confidence: float = 1.0  # 0.0 to 1.0 confidence score
    inferred_subtype: str | None = None
    is_visualizable: bool = True
    visualization_suitability: str = "auto"  # "distribution", "categories", "scatter", "trend", "excluded"
    governance_recommendation: str = "preserve_nulls"  # "preserve_nulls", "drop_rows", "impute_median", etc.

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        d = asdict(self)
        d["semantic_type"] = self.semantic_type.value
        d["analytical_role"] = self.analytical_role.value
        return d


@dataclass(frozen=True)
class DatasetProfile:
    """
    Complete dataset profiling result containing summary metrics and per-column profiles.
    """

    row_count: int
    column_count: int
    column_profiles: dict[str, ColumnProfile]
    memory_bytes: int = 0
    has_missing_values: bool = False
    total_missing_cells: int = 0
    overall_completeness_pct: float = 100.0
    semantic_counts: dict[str, int] = field(default_factory=dict)
    role_counts: dict[str, int] = field(default_factory=dict)

    def get_column(self, name: str) -> ColumnProfile | None:
        """Get profile for a specific column."""
        return self.column_profiles.get(name)

    def get_columns_by_role(self, role: AnalyticalRole) -> list[ColumnProfile]:
        """Get all columns matching an analytical role."""
        return [cp for cp in self.column_profiles.values() if cp.analytical_role == role]

    def get_columns_by_semantic_type(self, sem_type: SemanticType) -> list[ColumnProfile]:
        """Get all columns matching a semantic type."""
        return [cp for cp in self.column_profiles.values() if cp.semantic_type == sem_type]

    def get_visualizable_columns(self) -> list[ColumnProfile]:
        """Get all columns suitable for visualization."""
        return [cp for cp in self.column_profiles.values() if cp.is_visualizable]

    def get_columns_with_missing(self) -> list[ColumnProfile]:
        """Get all columns containing at least one missing value."""
        return [cp for cp in self.column_profiles.values() if cp.missing_count > 0]

    def to_dict(self) -> dict[str, Any]:
        """Convert dataset profile to dictionary."""
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "memory_bytes": self.memory_bytes,
            "has_missing_values": self.has_missing_values,
            "total_missing_cells": self.total_missing_cells,
            "overall_completeness_pct": self.overall_completeness_pct,
            "semantic_counts": self.semantic_counts,
            "role_counts": self.role_counts,
            "columns": {name: cp.to_dict() for name, cp in self.column_profiles.items()},
        }
