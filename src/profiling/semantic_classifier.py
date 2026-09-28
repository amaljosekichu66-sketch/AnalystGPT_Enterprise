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

# ==========================================================
# Numeric identifier detection
# ==========================================================
#
# A record key stored as an integer is numeric by dtype and meaningless as a
# measure. Left undetected, `ticket_#` (27,945 rows, every value distinct,
# 99.88% of sorted gaps equal to 1) was classified `numeric_measure` /
# `MEASURE`, which then published a mean ticket number as a business
# statistic, offered an "impute median" governance policy for a primary key,
# and handed the model a skewness and kurtosis to narrate.
#
# The discriminator is *density*, not uniqueness alone. A genuine measure can
# happen to be fully distinct; what it does not do is tile a contiguous
# integer range with no gaps. Requiring both keeps real measures safe.

#: Below this many distinct values the evidence is too thin to be confident.
_IDENTIFIER_MIN_DISTINCT = 100

#: Practically every row distinct.
_IDENTIFIER_MIN_UNIQUENESS = 0.99

#: distinct values / (max - min + 1). A perfect auto-increment run scores 1.0.
_IDENTIFIER_MIN_DENSITY = 0.90


def _is_sequential_identifier(
    numeric_values: pd.Series,
    unique_count: int,
    uniqueness_ratio: float,
) -> bool:
    """
    Return True when numeric values behave like a sequential record key.

    Requires all four signals to agree:

    1. enough distinct values to judge (`_IDENTIFIER_MIN_DISTINCT`),
    2. effectively one value per row (`_IDENTIFIER_MIN_UNIQUENESS`),
    3. whole numbers only - a fractional value rules out a counter,
    4. the values densely tile an integer range (`_IDENTIFIER_MIN_DENSITY`).

    Condition 4 is what separates a key from a measure that merely happens to
    be distinct: revenue figures scattered over a wide range score near zero,
    while an auto-increment column scores close to 1.

    Deliberately conservative. A sparse unique integer key (a random account
    number, say) is not caught here and stays a measure unless its *name*
    matches `ID_KEYWORDS`. Widening this needs evidence that real measures are
    not caught with it.
    """
    if numeric_values.empty:
        return False

    if unique_count < _IDENTIFIER_MIN_DISTINCT:
        return False

    if uniqueness_ratio < _IDENTIFIER_MIN_UNIQUENESS:
        return False

    try:
        if not bool((numeric_values % 1 == 0).all()):
            return False

        minimum = float(numeric_values.min())
        maximum = float(numeric_values.max())
    except (TypeError, ValueError):
        return False

    span = maximum - minimum + 1.0

    if span <= 0:
        return False

    return (unique_count / span) >= _IDENTIFIER_MIN_DENSITY


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

    #: Above this mean character length a column is prose, not a contact
    #: detail. The longest realistic email address in practice is well under
    #: this; the misclassified narrative columns averaged 432 and 627.
    FREE_TEXT_MEAN_LENGTH = 60

    @staticmethod
    def _holds_free_text(non_null_series: pd.Series) -> bool:
        """Return True when the column's values are long enough to be prose."""
        if non_null_series.empty:
            return False

        try:
            sample = non_null_series.iloc[:200].astype(str)
            return bool(sample.str.len().mean() > SemanticClassifier.FREE_TEXT_MEAN_LENGTH)
        except (TypeError, ValueError):
            return False

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

        # A contact detail is short by construction: an email address, a phone
        # number and a postal code are all well under 60 characters. Long prose
        # is therefore decisive counter-evidence, whatever the column is named.
        #
        # This is what stops a *_email_* / *_phone_* / *_zip_* keyword from
        # capturing a narrative column. `ai_-_email_summary` averaged 432
        # characters and `email_body_(outbound)` 627; both were being reported
        # as contact identifiers, excluded from analysis and masked from the
        # prompt.
        holds_free_text = self._holds_free_text(non_null_series)

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
        if not holds_free_text and any(k in col_normalized for k in self.PHONE_KEYWORDS):
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
        if not holds_free_text and any(k in col_normalized for k in self.POSTAL_KEYWORDS):
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
        #
        # The name is a hypothesis, never a verdict. Matching "mail" as a bare
        # substring classified `email_subject`, `email_body_(outbound)` and
        # `ai_-_email_summary` as email addresses - measured at 0.2%, 0.0% and
        # 0.0% actual address content, with mean lengths of 48, 627 and 432
        # characters. All three were then excluded from analysis AND masked out
        # of the AI prompt, which removed the only columns describing what each
        # ticket was actually about.
        #
        # So the keyword now only decides how much value-level agreement to
        # demand, and never substitutes for it.
        is_text_like = non_null_count > 0 and (
            pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series)
        )

        if is_text_like:
            name_suggests_email = not holds_free_text and any(k in col_normalized for k in self.EMAIL_KEYWORDS)
            sample = [str(x).strip() for x in non_null_series.iloc[:30]]
            email_matches = sum(1 for s in sample if _EMAIL_REGEX.match(s))
            match_ratio = (email_matches / len(sample)) if sample else 0.0

            # A supporting name lowers the bar; it never removes it.
            required_ratio = 0.5 if name_suggests_email else 0.8

            if sample and match_ratio >= required_ratio:
                return (
                    SemanticType.EMAIL,
                    AnalyticalRole.CONTACT_IDENTIFIER,
                    0.98 if name_suggests_email else 0.95,
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

                # A numeric dtype is a storage fact, not a semantic one. A
                # record key stored as int64 is still a key: aggregating it,
                # charting its distribution or imputing its median are all
                # meaningless. Decide on the measured shape of the values -
                # never on the column name - before accepting it as a measure.
                if _is_sequential_identifier(
                    numeric_vals,
                    unique_count=unique_count,
                    uniqueness_ratio=uniqueness_ratio,
                ):
                    return (
                        SemanticType.IDENTIFIER,
                        AnalyticalRole.IDENTIFIER,
                        0.95,
                        card_class,
                        "excluded",
                        "preserve_nulls",
                    )

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

        # 11a. Prose is prose regardless of how often it repeats.
        #
        # The uniqueness gate below asks for >= 0.80 before it will consider
        # free text, which left `email_body_(outbound)` (627 characters per
        # value, 46.6% distinct) classified as a CATEGORICAL_DIMENSION - a
        # "dimension" with roughly 13,000 categories, each a paragraph long.
        # Length alone settles it.
        if holds_free_text and unique_count > 100:
            return (
                SemanticType.FREE_TEXT,
                AnalyticalRole.DESCRIPTIVE_ATTRIBUTE,
                0.85,
                card_class,
                "excluded",
                "preserve_nulls",
            )

        # 11. High Cardinality Categorical / Free Text vs Categorical Dimension
        if uniqueness_ratio >= 0.80 and unique_count > 100:
            if holds_free_text:
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
