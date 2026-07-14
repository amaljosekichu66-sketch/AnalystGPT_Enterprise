"""
Custom exceptions for AnalystGPT Enterprise.
"""


class AnalystGPTError(Exception):
    """Base exception for AnalystGPT Enterprise."""
    pass


class UnsupportedFileTypeError(AnalystGPTError):
    """Raised when an unsupported file type is uploaded."""
    pass