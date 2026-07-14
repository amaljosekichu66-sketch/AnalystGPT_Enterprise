"""
Custom exceptions for AnalystGPT Enterprise.
"""


class AnalystGPTError(Exception):
    """Base exception for AnalystGPT Enterprise."""
    pass


class UnsupportedFileTypeError(AnalystGPTError):
    """Raised when an unsupported file type is uploaded."""
    pass


class FileReadError(AnalystGPTError):
    """Raised when a supported file cannot be read."""
    pass


class SourceFileNotFoundError(AnalystGPTError):
    """Raised when the specified source file does not exist."""
    pass


class FileTooLargeError(AnalystGPTError):
    """Raised when the uploaded file exceeds the configured size limit."""
    pass