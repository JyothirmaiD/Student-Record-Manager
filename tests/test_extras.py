"""Unit tests for extra student fields, phone regex, attendance, and analytics."""

import unittest
from student_manager.exceptions import (
    InvalidPhoneError,
    InvalidAttendanceError,
    InvalidStatusError,
    DuplicateStudentError,
    StudentNotFoundError,
)
from student_manager.validator import (
    validate_phone,
    validate_attendance,
    validate_status,
    calculate_grade_letter,
)
from student_manager.models import Student
from student_manager.manager import StudentRecordManager
from student_manager.storage import JsonStorageHandler
import tempfile
import shutil
from pathlib import Path


class TestPhoneValidator(unittest.TestCase):
    """Test suite for phone regex validator."""

    def test_valid_phone_numbers(self):
        valid_cases = [
            ("+1-555-0143", "+1-555-0143"),
            ("+91-98765-43210", "+91-98765-43210"),
            ("(555) 123-4567", "(555) 123-4567"),
            ("+44 20 7946 0912", "+44 20 7946 0912"),
            ("9876543210", "9876543210"),
            ("", ""),  # optional empty
            (None, ""),  # optional None
        ]
        for raw, expected in valid_cases:
            with self.subTest(raw=raw):
                self.assertEqual(validate_phone(raw, optional=True), expected)

    def test_invalid_phone_numbers(self):
        invalid_cases = [
            ("123", "Too short"),
            ("1234567890123456789", "Too long"),
            ("abc-def-ghij", "Letters in phone"),
            ("++1234567890", "Double plus"),
            ("!@#$%", "Symbols"),
        ]
        for raw, reason in invalid_cases:
            with self.subTest(raw=raw, reason=reason):
                with self.assertRaises(InvalidPhoneError):
                    validate_phone(raw, optional=True)

    def test_mandatory_phone_empty_raises(self):
        with self.assertRaises(InvalidPhoneError):
            validate_phone("", optional=False)


class TestAttendanceValidator(unittest.TestCase):
    """Test suite for attendance percentage validation."""

    def test_valid_attendance(self):
        self.assertEqual(validate_attendance(95.5), 95.5)
        self.assertEqual(validate_attendance("100"), 100.0)
        self.assertEqual(validate_attendance(0), 0.0)

    def test_invalid_attendance_raises(self):
        invalid_cases = [-5.0, 105.0, "not_a_number", None]
        for val in invalid_cases:
            with self.subTest(val=val):
                with self.assertRaises(InvalidAttendanceError):
                    validate_attendance(val)  # type: ignore


class TestStatusAndGrade(unittest.TestCase):
    """Test suite for status and grade calculation."""

    def test_status_validation(self):
        self.assertEqual(validate_status("active"), "Active")
        self.assertEqual(validate_status("on-leave"), "On Leave")
        self.assertEqual(validate_status("Graduated"), "Graduated")
        self.assertEqual(validate_status("probation"), "Probation")

        with self.assertRaises(InvalidStatusError):
            validate_status("Expelled")

    def test_grade_letter_calculation(self):
        self.assertEqual(calculate_grade_letter(4.0), "A+")
        self.assertEqual(calculate_grade_letter(3.9), "A+")
        self.assertEqual(calculate_grade_letter(3.6), "A")
        self.assertEqual(calculate_grade_letter(3.2), "B+")
        self.assertEqual(calculate_grade_letter(2.8), "B")
        self.assertEqual(calculate_grade_letter(2.2), "C")
        self.assertEqual(calculate_grade_letter(1.5), "D")
        self.assertEqual(calculate_grade_letter(0.5), "F")


