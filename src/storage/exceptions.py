"""
Exceptions for artifact storage layer.
"""

from __future__ import annotations


class ArtifactStoreError(Exception):
    """Base exception for storage errors."""


class ChecksumMismatchError(ArtifactStoreError):
    """Raised when artifact bytes do not match expected checksum."""
