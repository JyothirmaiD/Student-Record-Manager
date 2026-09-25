"""Unit tests for JSON and CSV storage persistence."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from student_manager.exceptions import StorageError
from student_manager.models import Student
from student_manager.storage import JsonStorageHandler, CsvStorageHandler


class TestStorage(unittest.TestCase):
    """Test storage persistence, atomic file write, and corrupted file handling."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.json_path = Path(self.test_dir) / "subfolder" / "students.json"
        self.csv_path = Path(self.test_dir) / "students.csv"
        self.handler = JsonStorageHandler(self.json_path)
        self.sample_students = [
            Student.create(
                student_id="STU-001",
                name="Alice Smith",
                email="alice@university.edu",
                age=20,
                course="Computer Science",
                gpa=3.9,
            ),
            Student.create(
                student_id="STU-002",
                name="Bob Jones",
                email="bob@university.edu",
                age=22,
                course="Mathematics",
                gpa=3.6,
            ),
        ]

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_and_load_json(self):
        self.handler.save(self.sample_students)
        self.assertTrue(self.json_path.exists())

        loaded = self.handler.load()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].student_id, "STU-001")
        self.assertEqual(loaded[0].name, "Alice Smith")
        self.assertEqual(loaded[1].email, "bob@university.edu")

    def test_load_nonexistent_file_returns_empty_list(self):
        nonexistent = JsonStorageHandler(Path(self.test_dir) / "does_not_exist.json")
        self.assertEqual(nonexistent.load(), [])

    def test_load_corrupted_json_raises_storage_error(self):
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.json_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json content ]")

        with self.assertRaises(StorageError):
            self.handler.load()

    def test_csv_export_and_load(self):
        csv_handler = CsvStorageHandler(self.csv_path)
        csv_handler.save(self.sample_students)
        self.assertTrue(self.csv_path.exists())

        loaded = csv_handler.load()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].student_id, "STU-001")
        self.assertEqual(loaded[1].student_id, "STU-002")


if __name__ == "__main__":
    unittest.main()
