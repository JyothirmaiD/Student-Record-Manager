"""Student Record Manager Package

A modular and robust Python system for student academic records management
featuring Regex email validation, persistent storage, and comprehensive
exception handling.
"""

from student_manager.exceptions import (
    StudentRecordError,
    ValidationError,
    InvalidEmailError,
    InvalidStudentIdError,
    InvalidNameError,
    InvalidAgeError,
    InvalidGPAError,
    StudentNotFoundError,
    DuplicateStudentError,
    StorageError,
)
from student_manager.models import Student
from student_manager.validator import (
    validate_email,
    validate_student_id,
    validate_name,
    validate_age,
    validate_gpa,
)
from student_manager.storage import JsonStorageHandler, CsvStorageHandler
from student_manager.manager import StudentRecordManager

__all__ = [
    "StudentRecordError",
    "ValidationError",
    "InvalidEmailError",
    "InvalidStudentIdError",
    "InvalidNameError",
    "InvalidAgeError",
    "InvalidGPAError",
    "StudentNotFoundError",
    "DuplicateStudentError",
    "StorageError",
    "Student",
    "validate_email",
    "validate_student_id",
    "validate_name",
    "validate_age",
    "validate_gpa",
    "JsonStorageHandler",
    "CsvStorageHandler",
    "StudentRecordManager",
]

__version__ = "1.0.0"
