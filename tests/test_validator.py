"""Unit tests for regex email validation and field validator functions."""

import unittest
from src.validator import (
    validate_email,
    validate_student_id,
    validate_name,
    validate_course,
    validate_gpa,
)
from src.exceptions import InvalidEmailError, InvalidInputError


class TestEmailRegexValidation(unittest.TestCase):
    """Test suite specifically targeting Email validation using Regular Expressions."""

    def test_valid_emails(self):
        """Ensure standard, academic, and subdomain emails pass validation."""
        valid_samples = [
            "student@university.edu",
            "john.doe@domain.com",
            "jane_doe123@sub.college.org",
            "user+tag@domain.co.uk",
            "first-last@dept.school.edu",
        ]
        for email in valid_samples:
            with self.subTest(email=email):
                result = validate_email(email)
                self.assertEqual(result, email.lower())

    def test_invalid_email_missing_at(self):
        """Ensure emails without '@' symbol raise InvalidEmailError."""
        with self.assertRaises(InvalidEmailError) as ctx:
            validate_email("plainaddress.com")
        self.assertIn("Email does not match valid pattern", str(ctx.exception))

    def test_invalid_email_missing_domain(self):
        """Ensure emails without domain part raise InvalidEmailError."""
        with self.assertRaises(InvalidEmailError):
            validate_email("user@")

    def test_invalid_email_missing_tld(self):
        """Ensure emails without top-level domain raise InvalidEmailError."""
        with self.assertRaises(InvalidEmailError):
            validate_email("user@domain")

    def test_invalid_email_with_spaces(self):
        """Ensure emails containing spaces raise InvalidEmailError."""
        with self.assertRaises(InvalidEmailError):
            validate_email("user name@example.com")

    def test_invalid_email_empty_string(self):
        """Ensure empty email raises InvalidEmailError."""
        with self.assertRaises(InvalidEmailError) as ctx:
            validate_email("   ")
        self.assertIn("cannot be empty", str(ctx.exception))

    def test_invalid_email_non_string_type(self):
        """Ensure non-string input raises InvalidEmailError."""
        with self.assertRaises(InvalidEmailError):
            validate_email(12345)  # type: ignore


class TestFieldValidators(unittest.TestCase):
    """Test suite for other field validators and their exception handling."""

    def test_valid_student_id(self):
        self.assertEqual(validate_student_id("stu101"), "STU101")
        self.assertEqual(validate_student_id("S-99_A"), "S-99_A")

    def test_invalid_student_id_empty(self):
        with self.assertRaises(InvalidInputError):
            validate_student_id("")

    def test_invalid_student_id_special_characters(self):
        with self.assertRaises(InvalidInputError):
            validate_student_id("STU#100!")

    def test_valid_name(self):
        self.assertEqual(validate_name("john doe"), "John Doe")
        self.assertEqual(validate_name("Dr. Mary-Jane Watson"), "Dr. Mary-jane Watson")

    def test_invalid_name_too_short(self):
        with self.assertRaises(InvalidInputError):
            validate_name("A")

    def test_valid_course(self):
        self.assertEqual(validate_course("Computer Science"), "Computer Science")

    def test_invalid_course_empty(self):
        with self.assertRaises(InvalidInputError):
            validate_course("   ")

    def test_valid_gpa(self):
        self.assertEqual(validate_gpa(3.75), 3.75)
        self.assertEqual(validate_gpa("4.0"), 4.0)
        self.assertEqual(validate_gpa(0), 0.0)

    def test_invalid_gpa_out_of_range(self):
        with self.assertRaises(InvalidInputError):
            validate_gpa(4.5)
        with self.assertRaises(InvalidInputError):
            validate_gpa(-0.5)

    def test_invalid_gpa_non_numeric(self):
        with self.assertRaises(InvalidInputError):
            validate_gpa("four point zero")


if __name__ == "__main__":
    unittest.main()
