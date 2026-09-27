"""Custom exceptions for the Student Record Manager system."""


class StudentRecordException(Exception):
    """Base exception for all Student Record Manager errors."""
    pass


class InvalidEmailError(StudentRecordException):
    """Raised when an email address fails regex format validation."""

    def __init__(self, email: str, message: str = "Invalid email format"):
        self.email = email
        self.message = f"{message}: '{email}'. Expected format: name@domain.com"
        super().__init__(self.message)


class InvalidInputError(StudentRecordException):
    """Raised when general user input is malformed or invalid."""

    def __init__(self, field: str, value: str, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        self.message = f"Invalid value for '{field}' ('{value}'): {reason}"
        super().__init__(self.message)


class DuplicateStudentError(StudentRecordException):
    """Raised when attempting to add a student with an ID that already exists."""

    def __init__(self, student_id: str):
        self.student_id = student_id
        self.message = f"Student with ID '{student_id}' already exists."
        super().__init__(self.message)


class StudentNotFoundError(StudentRecordException):
    """Raised when a requested student cannot be found in the records."""

    def __init__(self, student_id: str):
        self.student_id = student_id
        self.message = f"Student with ID '{student_id}' was not found."
        super().__init__(self.message)


class StorageError(StudentRecordException):
    """Raised when persistent file storage operations fail."""

    def __init__(self, filepath: str, operation: str, details: str):
        self.filepath = filepath
        self.operation = operation
        self.details = details
        self.message = f"Failed to {operation} storage file '{filepath}': {details}"
        super().__init__(self.message)
