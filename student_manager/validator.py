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
    InvalidPhoneError,
    InvalidAttendanceError,
    InvalidStatusError,
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

# Phone Regex: International / national phone format with optional country code, parenthesized area code, spaces, hyphens, and dots
PHONE_REGEX = re.compile(
    r"^(?:\+?[0-9]{1,4}[-.\s]*)?(?:\([0-9]{1,6}\)[-.\s]*)?[0-9]{1,6}(?:[-.\s]?[0-9]{1,6})*$"
)

VALID_STATUSES = {"Active", "Graduated", "On Leave", "Probation"}


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


def validate_phone(phone_val: str | None, optional: bool = True) -> str:
    """Validate student phone number using Regex.

    Args:
        phone_val: Raw phone string (e.g., '+1-555-0199', '9876543210').
        optional: If True, an empty string is accepted and returned as ''.

    Returns:
        The cleaned phone string.

    Raises:
        InvalidPhoneError: If phone is provided but does not match required format.
    """
    if phone_val is None or (isinstance(phone_val, str) and not phone_val.strip()):
        if optional:
            return ""
        raise InvalidPhoneError("", "Phone number cannot be empty")

    cleaned = str(phone_val).strip()
    # Strip any formatting characters to count raw digits
    digits_only = re.sub(r"\D", "", cleaned)
    if len(digits_only) < 7 or len(digits_only) > 15:
        raise InvalidPhoneError(cleaned, "Phone number must contain between 7 and 15 digits")

    if not PHONE_REGEX.match(cleaned):
        raise InvalidPhoneError(
            cleaned,
            "Phone must follow standard formats (e.g., +1-555-0199, (555) 123-4567, or 9876543210)",
        )

    return cleaned


def validate_attendance(attendance_val: float | int | str) -> float:
    """Validate student attendance percentage.

    Args:
        attendance_val: Percentage value (0.0 to 100.0).

    Returns:
        Validated float attendance rounded to 1 decimal place.

    Raises:
        InvalidAttendanceError: If value is not a number or outside [0.0, 100.0].
    """
    try:
        att = float(attendance_val)
    except (ValueError, TypeError):
        raise InvalidAttendanceError(attendance_val, "Attendance must be a valid numeric percentage")

    if att < 0.0 or att > 100.0:
        raise InvalidAttendanceError(att, "Attendance percentage must be between 0.0% and 100.0%")

    return round(att, 1)


def validate_status(status_val: str) -> str:
    """Validate student enrollment status.

    Args:
        status_val: Status string.

    Returns:
        Canonical status string (e.g. 'Active').

    Raises:
        InvalidStatusError: If status is not in VALID_STATUSES.
    """
    if not isinstance(status_val, str):
        raise InvalidStatusError(str(status_val), "Status must be a string")

    cleaned = status_val.strip().title()
    # Normalizing variations like 'On-leave' -> 'On Leave'
    if cleaned.lower() in ("on-leave", "on leave", "leave"):
        cleaned = "On Leave"

    if cleaned not in VALID_STATUSES:
        raise InvalidStatusError(
            status_val,
            f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )
    return cleaned


def calculate_grade_letter(gpa: float) -> str:
    """Determine letter grade from GPA.

    Scale:
        >= 3.85: A+
        >= 3.50: A
        >= 3.00: B+
        >= 2.50: B
        >= 2.00: C
        >= 1.00: D
        <  1.00: F
    """
    if gpa >= 3.85:
        return "A+"
    if gpa >= 3.50:
        return "A"
    if gpa >= 3.00:
        return "B+"
    if gpa >= 2.50:
        return "B"
    if gpa >= 2.00:
        return "C"
    if gpa >= 1.00:
        return "D"
    return "F"
