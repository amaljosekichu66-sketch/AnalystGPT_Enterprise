"""
Keep server filesystem paths out of API responses.

Internal artifacts (uploaded datasets, generated reports) live at server
paths that clients have no business knowing. Responses carry a bare file
name at most, and free-text error messages are scrubbed of anything that
looks like an absolute path before they are returned.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath, PureWindowsPath

REDACTED_PATH = "<server-path>"

_PATH_PATTERN = re.compile(
    r"""
      \\\\[^\s'"<>|]+                           # UNC: \\host\share\...
    | (?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s'"<>|]*   # Windows drive: C:\... or C:/...
    | (?<![\w.:/])/(?:app|etc|home|root|tmp|var|usr|opt|mnt|srv|proc|data|private|Users)
      (?:/[^\s'"<>|]*)?                         # POSIX absolute under a real root
    """,
    re.VERBOSE,
)


def redact_server_paths(text: str | None) -> str | None:
    """Replace absolute filesystem paths in free text with a placeholder."""
    if not text:
        return text
    return _PATH_PATTERN.sub(REDACTED_PATH, text)


def public_artifact_name(path: str | None) -> str | None:
    """Reduce a server artifact path to its bare file name."""
    if not path:
        return None
    return PurePosixPath(PureWindowsPath(str(path)).name).name or None


def public_report_dict(report: dict | None) -> dict:
    """Copy a `ReportingReport.to_dict()` payload with its export path reduced to a file name."""
    public = dict(report or {})
    if "export_path" in public:
        public["export_path"] = public_artifact_name(public["export_path"])
    return public
