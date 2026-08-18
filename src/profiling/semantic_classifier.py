"""
Semantic Classifier for Column Data Types and Analytical Roles.

Provides deterministic pattern- and heuristic-based classification to distinguish
physical storage representations (e.g. object/string) from domain semantics (e.g.
phone numbers, postal codes, continuous numeric measures, identifiers, or categories).

Sprint 14 Remediation — Data Profiling, Null Governance & Visual Analytics.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import pandas as pd

from src.profiling.models import AnalyticalRole, SemanticType

# Regex patterns for deterministic recognition
_EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")
_PHONE_REGEX = re.compile(r"^(\+?\d{1,3}[\s\-\.]?)?(\(?\d{2,4}\)?[\s\-\.]?)?\d{3,4}[\s\-\.]?\d{3,4}$")
_UUID_REGEX = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_HEX_HASH_REGEX = re.compile(r"^[0-9a-fA-F]{32,64}$")
_US_ZIP_REGEX = re.compile(r"^\d{5}(-\d{4})?$")
_UK_POSTAL_REGEX = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$", re.IGNORECASE)
_CANADIAN_POSTAL_REGEX = re.compile(r"^[A-Z]\d[A-Z]\s*\d[A-Z]\d$", re.IGNORECASE)
_NUMERIC_STRING_REGEX = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
_CURRENCY_STRING_REGEX = re.compile(r"^[\$€£¥₹]?\s*[+-]?\d+(,\d{3})*(\.\d+)?$")


class SemanticClassifier:
    """
    Deterministic classifier inferring semantic types and analytical roles from column metadata and values.
    """

    # Name-based keywords
    PHONE_KEYWORDS = {"phone", "mobile", "cell", "telephone", "tel", "fax", "contact_no", "contact_number"}
    POSTAL_KEYWORDS = {"zip", "zipcode", "zip_code", "postal", "postal_code", "postcode", "pincode"}
    EMAIL_KEYWORDS = {"email", "e_mail", "email_address", "mail"}
    NAME_KEYWORDS = {
        "first_name",
        "last_name",
        "firstname",
        "lastname",
        "fullname",
        "full_name",
        "client_name",
        "customer_name",
        "author",
        "employee_name",
        "user_name",
        "middle_name",
        "surname",
        "given_name",
        "fname",
        "lname",
    }
    ADDRESS_KEYWORDS = {"address", "street", "addr", "line1", "line2", "address_line_1", "address_line_2"}
    CITY_KEYWORDS = {"city", "town", "municipality"}
    STATE_KEYWORDS = {"state", "province", "region", "territory"}
    COUNTRY_KEYWORDS = {"country", "nation", "country_code"}
    ID_KEYWORDS = {"id", "uuid", "guid", "key", "identifier", "unique_data", "pk", "fk", "token", "hash", "code"}
    DATE_KEYWORDS = {
        "date",
        "dob",
        "birth_date",
        "created_date",
        "updated_date",
        "timestamp",
        "datetime",
        "created_at",
        "updated_at",
        "deleted_at",
    }
    BOOLEAN_VALUES = {"true", "false", "yes", "no", "y", "n", "t", "f", "1", "0", "active", "inactive"}

    def classify_column(
        self,
        column_name: str,
        series: pd.Series,
        total_rows: int,
    ) -> tuple[SemanticType, AnalyticalRole, float, str, str, str]:
        """
        Classify a column and return:
        (semantic_type, analytical_role, confidence, cardinality_class, visual_suitability, governance_rec)
        """
        non_null_series = series.dropna()
        non_null_count = len(non_null_series)
        unique_count = int(non_null_series.nunique())
        col_normalized = column_name.strip().lower().replace(" ", "_").replace("-", "_")

        # 1. Constant Column Check (Zero variance)
        if unique_count <= 1:
            return (
                SemanticType.CONSTANT,
                AnalyticalRole.CONSTANT_ATTRIBUTE,
                1.0,
                "constant",
                "excluded",
                "drop_rows" if non_null_count == 0 else "preserve_nulls",
            )

        # Compute uniqueness ratio
        uniqueness_ratio = unique_count / non_null_count if non_null_count > 0 else 0.0

        # Cardinality Classification
        if unique_count == 2:
            card_class = "binary"
        elif unique_count <= 10:
            card_class = "low"
        elif unique_count <= 50:
            card_class = "medium"
        elif uniqueness_ratio >= 0.95 or unique_count > 500:
            card_class = "unique" if uniqueness_ratio == 1.0 else "high"
        else:
            card_class = "high"

        # 2. Boolean Physical or Semantic Check
        if pd.api.types.is_bool_dtype(series):
            return (
                SemanticType.BOOLEAN,
                AnalyticalRole.CATEGORICAL_DIMENSION,
                1.0,
                "binary",
                "categories",
                "preserve_nulls",
            )

        if non_null_count > 0 and unique_count == 2:
            str_vals = {str(v).strip().lower() for v in non_null_series.iloc[:100]}
            if str_vals.issubset(self.BOOLEAN_VALUES):
                return (
                    SemanticType.BOOLEAN,
                    AnalyticalRole.CATEGORICAL_DIMENSION,
                    0.95,
                    "binary",
                    "categories",
                    "preserve_nulls",
                )

        # 3. Datetime / Timestamp Check
        if pd.api.types.is_datetime64_any_dtype(series):
            return (
                SemanticType.DATETIME,
                AnalyticalRole.TEMPORAL_DIMENSION,
                1.0,
                card_class,
                "trend",
                "preserve_nulls",
            )

        if (
            any(col_normalized.endswith(k) or col_normalized == k for k in self.DATE_KEYWORDS)
            or "date" in col_normalized
            or "time" in col_normalized
        ):
            if non_null_count > 0:
                sample = [str(x).strip() for x in non_null_series.iloc[:20]]
                parse_count = 0
                for s in sample:
                    try:
                        datetime.fromisoformat(s.replace("Z", "+00:00"))
                        parse_count += 1
                    except Exception:
                        if re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}", s):
                            parse_count += 1
                if sample and parse_count / len(sample) >= 0.75:
                    return (
                        (
                            SemanticType.DATETIME
                            if "time" in col_normalized or "timestamp" in col_normalized
                            else SemanticType.DATE
                        ),
                        AnalyticalRole.TEMPORAL_DIMENSION,
                        0.9,
                        card_class,
                        "trend",
                        "preserve_nulls",
                    )

        # 4. Phone Numbers (Explicit Heuristic & Pattern Check)
        if any(k in col_normalized for k in self.PHONE_KEYWORDS):
            return (
                SemanticType.PHONE,
                AnalyticalRole.CONTACT_IDENTIFIER,
                0.98,
                card_class,
                "excluded",
                "preserve_nulls",
            )

        if non_null_count > 0 and (pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series)):
            sample = [str(x).strip() for x in non_null_series.iloc[:30]]
            phone_matches = sum(1 for s in sample if _PHONE_REGEX.match(s) and sum(c.isdigit() for c in s) >= 7)
            if sample and (phone_matches / len(sample)) >= 0.8:
                return (
                    SemanticType.PHONE,
                    AnalyticalRole.CONTACT_IDENTIFIER,
                    0.90,
                    card_class,
                    "excluded",
                    "preserve_nulls",
                )

        # 5. Postal Codes (Leading Zero & Format Heuristic)
        if any(k in col_normalized for k in self.POSTAL_KEYWORDS):
            return (
                SemanticType.POSTAL_CODE,
                AnalyticalRole.GEOGRAPHIC_IDENTIFIER,
                0.98,
                card_class,
                "categories",
                "preserve_nulls",
            )

        if non_null_count > 0 and (pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series)):
            sample = [str(x).strip() for x in non_null_series.iloc[:30]]
            zip_matches = sum(
                1
                for s in sample
                if _US_ZIP_REGEX.match(s) or _UK_POSTAL_REGEX.match(s) or _CANADIAN_POSTAL_REGEX.match(s)
            )
            if sample and (zip_matches / len(sample)) >= 0.85:
                return (
                    SemanticType.POSTAL_CODE,
                    AnalyticalRole.GEOGRAPHIC_IDENTIFIER,
                    0.88,
                    card_class,
                    "categories",
                    "preserve_nulls",
                )

        # 6. Emails
        if any(k in col_normalized for k in self.EMAIL_KEYWORDS):
            return (
                SemanticType.EMAIL,
                AnalyticalRole.CONTACT_IDENTIFIER,
                0.98,
                card_class,
                "excluded",
                "preserve_nulls",
            )

        if non_null_count > 0 and (pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series)):
            sample = [str(x).strip() for x in non_null_series.iloc[:30]]
            email_matches = sum(1 for s in sample if _EMAIL_REGEX.match(s))
            if sample and (email_matches / len(sample)) >= 0.8:
                return (
                    SemanticType.EMAIL,
                    AnalyticalRole.CONTACT_IDENTIFIER,
                    0.95,
                    card_class,
                    "excluded",
                    "preserve_nulls",
                )

        # 7. Person Names & Addresses
        if any(k == col_normalized or k in col_normalized.split("_") for k in self.NAME_KEYWORDS):
            return (
                SemanticType.PERSON_NAME,
                AnalyticalRole.DESCRIPTIVE_ATTRIBUTE,
                0.95,
                card_class,
                "excluded",
                "preserve_nulls",
            )

        if any(k in col_normalized for k in self.ADDRESS_KEYWORDS):
            return (
                SemanticType.ADDRESS,
                AnalyticalRole.DESCRIPTIVE_ATTRIBUTE,
                0.95,
                card_class,
                "excluded",
                "preserve_nulls",
            )

        # 8. City, State, Country Dimensions
        if any(k in col_normalized for k in self.CITY_KEYWORDS) or col_normalized == "city":
            return (
                SemanticType.CITY,
                AnalyticalRole.GEOGRAPHIC_DIMENSION,
                0.95,
                card_class,
                "categories",
                "impute_categorical",
            )

        if any(k in col_normalized for k in self.STATE_KEYWORDS) or col_normalized in {"state", "st"}:
            return (
                SemanticType.STATE_REGION,
                AnalyticalRole.GEOGRAPHIC_DIMENSION,
                0.95,
                card_class,
                "categories",
                "impute_categorical",
            )

        if any(k in col_normalized for k in self.COUNTRY_KEYWORDS) or col_normalized == "country":
            return (
                SemanticType.COUNTRY,
                AnalyticalRole.GEOGRAPHIC_DIMENSION,
                0.95,
                card_class,
                "categories",
                "impute_categorical",
            )

        # 9. Identifiers (UUIDs, Hashes, System IDs, Unique Data)
        if any(
            col_normalized == k or col_normalized.endswith(f"_{k}") or col_normalized.startswith(f"{k}_")
            for k in self.ID_KEYWORDS
        ):
            if uniqueness_ratio >= 0.7 or card_class in {"unique", "high"}:
                return (
                    SemanticType.IDENTIFIER,
                    AnalyticalRole.IDENTIFIER,
                    0.95,
                    card_class,
                    "excluded",
                    "drop_rows" if uniqueness_ratio == 1.0 else "preserve_nulls",
                )

        if non_null_count > 0 and (pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series)):
            sample = [str(x).strip() for x in non_null_series.iloc[:30]]
            uuid_matches = sum(1 for s in sample if _UUID_REGEX.match(s) or _HEX_HASH_REGEX.match(s))
            if sample and (uuid_matches / len(sample)) >= 0.8:
                return (
                    SemanticType.IDENTIFIER,
                    AnalyticalRole.IDENTIFIER,
                    0.95,
                    card_class,
                    "excluded",
                    "preserve_nulls",
                )

        # 10. Physical Numeric Check vs String-Encoded Numeric
        is_phys_numeric = pd.api.types.is_numeric_dtype(series)

        if (
            not is_phys_numeric
            and non_null_count > 0
            and (pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series))
        ):
            # Test if column values are numeric strings (e.g. "123.45", "4500", "$50.00")
            sample = [str(x).strip() for x in non_null_series.iloc[:50]]
            num_matches = 0
            for s in sample:
                cleaned_num = (
                    s.replace("$", "")
                    .replace("€", "")
                    .replace("£", "")
                    .replace("¥", "")
                    .replace("₹", "")
                    .replace(",", "")
                    .strip()
                )
                if _NUMERIC_STRING_REGEX.match(cleaned_num):
                    num_matches += 1
            if sample and (num_matches / len(sample)) >= 0.90:
                is_phys_numeric = True

        if is_phys_numeric:
            try:
                numeric_vals = pd.to_numeric(
                    non_null_series.astype(str).str.replace(r"[\$,€,£,¥,₹]", "", regex=True).str.replace(",", ""),
                    errors="coerce",
                ).dropna()
                if not numeric_vals.empty:
                    is_all_int = (numeric_vals % 1 == 0).all()
                    if is_all_int and (
                        col_normalized in {"age", "quantity", "units", "count", "items", "score", "tenure"}
                        or unique_count <= 100
                    ):
                        return (
                            SemanticType.NUMERIC_DISCRETE,
                            AnalyticalRole.DEMOGRAPHIC_MEASURE if "age" in col_normalized else AnalyticalRole.MEASURE,
                            0.90,
                            card_class,
                            "distribution",
                            "impute_median",
                        )
            except Exception:
                pass

            return (
                SemanticType.NUMERIC_MEASURE,
                AnalyticalRole.MEASURE,
                0.95,
                card_class,
                "distribution",
                "impute_median",
            )

        # 11. High Cardinality Categorical / Free Text vs Categorical Dimension
        if uniqueness_ratio >= 0.80 and unique_count > 100:
            avg_len = non_null_series.astype(str).str.len().mean() if non_null_count > 0 else 0
            if avg_len > 60:
                return (
                    SemanticType.FREE_TEXT,
                    AnalyticalRole.DESCRIPTIVE_ATTRIBUTE,
                    0.85,
                    card_class,
                    "excluded",
                    "preserve_nulls",
                )
            return (
                SemanticType.IDENTIFIER,
                AnalyticalRole.IDENTIFIER,
                0.75,
                card_class,
                "excluded",
                "preserve_nulls",
            )

        # 12. Standard Categorical Dimension
        return (
            SemanticType.CATEGORICAL,
            AnalyticalRole.CATEGORICAL_DIMENSION,
            0.85,
            card_class,
            "categories" if card_class in {"binary", "low", "medium"} else "excluded",
            "impute_categorical",
        )
