"""Custom exceptions for ETL operations."""


class DocumentLoaderError(Exception):
    """Base exception for document loading errors."""
    pass


class NoDocumentsFoundError(DocumentLoaderError):
    """Raised when no documents are found in any source."""
    pass


class DocumentProcessingError(DocumentLoaderError):
    """Raised when there's an error processing documents."""
    pass


class InvalidFileTypeError(DocumentLoaderError):
    """Raised when an invalid file type is provided."""
    pass


class ETLProcessError(Exception):
    """Base exception for ETL process errors."""
    pass

class ETLStateError(Exception):
    """Base exception for ETL State errors."""
    pass