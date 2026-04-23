class LintasNiagaException(Exception):
    """Base exception for LintasNiaga"""
    pass

class ExtractionFailed(LintasNiagaException):
    pass

class ValidationFailed(LintasNiagaException):
    pass

class UnsupportedScope(LintasNiagaException):
    pass

class ExternalFetchFailed(LintasNiagaException):
    pass

class NormalizationFailed(LintasNiagaException):
    pass

class SnapshotWriteFailed(LintasNiagaException):
    pass

class SnapshotStaleUsingLastValid(LintasNiagaException):
    pass

class NoValidQuotes(LintasNiagaException):
    pass

class SingleValidQuoteFallback(LintasNiagaException):
    pass

class ComputationFailed(LintasNiagaException):
    pass

class AIReasoningFailedFallbackToDeterministic(LintasNiagaException):
    pass
