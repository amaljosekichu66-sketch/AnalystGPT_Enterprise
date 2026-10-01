"""
Readable messages for failed API calls (P2-08).

`APIClient` raises `RuntimeError("Backend returned HTTP <code>: <detail>")`,
`"Unable to connect to backend: ..."` or `"Backend request timed out..."`.
Pages used to show that text verbatim - raw "HTTP 422: {json}" on login - or
let it escape as a traceback. `friendly_error` turns it into one sentence a
user can act on; the original goes to the log.
"""

from __future__ import annotations

import re

from src.core.logger import logger

_HTTP = re.compile(r"HTTP (\d{3}): ?(.*)", re.S)

_BY_STATUS = {
    400: None,  # the API's own message is already user-facing (e.g. password policy)
    401: "Your session has expired. Please sign in again.",
    403: "You do not have permission to do this.",
    404: "That item was not found. It may have been deleted, or it belongs to another account.",
    409: None,
    411: "The upload did not declare its size. Please try again.",
    413: "The file or request is too large.",
    415: "This file type is not supported.",
    422: "Some of the details are not in the expected format. Please check them and try again.",
    429: "Too many requests or jobs in progress. Wait a moment and try again.",
}

UNAVAILABLE = "The analytics service is not reachable right now. Please try again shortly."


def http_status(error: Exception | str) -> int | None:
    match = _HTTP.search(str(error))
    return int(match.group(1)) if match else None


def friendly_error(error: Exception | str, context: str = "request") -> str:
    """One readable sentence for a failed API call; the raw text is logged."""
    text = str(error)
    logger.warning("Frontend %s failed: %s", context, text)

    if "Unable to connect" in text or "timed out" in text.lower() or "ConnectError" in text:
        return UNAVAILABLE

    match = _HTTP.search(text)
    if match is None:
        return f"The {context} could not be completed. Please try again."

    status, detail = int(match.group(1)), match.group(2).strip()
    message = _BY_STATUS.get(status)
    if message is not None:
        return message
    if status in (400, 409) and detail and len(detail) <= 200 and not detail.startswith(("{", "[")):
        return detail
    if status >= 500:
        return f"The {context} failed on the server. Please try again; if it keeps failing, contact an administrator."
    return f"The {context} could not be completed. Please try again."
