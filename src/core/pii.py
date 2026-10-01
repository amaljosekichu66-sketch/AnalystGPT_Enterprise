"""
Shared rule for deciding whether a column name denotes personal contact data.

Why this exists
---------------
Two layers independently masked columns by testing whether a PII keyword
appeared *anywhere* in the column name:

    src/llm/report_serializer.py     {"phone", "email", "ssn", ...}
    src/reporting/exporters/text_report_exporter.py   ... plus "id", "zip"

Substring matching is far too eager, and it cost real analytical content:

    email_subject           -> masked, because it contains "email"
    email_body_(outbound)   -> masked, because it contains "email"
    ai_-_email_summary      -> masked, because it contains "email"

None of those hold an email address; they hold what the ticket was about. They
were the three most informative columns in the dataset and the model never saw
any of them.

The "id" keyword in the text exporter was worse still:

    ai_-_classification_confidence  ->  "Masked identifier field"

because "confidence" contains the letters "id".

The rule
--------
A PII keyword must be the name's *subject*, not an incidental word in it. The
name is split into tokens; if a PII token is present and every remaining token
is a generic qualifier ("client", "primary", "address", ...), the column is
contact data. Any other token - "subject", "body", "summary", "confidence" -
means the column is about something else.

    client_email        -> {client} qualifies          -> PII
    email               -> nothing left                -> PII
    email_address       -> {address} qualifies         -> PII
    primary_phone_no    -> {primary, no} qualify       -> PII
    email_subject       -> {subject} does not          -> not PII
    ai_-_email_summary  -> {ai, summary} do not        -> not PII
    classification_confidence -> no PII token at all   -> not PII

This is a name-level heuristic and stays a backstop. The authoritative decision
is `SemanticClassifier`, which confirms against the values themselves.

P2-15 extended it: names, addresses, dates of birth, IP addresses and social
security numbers are personal data too (`full_name`, `date_of_birth`,
`ip_address`, `social_security_number` all used to read as safe), camelCase
is split (`EmailAddress`), and `values_look_like_pii` recognises e-mail
addresses, phone numbers, SSNs and IPv4 addresses from the values when the
name says nothing. `mask_pii_columns` blanks such columns in API views.
"""

from __future__ import annotations

import re

#: Tokens that name personal data directly.
PII_TOKENS = frozenset(
    {
        "name",
        "fullname",
        "firstname",
        "lastname",
        "surname",
        "address",
        "dob",
        "birth",
        "birthdate",
        "birthday",
        "ip",
        "ipaddress",
        "socialsecurity",
        "nationalid",
        "phone",
        "telephone",
        "mobile",
        "email",
        "mail",
        "ssn",
        "passport",
        "creditcard",
        "credit_card",
        "iban",
    }
)

#: Tokens that merely qualify a personal-data field without changing what it is.
#: Kept deliberately short: an unknown token means "not plain contact data",
#: which fails safe towards keeping analytical content visible while still
#: masking anything that reads as a contact column.
PII_QUALIFIER_TOKENS = frozenset(
    {
        "address",
        "addr",
        "no",
        "num",
        "number",
        "id",
        "primary",
        "secondary",
        "alternate",
        "alt",
        "work",
        "home",
        "personal",
        "business",
        "contact",
        "client",
        "customer",
        "user",
        "employee",
        "person",
        "account",
        "billing",
        "shipping",
        "1",
        "2",
        "",
        # names (P2-15)
        "full",
        "first",
        "last",
        "middle",
        "given",
        "family",
        "maiden",
        "legal",
        # addresses and dates of birth
        "street",
        "line",
        "mailing",
        "postal",
        "residential",
        "date",
        "of",
        "v4",
        "v6",
    }
)

_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def tokenize_column_name(column_name: str) -> list[str]:
    """Split a column name into comparable lowercase tokens; camelCase splits too (P2-15)."""
    spaced = _CAMEL_BOUNDARY.sub("_", str(column_name))
    return [token for token in _TOKEN_SPLIT.split(spaced.lower()) if token]


def is_contact_pii_column(column_name: str) -> bool:
    """
    Return True when the column name denotes personal contact data.

    Parameters
    ----------
    column_name:
        Raw column name, in any casing or separator style.
    """
    tokens = tokenize_column_name(column_name)

    if not tokens:
        return False

    # Indices consumed by a PII match, so "credit_card" is recognised the same
    # way as "creditcard" and neither half is then left over as an unknown
    # token.
    consumed: set[int] = set()

    for index, token in enumerate(tokens):
        if token in PII_TOKENS:
            consumed.add(index)

    for index in range(len(tokens) - 1):
        if tokens[index] + tokens[index + 1] in PII_TOKENS:
            consumed.update({index, index + 1})

    if not consumed:
        return False

    remaining = [
        token for index, token in enumerate(tokens) if index not in consumed and token not in PII_QUALIFIER_TOKENS
    ]

    return not remaining


# ==========================================================
# Value-based detection and masking (P2-15)
# ==========================================================

_VALUE_PATTERNS = (
    re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.IGNORECASE),  # e-mail
    re.compile(r"^\+?[\d\s().-]{7,20}$"),  # phone (checked for digit count below)
    re.compile(r"^\d{3}-\d{2}-\d{4}$"),  # US social security number
    re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$"),  # IPv4 address
)

#: Share of sampled text values that must match one pattern.
VALUE_MATCH_THRESHOLD = 0.8
_SAMPLE_SIZE = 200

MASK = "<masked personal data>"


def _matches_pattern(value: str, pattern: re.Pattern[str]) -> bool:
    if not pattern.match(value):
        return False
    if pattern is _VALUE_PATTERNS[1]:
        digits = sum(ch.isdigit() for ch in value)
        return 7 <= digits <= 15
    return True


def values_look_like_pii(values) -> bool:
    """
    True when most sampled TEXT values are e-mail addresses, phone numbers,
    SSNs or IPv4 addresses. Numbers are ignored: a numeric measure is not a
    phone number.
    """
    sample = [str(v).strip() for v in list(values)[:_SAMPLE_SIZE] if isinstance(v, str) and str(v).strip()]
    if len(sample) < 3:
        return False
    for pattern in _VALUE_PATTERNS:
        hits = sum(_matches_pattern(value, pattern) for value in sample)
        if hits / len(sample) >= VALUE_MATCH_THRESHOLD:
            return True
    return False


def is_pii_column(column_name: str, values=None) -> bool:
    """Name rule, then (when values are given) the value rule."""
    if is_contact_pii_column(column_name):
        return True
    return values is not None and values_look_like_pii(values)


def mask_pii_columns(analytics):
    """
    Copy an analytics mapping with every PII-named column's content masked.

    Analytics sections are keyed by column name at varying depths; a key that
    names personal data keeps its place (so the column is still listed) but
    its statistics - top values, distributions - are replaced. Only for
    column-keyed analytics: generic payloads have keys like "name" too.
    """
    if isinstance(analytics, dict):
        return {
            key: (MASK if isinstance(key, str) and is_contact_pii_column(key) else mask_pii_columns(value))
            for key, value in analytics.items()
        }
    if isinstance(analytics, list):
        return [mask_pii_columns(item) for item in analytics]
    return analytics
