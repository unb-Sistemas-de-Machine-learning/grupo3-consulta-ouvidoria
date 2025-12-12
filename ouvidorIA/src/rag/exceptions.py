"""Custom exceptions for RAG operations."""


class RAGServiceError(Exception):
    """Base exception for RAG service errors."""
    pass


class LLMConnectionError(RAGServiceError):
    """Raised when LLM connection fails."""
    pass


class QueryEngineNotReadyError(RAGServiceError):
    """Raised when query engine is not initialized."""
    pass


class IndexNotReadyError(RAGServiceError):
    """Raised when index is not available."""
    pass


class IndexingError(RAGServiceError):
    """Raised when document indexing fails."""
    pass
