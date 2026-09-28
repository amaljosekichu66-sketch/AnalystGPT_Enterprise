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
"""

from __future__ import annotations

import re

#: Tokens that name personal contact data directly.
PII_TOKENS = frozenset(
    {
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

#: Tokens that merely qualify a contact field without changing what it is.
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
    }
)

_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")


def tokenize_column_name(column_name: str) -> list[str]:
    """Split a column name into comparable lowercase tokens."""
    return [token for token in _TOKEN_SPLIT.split(str(column_name).lower()) if token]


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
