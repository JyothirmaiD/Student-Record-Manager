"""Unit tests for StudentRecordManager and file persistence."""

import os
import shutil
import tempfile
import unittest
from src.models import Student
from src.manager import StudentRecordManager
from src.storage import JSONStorage
from src.exceptions import DuplicateStudentError, StudentNotFoundError, StorageError


class TestStudentRecordManager(unittest.TestCase):
    """Test suite for StudentRecordManager CRUD operations and exceptions."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, "test_students.json")
        self.storage = JSONStorage(filepath=self.temp_file)
        self.manager = StudentRecordManager(storage=self.storage)

        self.student1 = Student.create("STU001", "Emma Watson", "emma@college.edu", "Literature", 3.9)
        self.student2 = Student.create("STU002", "Liam Smith", "liam@tech.edu", "Engineering", 3.4)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_student_success(self):
        self.manager.add_student(self.student1)
        self.assertEqual(self.manager.count(), 1)
        retrieved = self.manager.get_student("STU001")
        self.assertEqual(retrieved.name, "Emma Watson")

    def test_add_duplicate_student_raises_exception(self):
        self.manager.add_student(self.student1)
        with self.assertRaises(DuplicateStudentError) as ctx:
            self.manager.add_student(self.student1)
        self.assertIn("STU001", str(ctx.exception))

    def test_get_non_existent_student_raises_exception(self):
        with self.assertRaises(StudentNotFoundError) as ctx:
            self.manager.get_student("NONEXISTENT")
        self.assertIn("NONEXISTENT", str(ctx.exception))

    def test_delete_student_success(self):
        self.manager.add_student(self.student1)
        deleted = self.manager.delete_student("STU001")
        self.assertEqual(deleted.student_id, "STU001")
        self.assertEqual(self.manager.count(), 0)

    def test_delete_non_existent_student_raises_exception(self):
        with self.assertRaises(StudentNotFoundError):
            self.manager.delete_student("UNKNOWN_ID")

    def test_search_students(self):
        self.manager.add_student(self.student1)
        self.manager.add_student(self.student2)

        # Search by name
        results = self.manager.search_students("emma")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].student_id, "STU001")

        # Search by course
        results = self.manager.search_students("engineering")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].student_id, "STU002")

        # Search by email
        results = self.manager.search_students("college.edu")
        self.assertEqual(len(results), 1)

    def test_save_and_read_persistence_roundtrip(self):
        """Verify Save Data to File and Read Student Data requirements."""
        self.manager.add_student(self.student1)
        self.manager.add_student(self.student2)

        # Save to file
        saved_count = self.manager.save_to_file()
        self.assertEqual(saved_count, 2)
        self.assertTrue(os.path.exists(self.temp_file))

        # Create a fresh manager pointing to the same storage
        new_manager = StudentRecordManager(storage=self.storage)
        self.assertEqual(new_manager.count(), 0)

        # Load from file
        loaded_count = new_manager.load_from_file()
        self.assertEqual(loaded_count, 2)
        self.assertEqual(new_manager.count(), 2)

        stu1 = new_manager.get_student("STU001")
        self.assertEqual(stu1.name, "Emma Watson")
        self.assertEqual(stu1.email, "emma@college.edu")

    def test_load_corrupted_file_raises_storage_error(self):
        """Verify that loading an invalid JSON file raises StorageError."""
        with open(self.temp_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json [ [")

        with self.assertRaises(StorageError):
            self.manager.load_from_file()


if __name__ == "__main__":
    unittest.main()
