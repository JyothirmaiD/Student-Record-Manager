"""Unit tests verifying custom exception hierarchy and error details."""

import unittest
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


class TestExceptions(unittest.TestCase):
    """Test custom exception classes and their metadata."""

    def test_inheritance_hierarchy(self):
        self.assertTrue(issubclass(ValidationError, StudentRecordError))
        self.assertTrue(issubclass(InvalidEmailError, ValidationError))
        self.assertTrue(issubclass(InvalidStudentIdError, ValidationError))
        self.assertTrue(issubclass(InvalidNameError, ValidationError))
        self.assertTrue(issubclass(InvalidAgeError, ValidationError))
        self.assertTrue(issubclass(InvalidGPAError, ValidationError))
        self.assertTrue(issubclass(StudentNotFoundError, StudentRecordError))
        self.assertTrue(issubclass(DuplicateStudentError, StudentRecordError))
        self.assertTrue(issubclass(StorageError, StudentRecordError))

    def test_invalid_email_error_attributes(self):
        err = InvalidEmailError("bad@@address", "double at sign")
        self.assertEqual(err.email, "bad@@address")
        self.assertEqual(err.reason, "double at sign")
        self.assertIn("bad@@address", str(err))

    def test_student_not_found_error_attributes(self):
        err = StudentNotFoundError("STU-404")
        self.assertEqual(err.student_id, "STU-404")
        self.assertIn("STU-404", str(err))

    def test_duplicate_student_error_attributes(self):
        err = DuplicateStudentError("Student ID", "STU-101")
        self.assertEqual(err.field, "Student ID")
        self.assertEqual(err.value, "STU-101")
        self.assertIn("STU-101", str(err))

    def test_storage_error_attributes(self):
        underlying = PermissionError("Access denied")
        err = StorageError("save", "data/test.json", underlying)
        self.assertEqual(err.operation, "save")
        self.assertEqual(err.file_path, "data/test.json")
        self.assertEqual(err.underlying_error, underlying)
        self.assertIn("Access denied", str(err))


if __name__ == "__main__":
    unittest.main()
