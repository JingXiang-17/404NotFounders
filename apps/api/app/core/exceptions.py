class LintasNiagaException(Exception):
    """Base exception for LintasNiaga."""


class IngestionError(LintasNiagaException):
    """Base class for ingestion and snapshot failures."""


class ExtractionFailed(IngestionError):
    pass


class ValidationFailed(IngestionError):
    pass


class ValidationError(ValidationFailed):
    """Raised when local data violates a contract."""


class UnsupportedScope(IngestionError):
    pass


class ExternalFetchFailed(IngestionError):
    pass


class ProviderError(ExternalFetchFailed):
    """Raised when an upstream provider fails."""


class DependencyNotAvailableError(IngestionError):
    """Raised when an optional runtime dependency is missing."""


class NormalizationFailed(IngestionError):
    pass


class SnapshotWriteFailed(IngestionError):
    pass


class SnapshotStaleUsingLastValid(IngestionError):
    pass


class NoValidQuotes(IngestionError):
    pass


class SingleValidQuoteFallback(IngestionError):
    pass


class ComputationFailed(IngestionError):
    pass


class AIReasoningFailedFallbackToDeterministic(IngestionError):
    pass
