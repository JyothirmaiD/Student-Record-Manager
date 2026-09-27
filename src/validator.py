"""Validation logic for Student Record Manager including Regex Email Validation."""

import re
from src.exceptions import InvalidEmailError, InvalidInputError

# Standard RFC 5322-compliant email regex pattern
EMAIL_REGEX_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
_COMPILED_EMAIL_REGEX = re.compile(EMAIL_REGEX_PATTERN)


def validate_email(email: str) -> str:
    """
    Validate email address format using regular expressions.

    Args:
        email: The email string to validate.

    Returns:
        The trimmed, lowercased valid email string.

    Raises:
        InvalidEmailError: If the email string does not conform to standard format.
    """
    if not isinstance(email, str):
        raise InvalidEmailError(str(email), "Email must be a string")

    cleaned_email = email.strip()
    if not cleaned_email:
        raise InvalidEmailError("", "Email address cannot be empty")

    if not _COMPILED_EMAIL_REGEX.match(cleaned_email):
        raise InvalidEmailError(cleaned_email, "Email does not match valid pattern")

    return cleaned_email.lower()


def validate_student_id(student_id: str) -> str:
    """
    Validate that student ID is non-empty and alphanumeric.

    Args:
        student_id: The ID string to check.

    Returns:
        The trimmed, uppercase student ID.

    Raises:
        InvalidInputError: If student ID is empty or contains illegal characters.
    """
    if not isinstance(student_id, str):
        raise InvalidInputError("Student ID", str(student_id), "ID must be a string")

    cleaned_id = student_id.strip()
    if not cleaned_id:
        raise InvalidInputError("Student ID", cleaned_id, "ID cannot be empty")

    if not re.match(r"^[A-Za-z0-9_-]{2,20}$", cleaned_id):
        raise InvalidInputError(
            "Student ID",
            cleaned_id,
            "ID must be 2-20 characters long and contain only letters, numbers, hyphens, or underscores"
        )

    return cleaned_id.upper()


def validate_name(name: str) -> str:
    """
    Validate student name.

    Args:
        name: Name string.

    Returns:
        Formatted title-case name string.

    Raises:
        InvalidInputError: If name is invalid.
    """
    if not isinstance(name, str):
        raise InvalidInputError("Name", str(name), "Name must be a string")

    cleaned_name = name.strip()
    if len(cleaned_name) < 2:
        raise InvalidInputError("Name", cleaned_name, "Name must be at least 2 characters long")

    if not re.match(r"^[A-Za-z\s.'-]+$", cleaned_name):
        raise InvalidInputError("Name", cleaned_name, "Name may only contain letters, spaces, dots, and hyphens")

    return " ".join(word.capitalize() for word in cleaned_name.split())


def validate_course(course: str) -> str:
    """
    Validate student enrolled course or major.

    Args:
        course: Course name string.

    Returns:
        Trimmed course string.

    Raises:
        InvalidInputError: If course name is invalid.
    """
    if not isinstance(course, str):
        raise InvalidInputError("Course", str(course), "Course must be a string")

    cleaned_course = course.strip()
    if not cleaned_course:
        raise InvalidInputError("Course", cleaned_course, "Course name cannot be empty")

    return cleaned_course


def validate_gpa(gpa_value: float | int | str) -> float:
    """
    Validate GPA value (between 0.0 and 4.0 scale).

    Args:
        gpa_value: Numerical or string representation of GPA.

    Returns:
        Validated float GPA rounded to 2 decimal places.

    Raises:
        InvalidInputError: If GPA is not a number or outside [0.0, 4.0].
    """
    try:
        gpa = float(gpa_value)
    except (ValueError, TypeError):
        raise InvalidInputError("GPA", str(gpa_value), "GPA must be a valid numeric value")

    if not (0.0 <= gpa <= 4.0):
        raise InvalidInputError("GPA", str(gpa), "GPA must be between 0.0 and 4.0")

    return round(gpa, 2)
