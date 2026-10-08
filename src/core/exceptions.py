"""
Custom exceptions used throughout AnalystGPT Enterprise.

Each business module should derive its own exceptions
from AnalystGPTError.
"""

# ==========================================================
# Base Exception
# ==========================================================


class AnalystGPTError(Exception):
    """
    Base exception for AnalystGPT Enterprise.
    """

    pass


# ==========================================================
# Upload Exceptions
# ==========================================================


class UnsupportedFileTypeError(AnalystGPTError):
    """
    Raised when an unsupported file type is uploaded.
    """

    pass


class FileReadError(AnalystGPTError):
    """
    Raised when a supported file cannot be read.
    """

    pass


class SourceFileNotFoundError(AnalystGPTError):
    """
    Raised when the specified source file does not exist.
    """

    pass


class TooManyConcurrentJobsError(AnalystGPTError):
    """
    Raised when a user already has the maximum number of heavy jobs (uploads
    being parsed, pipeline runs) in progress (SEC-10).
    """

    pass


class PipelineResultNotFoundError(AnalystGPTError):
    """
    Raised when a read-only view is requested for a dataset that has not been
    processed yet. Views never execute the pipeline to fill the gap.
    """

    pass


class DatasetNotFoundError(AnalystGPTError):
    """
    Raised when a dataset identifier does not resolve to a source dataset the
    caller may use. Unknown and foreign identifiers are deliberately
    indistinguishable.
    """

    pass


# ==========================================================
# Identity & Security Exceptions (Sprint 13)
# ==========================================================
