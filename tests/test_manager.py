"""Unit tests for StudentRecordManager operations."""

import shutil
import tempfile
import unittest
from pathlib import Path

from student_manager.exceptions import (
    DuplicateStudentError,
    StudentNotFoundError,
    InvalidEmailError,
    InvalidAgeError,
)
from student_manager.manager import StudentRecordManager
from student_manager.storage import JsonStorageHandler


class TestStudentRecordManager(unittest.TestCase):
    """Test CRUD operations, unique constraints, and search features."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage_file = Path(self.test_dir) / "students_test.json"
        self.storage = JsonStorageHandler(self.storage_file)
        self.manager = StudentRecordManager(storage=self.storage, auto_save=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_add_student_success(self):
        student = self.manager.add_student(
            student_id="STU-101",
            name="Charlie Brown",
            email="charlie@peanuts.org",
            age=19,
            course="Arts",
            gpa=3.4,
        )
        self.assertEqual(student.student_id, "STU-101")
        self.assertEqual(student.name, "Charlie Brown")
        self.assertEqual(student.email, "charlie@peanuts.org")
        self.assertEqual(len(self.manager.get_all_students()), 1)

        # Verify persisted to disk
        reloaded_manager = StudentRecordManager(storage=self.storage)
        self.assertEqual(len(reloaded_manager.get_all_students()), 1)
        self.assertEqual(reloaded_manager.get_student("STU-101").name, "Charlie Brown")

    def test_add_duplicate_student_id_raises_exception(self):
        self.manager.add_student("STU-101", "Charlie Brown", "charlie@peanuts.org", 19)
        with self.assertRaises(DuplicateStudentError) as ctx:
            self.manager.add_student("STU-101", "Different Name", "different@email.com", 20)
        self.assertIn("Student ID", str(ctx.exception))

    def test_add_duplicate_email_raises_exception(self):
        self.manager.add_student("STU-101", "Charlie Brown", "charlie@peanuts.org", 19)
        with self.assertRaises(DuplicateStudentError) as ctx:
            self.manager.add_student("STU-102", "Lucy van Pelt", "charlie@peanuts.org", 20)
        self.assertIn("Email address", str(ctx.exception))

    def test_add_invalid_email_raises_regex_exception(self):
        with self.assertRaises(InvalidEmailError):
            self.manager.add_student("STU-101", "Charlie", "not-a-valid-email", 19)

    def test_add_invalid_age_raises_exception(self):
        with self.assertRaises(InvalidAgeError):
            self.manager.add_student("STU-101", "Charlie", "charlie@peanuts.org", 200)

    def test_get_nonexistent_student_raises_exception(self):
        with self.assertRaises(StudentNotFoundError):
            self.manager.get_student("STU-999")

    def test_search_students(self):
        self.manager.add_student("STU-001", "Alan Turing", "alan@cambridge.ac.uk", 24, "Computer Science", 4.0)
        self.manager.add_student("STU-002", "Ada Lovelace", "ada@london.ac.uk", 22, "Mathematics", 3.95)
        self.manager.add_student("STU-003", "Grace Hopper", "grace@navy.mil", 25, "Computer Science", 3.8)

        # Search by name
        results = self.manager.search_students("turing")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Alan Turing")

        # Search by course
        cs_students = self.manager.search_students("Computer Science")
        self.assertEqual(len(cs_students), 2)

        # Search by partial email
        email_matches = self.manager.search_students("navy.mil")
        self.assertEqual(len(email_matches), 1)
        self.assertEqual(email_matches[0].student_id, "STU-003")

    def test_update_student(self):
        self.manager.add_student("STU-001", "Alan Turing", "alan@cambridge.ac.uk", 24, "Computer Science", 4.0)
        updated = self.manager.update_student("STU-001", course="Cybernetics", gpa=3.98)
        self.assertEqual(updated.course, "Cybernetics")
        self.assertEqual(updated.gpa, 3.98)
        self.assertEqual(updated.name, "Alan Turing")

    def test_delete_student(self):
        self.manager.add_student("STU-001", "Alan Turing", "alan@cambridge.ac.uk", 24)
        deleted = self.manager.delete_student("STU-001")
        self.assertEqual(deleted.student_id, "STU-001")
        self.assertEqual(len(self.manager.get_all_students()), 0)
        with self.assertRaises(StudentNotFoundError):
            self.manager.get_student("STU-001")

    def test_statistics_calculation(self):
        self.manager.add_student("STU-001", "Student A", "a@test.com", 20, "CS", 3.5)
        self.manager.add_student("STU-002", "Student B", "b@test.com", 21, "CS", 3.9)
        self.manager.add_student("STU-003", "Student C", "c@test.com", 22, "Math", 4.0)

        stats = self.manager.get_statistics()
        self.assertEqual(stats["total_students"], 3)
        self.assertAlmostEqual(stats["average_gpa"], 3.8, places=2)
        self.assertEqual(stats["highest_gpa"], 4.0)
        self.assertEqual(stats["lowest_gpa"], 3.5)
        self.assertEqual(stats["courses"]["CS"], 2)
        self.assertEqual(stats["courses"]["Math"], 1)


if __name__ == "__main__":
    unittest.main()
