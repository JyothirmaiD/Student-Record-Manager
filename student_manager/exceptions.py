"""Custom Exception Hierarchy for Student Record Manager.

Defines domain-specific and validation exceptions for granular error handling.
"""


class StudentRecordError(Exception):
    """Base exception for all Student Record Manager errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v!r}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class ValidationError(StudentRecordError):
    """Raised when an input fails domain validation rules."""
    pass


class InvalidEmailError(ValidationError):
    """Raised when an email address does not match the required regex pattern."""

    def __init__(self, email: str, reason: str = "Invalid email format") -> None:
        message = f"Email validation failed for '{email}': {reason}"
        super().__init__(message, details={"email": email, "reason": reason})
        self.email = email
        self.reason = reason


class InvalidStudentIdError(ValidationError):
    """Raised when a student ID does not conform to the expected format."""

    def __init__(self, student_id: str, reason: str = "Invalid ID format") -> None:
        message = f"Student ID validation failed for '{student_id}': {reason}"
        super().__init__(message, details={"student_id": student_id, "reason": reason})
        self.student_id = student_id
        self.reason = reason


class InvalidNameError(ValidationError):
    """Raised when a student name is empty, too short, or contains illegal characters."""

    def __init__(self, name: str, reason: str = "Invalid name format") -> None:
        message = f"Name validation failed for '{name}': {reason}"
        super().__init__(message, details={"name": name, "reason": reason})
        self.name = name
        self.reason = reason


class InvalidAgeError(ValidationError):
    """Raised when a student age is invalid or outside reasonable academic bounds."""

    def __init__(self, age: object, reason: str = "Age must be an integer between 10 and 120") -> None:
        message = f"Age validation failed for '{age}': {reason}"
        super().__init__(message, details={"age": str(age), "reason": reason})
        self.age = age
        self.reason = reason


class InvalidGPAError(ValidationError):
    """Raised when a student GPA is outside the valid range [0.0, 4.0]."""

    def __init__(self, gpa: object, reason: str = "GPA must be a number between 0.0 and 4.0") -> None:
        message = f"GPA validation failed for '{gpa}': {reason}"
        super().__init__(message, details={"gpa": str(gpa), "reason": reason})
        self.gpa = gpa
        self.reason = reason


class InvalidPhoneError(ValidationError):
    """Raised when a phone number fails regex or format checks."""

    def __init__(self, phone: str, reason: str = "Invalid phone number format") -> None:
        message = f"Phone validation failed for '{phone}': {reason}"
        super().__init__(message, details={"phone": phone, "reason": reason})
        self.phone = phone
        self.reason = reason


class InvalidAttendanceError(ValidationError):
    """Raised when attendance percentage is outside [0.0, 100.0]."""

    def __init__(self, attendance: object, reason: str = "Attendance must be between 0.0% and 100.0%") -> None:
        message = f"Attendance validation failed for '{attendance}': {reason}"
        super().__init__(message, details={"attendance": str(attendance), "reason": reason})
        self.attendance = attendance
        self.reason = reason


class InvalidStatusError(ValidationError):
    """Raised when student enrollment status is unrecognized."""

    def __init__(self, status: str, reason: str = "Status must be Active, Graduated, On Leave, or Probation") -> None:
        message = f"Status validation failed for '{status}': {reason}"
        super().__init__(message, details={"status": status, "reason": reason})
        self.status = status
        self.reason = reason


class StudentNotFoundError(StudentRecordError):
    """Raised when a student cannot be found by ID or query criteria."""

    def __init__(self, student_id: str) -> None:
        message = f"Student with ID '{student_id}' was not found."
        super().__init__(message, details={"student_id": student_id})
        self.student_id = student_id


class DuplicateStudentError(StudentRecordError):
    """Raised when attempting to add a student whose ID or Email is already registered."""

    def __init__(self, field: str, value: str) -> None:
        message = f"Student with {field} '{value}' already exists in the system."
        super().__init__(message, details={"conflict_field": field, "value": value})
        self.field = field
        self.value = value


class StorageError(StudentRecordError):
    """Raised when saving or loading student data encounters an I/O or parsing failure."""

    def __init__(self, operation: str, file_path: str, underlying_error: Exception | None = None) -> None:
        msg = f"Failed to {operation} student records at '{file_path}'"
        if underlying_error:
            msg += f": {underlying_error}"
        super().__init__(
            msg,
            details={
                "operation": operation,
                "file_path": file_path,
                "error": str(underlying_error) if underlying_error else "Unknown",
            },
        )
        self.operation = operation
        self.file_path = file_path
        self.underlying_error = underlying_error
