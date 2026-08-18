"""
AI subsystem exceptions for AnalystGPT Enterprise.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations


class AIError(Exception):
    """Base exception for all AI subsystem errors."""


class AIJobNotFoundError(AIError):
    """Raised when a requested AI job cannot be found."""


class AIStateTransitionError(AIError):
    """Raised when an invalid state transition is attempted on an AI job."""


class AIRetryableError(AIError):
    """Raised when a transient failure occurs that can be safely retried."""


class AINonRetryableError(AIError):
    """Raised when a fatal or permanent failure occurs that cannot be retried."""
