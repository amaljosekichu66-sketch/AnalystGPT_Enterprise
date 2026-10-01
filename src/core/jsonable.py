"""
Convert analysis results (numpy scalars and arrays, datetimes) to plain JSON types.
"""

from __future__ import annotations

from typing import Any


def to_jsonable(value: Any) -> Any:
    """Recursively turn `value` into dict / list / str / int / float / bool / None."""
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if hasattr(value, "tolist"):
        return to_jsonable(value.tolist())
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
