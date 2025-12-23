"""Custom exception classes for BookBrain."""


class BookBrainError(Exception):
    """Base exception for BookBrain."""

    pass


class BookError(BookBrainError):
    """Base exception for book-related errors."""

    pass


class BookNotFoundError(BookError):
    """Raised when a book is not found."""

    def __init__(self, book_id: int) -> None:
        self.book_id = book_id
        super().__init__(f"Book not found: {book_id}")


class BookCreationError(BookError):
    """Raised when book creation fails."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        self.cause = cause
        super().__init__(message)


class DuplicateBookError(BookError):
    """Raised when attempting to create a duplicate book."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        super().__init__(f"Book already exists with file_path: {file_path}")


class VectorError(BookBrainError):
    """Base exception for vector-related errors."""

    pass


class VectorStorageError(VectorError):
    """Raised when vector storage fails."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        self.cause = cause
        super().__init__(message)


class DatabaseError(BookBrainError):
    """Base exception for database-related errors."""

    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


class ParserError(BookBrainError):
    """Base exception for parser-related errors."""

    pass


class StormParseAPIError(ParserError):
    """Raised when Storm Parse API call fails."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self.cause = cause
        super().__init__(message)


class PDFReadError(ParserError):
    """Raised when PDF file reading fails."""

    def __init__(self, file_path: str, cause: Exception | None = None) -> None:
        self.file_path = file_path
        self.cause = cause
        super().__init__(f"Failed to read PDF file: {file_path}")
