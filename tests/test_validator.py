"""Unit tests for validator module and regex email verification."""

import unittest
from student_manager.exceptions import (
    InvalidEmailError,
    InvalidStudentIdError,
    InvalidNameError,
    InvalidAgeError,
    InvalidGPAError,
)
from student_manager.validator import (
    validate_email,
    validate_student_id,
    validate_name,
    validate_age,
    validate_gpa,
)


class TestEmailValidator(unittest.TestCase):
    """Test suite for Regex email validation."""

    def test_valid_emails(self):
        valid_cases = [
            ("alice@example.com", "alice@example.com"),
            ("JOHN.DOE@UNIVERSITY.EDU", "john.doe@university.edu"),
            ("jane_smith123@sub.domain.org", "jane_smith123@sub.domain.org"),
            ("user+filter@gmail.com", "user+filter@gmail.com"),
            ("student.id-2024@cs.mit.edu", "student.id-2024@cs.mit.edu"),
            ("first.last@company.co.uk", "first.last@company.co.uk"),
        ]
        for raw, expected in valid_cases:
            with self.subTest(raw=raw):
                self.assertEqual(validate_email(raw), expected)

    def test_invalid_emails_raise_exception(self):
        invalid_cases = [
            ("", "empty"),
            ("   ", "whitespace"),
            ("plainaddress", "missing @ and domain"),
            ("@domain.com", "missing local part"),
            ("user@", "missing domain"),
            ("user@.com", "domain starts with dot"),
            ("user@domain..com", "consecutive dots"),
            ("user@domain.c", "single char TLD"),
            ("user name@domain.com", "space in local part"),
            ("user@dom ain.com", "space in domain"),
            ("user@@domain.com", "double @"),
            ("user@domain", "missing top-level domain"),
            (12345, "non-string input"),
            (None, "None input"),
        ]
        for raw, reason in invalid_cases:
            with self.subTest(raw=raw, reason=reason):
                with self.assertRaises(InvalidEmailError) as ctx:
                    validate_email(raw)  # type: ignore
                self.assertIn("Email", str(ctx.exception))


class TestStudentIdValidator(unittest.TestCase):
    """Test suite for Student ID format validation."""

    def test_valid_student_ids(self):
        valid_ids = ["STU-1001", "CS_2024_01", "abc", "ID-9999-XYZ"]
        for sid in valid_ids:
            with self.subTest(sid=sid):
                self.assertEqual(validate_student_id(sid), sid.upper())

    def test_invalid_student_ids(self):
        invalid_ids = ["", "  ", "ab", "toolongidstringexceeding20chars", "ID#100", "STU 100", None]
        for sid in invalid_ids:
            with self.subTest(sid=sid):
                with self.assertRaises(InvalidStudentIdError):
                    validate_student_id(sid)  # type: ignore


class TestNameValidator(unittest.TestCase):
    """Test suite for Student Name validation."""

    def test_valid_names(self):
        self.assertEqual(validate_name("John Doe"), "John Doe")
        self.assertEqual(validate_name("Mary-Jane Watson"), "Mary-Jane Watson")
        self.assertEqual(validate_name("  O'Connor  "), "O'Connor")
        self.assertEqual(validate_name("Dr. Martin Luther King Jr."), "Dr. Martin Luther King Jr.")

    def test_invalid_names(self):
        invalid_names = ["", " ", "A", "John123", "User@Name", None]
        for name in invalid_names:
            with self.subTest(name=name):
                with self.assertRaises(InvalidNameError):
                    validate_name(name)  # type: ignore


class TestAgeValidator(unittest.TestCase):
    """Test suite for Student Age validation."""

    def test_valid_ages(self):
        self.assertEqual(validate_age(20), 20)
        self.assertEqual(validate_age("25"), 25)
        self.assertEqual(validate_age(10), 10)
        self.assertEqual(validate_age(120), 120)

    def test_invalid_ages(self):
        invalid_ages = [9, 121, -5, "twenty", 22.5, None, ""]
        for age in invalid_ages:
            with self.subTest(age=age):
                with self.assertRaises(InvalidAgeError):
                    validate_age(age)  # type: ignore


class TestGPAValidator(unittest.TestCase):
    """Test suite for Student GPA validation."""

    def test_valid_gpas(self):
        self.assertEqual(validate_gpa(3.85), 3.85)
        self.assertEqual(validate_gpa("4.0"), 4.0)
        self.assertEqual(validate_gpa(0), 0.0)
        self.assertEqual(validate_gpa("2.756"), 2.76)

    def test_invalid_gpas(self):
        invalid_gpas = [-0.1, 4.01, 5.0, "high", None]
        for gpa in invalid_gpas:
            with self.subTest(gpa=gpa):
                with self.assertRaises(InvalidGPAError):
                    validate_gpa(gpa)  # type: ignore


if __name__ == "__main__":
    unittest.main()