class TestManagerExtraFeatures(unittest.TestCase):
    """Test suite for StudentRecordManager with extra attributes and analytics."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage_file = Path(self.test_dir) / "students_test.json"
        self.manager = StudentRecordManager(
            storage=JsonStorageHandler(self.storage_file),
            auto_save=True,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_add_student_with_all_extra_fields(self):
        student = self.manager.add_student(
            student_id="STU-9901",
            name="Alexander Pierce",
            email="a.pierce@shield.gov",
            age=22,
            course="Security Studies",
            gpa=3.95,
            phone="+1-555-9988",
            gender="Male",
            semester="Semester 5",
            status="Active",
            attendance=98.5,
            emergency_contact="Nick Fury (+1-555-0001)",
            city="Washington DC",
            tags=["Honor Roll", "Intelligence", "Pilot"],
            extra_attributes={"security_clearance": "Level 8", "blood_group": "AB+"},
        )
        self.assertEqual(student.student_id, "STU-9901")
        self.assertEqual(student.phone, "+1-555-9988")
        self.assertEqual(student.grade_letter, "A+")
        self.assertTrue(student.is_honor_roll)
        self.assertEqual(student.extra_attributes["security_clearance"], "Level 8")

        # Verify persisted to file
        reloaded_manager = StudentRecordManager(
            storage=JsonStorageHandler(self.storage_file),
            auto_save=False,
        )
        fetched = reloaded_manager.get_student("STU-9901")
        self.assertEqual(fetched.name, "Alexander Pierce")
        self.assertEqual(fetched.tags, ["Honor Roll", "Intelligence", "Pilot"])
        self.assertEqual(fetched.extra_attributes["blood_group"], "AB+")

    def test_search_with_filters(self):
        self.manager.add_student(
            student_id="STU-01",
            name="Alice Smith",
            email="alice@test.edu",
            age=20,
            course="Computer Science",
            gpa=3.9,
            status="Active",
        )
        self.manager.add_student(
            student_id="STU-02",
            name="Bob Jones",
            email="bob@test.edu",
            age=22,
            course="Mechanical Engineering",
            gpa=3.2,
            status="Active",
        )
        self.manager.add_student(
            student_id="STU-03",
            name="Charlie Brown",
            email="charlie@test.edu",
            age=24,
            course="Computer Science",
            gpa=2.8,
            status="Graduated",
        )

        # Filter by department
        cs_students = self.manager.search_students(department="Computer Science")
        self.assertEqual(len(cs_students), 2)

        # Filter by status
        graduated = self.manager.search_students(status="Graduated")
        self.assertEqual(len(graduated), 1)
        self.assertEqual(graduated[0].student_id, "STU-03")

        # Filter by min GPA
        honor_students = self.manager.search_students(min_gpa=3.5)
        self.assertEqual(len(honor_students), 1)
        self.assertEqual(honor_students[0].name, "Alice Smith")

    def test_update_student_extra_fields(self):
        self.manager.add_student(
            student_id="STU-10",
            name="Diana Prince",
            email="diana@amazon.org",
            age=25,
            course="Anthropology",
            gpa=3.8,
        )
        updated = self.manager.update_student(
            "STU-10",
            phone="+1-555-1122",
            status="Graduated",
            attendance=99.0,
            city="Themyscira",
            tags=["Alumni", "Ambassador"],
            extra_attributes={"title": "Princess"},
        )
        self.assertEqual(updated.phone, "+1-555-1122")
        self.assertEqual(updated.status, "Graduated")
        self.assertEqual(updated.city, "Themyscira")
        self.assertEqual(updated.extra_attributes["title"], "Princess")

    def test_statistics_calculation(self):
        self.manager.add_student(
            student_id="STU-01",
            name="Student One",
            email="s1@test.com",
            age=20,
            course="CS",
            gpa=4.0,
            attendance=100.0,
        )
        self.manager.add_student(
            student_id="STU-02",
            name="Student Two",
            email="s2@test.com",
            age=21,
            course="CS",
            gpa=3.0,
            attendance=90.0,
        )
        stats = self.manager.get_statistics()
        self.assertEqual(stats["total_students"], 2)
        self.assertEqual(stats["average_gpa"], 3.5)
        self.assertEqual(stats["highest_gpa"], 4.0)
        self.assertEqual(stats["lowest_gpa"], 3.0)
        self.assertEqual(stats["average_attendance"], 95.0)
        self.assertEqual(stats["honor_roll_count"], 1)
        self.assertEqual(stats["grade_distribution"]["A+"], 1)
        self.assertEqual(stats["grade_distribution"]["B+"], 1)

    def test_seed_sample_students(self):
        seeded = self.manager.seed_sample_students()
        self.assertGreaterEqual(len(seeded), 5)
        all_students = self.manager.get_all_students()
        self.assertGreaterEqual(len(all_students), 5)


if __name__ == "__main__":
    unittest.main()
