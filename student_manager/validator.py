"""Validation utilities for Student Record Manager.

Implements rigorous Regex-based validation for emails, student IDs,
names, age, and GPA, accompanied by descriptive custom exception raising.
"""

import re
from student_manager.exceptions import (
    InvalidEmailError,
    InvalidStudentIdError,
    InvalidNameError,
    InvalidAgeError,
    InvalidGPAError,
)

# RFC 5322-compliant practical email regular expression:
# - Local part: alphanumeric characters plus ._%+- (no leading/trailing dot, no consecutive dots)
# - @ delimiter
# - Domain: alphanumeric with hyphens
# - Top-Level Domain (TLD): 2 or more alphabetic characters
EMAIL_REGEX_PATTERN = r"^[a-zA-Z0-9]([a-zA-Z0-9._%+-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$"
EMAIL_REGEX = re.compile(EMAIL_REGEX_PATTERN)

# Student ID: Alphanumeric with hyphens/underscores, 3 to 20 characters (e.g., STU-1001, S102, CS_2024_01)
STUDENT_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{3,20}$")

# Name: Allows alphabets, spaces, apostrophes, hyphens, and periods (2 to 100 characters)
NAME_REGEX = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s'\-\.]{2,100}$")


def validate_email(email: str) -> str:
    """Validate student email address using Regular Expressions.

    Args:
        email: The email string to validate.

    Returns:
        The normalized (lowercased and stripped) email if valid.

    Raises:
        InvalidEmailError: If the email does not conform to regex or standard rules.
    """
    if not isinstance(email, str):
        raise InvalidEmailError(str(email), "Email must be a text string")

    cleaned = email.strip()
    if not cleaned:
        raise InvalidEmailError("", "Email address cannot be empty")

    if len(cleaned) > 254:
        raise InvalidEmailError(cleaned, "Email address exceeds maximum length of 254 characters")

    if ".." in cleaned:
        raise InvalidEmailError(cleaned, "Email cannot contain consecutive dots ('..')")

    if not EMAIL_REGEX.match(cleaned):
        raise InvalidEmailError(
            cleaned,
            "Must follow standard format (e.g., user@domain.com) with valid characters and TLD",
        )

    return cleaned.lower()


def validate_student_id(student_id: str) -> str:
    """Validate student ID format.

    Args:
        student_id: The ID string to validate.

    Returns:
        The cleaned, uppercase student ID.

    Raises:
        InvalidStudentIdError: If the ID is empty or contains invalid characters.
    """
    if not isinstance(student_id, str):
        raise InvalidStudentIdError(str(student_id), "Student ID must be a string")

    cleaned = student_id.strip()
    if not cleaned:
        raise InvalidStudentIdError("", "Student ID cannot be empty")

    if not STUDENT_ID_REGEX.match(cleaned):
        raise InvalidStudentIdError(
            cleaned,
            "Must be 3-20 alphanumeric characters, hyphens, or underscores (e.g., 'STU-1001')",
        )

    return cleaned.upper()


def validate_name(name: str) -> str:
    """Validate student full name.

    Args:
        name: The name string to validate.

    Returns:
        The normalized name with trimmed whitespace.

    Raises:
        InvalidNameError: If name is empty, too short, or has invalid characters.
    """
    if not isinstance(name, str):
        raise InvalidNameError(str(name), "Name must be a string")

    cleaned = name.strip()
    if not cleaned:
        raise InvalidNameError("", "Student name cannot be empty")

    if len(cleaned) < 2:
        raise InvalidNameError(cleaned, "Name must be at least 2 characters long")

    if not NAME_REGEX.match(cleaned):
        raise InvalidNameError(
            cleaned,
            "Name may only contain letters, spaces, hyphens, periods, and apostrophes",
        )

    # Normalize multiple whitespace into single space and title-case
    words = cleaned.split()
    return " ".join(words)


def validate_age(age_val: int | str) -> int:
    """Validate student age.

    Args:
        age_val: Integer or numeric string representing student age.

    Returns:
        The validated integer age.

    Raises:
        InvalidAgeError: If age is not numeric or falls outside [10, 120].
    """
    if isinstance(age_val, float):
        raise InvalidAgeError(age_val, "Age must be a whole integer number, not a float")

    if isinstance(age_val, str) and "." in age_val:
        raise InvalidAgeError(age_val, "Age must be an integer without decimal places")

    try:
        age = int(age_val)
    except (ValueError, TypeError):
        raise InvalidAgeError(age_val, "Age must be a valid integer number")

    if age < 10 or age > 120:
        raise InvalidAgeError(age, "Age must be between 10 and 120 years")

    return age


def validate_gpa(gpa_val: float | int | str) -> float:
    """Validate student Grade Point Average (GPA).

    Args:
        gpa_val: Float, int, or string representing student GPA.

    Returns:
        The validated float GPA rounded to 2 decimal places.

    Raises:
        InvalidGPAError: If GPA is not a number or outside [0.0, 4.0].
    """
    try:
        gpa = float(gpa_val)
    except (ValueError, TypeError):
        raise InvalidGPAError(gpa_val, "GPA must be a valid decimal number")

    if gpa < 0.0 or gpa > 4.0:
        raise InvalidGPAError(gpa, "GPA must be between 0.0 and 4.0")

    return round(gpa, 2)
