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


class FileTooLargeError(AnalystGPTError):
    """
    Raised when the uploaded file exceeds the configured size limit.
    """
    pass