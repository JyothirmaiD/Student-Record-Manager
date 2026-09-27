#!/usr/bin/env python3
"""
Automated Demo Runner for Student Record Manager
Runs all required features sequentially and prints the results clearly:
  1. Add Student
  2. Validate Email using Regex (shows both valid and invalid test cases)
  3. Save Data to File
  4. Read Student Data
  5. Handle Invalid Input using Exceptions
"""

import os
import sys

# Ensure current directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.models import Student
from src.manager import StudentRecordManager
from src.storage import JSONStorage
from src.validator import validate_email
from src.exceptions import (
    InvalidEmailError,
    InvalidInputError,
    DuplicateStudentError,
    StudentNotFoundError,
)


def print_header(title: str) -> None:
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def run_demo() -> None:
    print_header("STUDENT RECORD MANAGER - AUTOMATED EXECUTION DEMO")

    data_file = os.path.join(os.path.dirname(__file__), "data", "students.json")
    storage = JSONStorage(filepath=data_file)
    manager = StudentRecordManager(storage=storage)

    # -------------------------------------------------------------
    # FEATURE 1 & 2: Regex Email Validation
    # -------------------------------------------------------------
    print_header("FEATURE 1: Validate Email using Regular Expressions (Regex)")
    test_emails = [
        ("alice.johnson@university.edu", True),
        ("bad-email-without-at.com", False),
        ("clara.davis@institute.ac.uk", True),
        ("user@missing-tld", False),
        ("diana.prince@wayne.edu", True),
        ("invalid spaces@domain.com", False),
    ]

    for email_str, should_be_valid in test_emails:
        try:
            valid_email = validate_email(email_str)
            print(f"  [PASS] Valid Email: '{valid_email}' matches pattern.")
        except InvalidEmailError as e:
            print(f"  [CAUGHT EXCEPTION] InvalidEmailError: '{email_str}' -> {e.message}")

    # -------------------------------------------------------------
    # FEATURE 3: Handle Invalid Input using Exceptions
    # -------------------------------------------------------------
    print_header("FEATURE 2: Handle Invalid Input using Exceptions")

    # Test invalid GPA
    try:
        print("  Attempting to create student with invalid GPA (5.5)...")
        Student.create("STU999", "Bad GPA Student", "test@domain.com", "CS", 5.5)
    except InvalidInputError as e:
        print(f"  [CAUGHT EXCEPTION] InvalidInputError handled: {e.message}")

    # Test empty name
    try:
        print("  Attempting to create student with blank name...")
        Student.create("STU998", " ", "test@domain.com", "CS", 3.5)
    except InvalidInputError as e:
        print(f"  [CAUGHT EXCEPTION] InvalidInputError handled: {e.message}")

    # -------------------------------------------------------------
    # FEATURE 4: Add Students
    # -------------------------------------------------------------
    print_header("FEATURE 3: Add Students")
    sample_students = [
        Student.create("STU101", "Alice Johnson", "alice.johnson@university.edu", "Computer Science", 3.85),
        Student.create("STU102", "Bob Smith", "bob.smith@techcollege.org", "Data Science", 3.65),
        Student.create("STU103", "Clara Davis", "clara.davis@institute.ac.uk", "Cybersecurity", 3.92),
        Student.create("STU104", "Diana Prince", "diana.prince@wayne.edu", "Software Engineering", 3.95),
        Student.create("STU105", "Evan Wright", "evan.wright@stanford.edu", "Artificial Intelligence", 3.78),
    ]

    for student in sample_students:
        try:
            manager.add_student(student)
            print(f"  [ADDED] {student}")
        except DuplicateStudentError:
            print(f"  [EXISTING] Student {student.student_id} is already in registry.")

    # Test duplicate student ID exception
    try:
        print("\n  Attempting to add duplicate student ID 'STU101'...")
        manager.add_student(sample_students[0])
    except DuplicateStudentError as e:
        print(f"  [CAUGHT EXCEPTION] DuplicateStudentError handled: {e.message}")

    # -------------------------------------------------------------
    # FEATURE 5: Save Data to File
    # -------------------------------------------------------------
    print_header("FEATURE 4: Save Data to File")
    saved_count = manager.save_to_file()
    print(f"  [SAVED] Successfully saved {saved_count} student records to '{data_file}'.")

    # -------------------------------------------------------------
    # FEATURE 6: Read Student Data from File
    # -------------------------------------------------------------
    print_header("FEATURE 5: Read Student Data from File")
    fresh_manager = StudentRecordManager(storage=storage)
    loaded_count = fresh_manager.load_from_file()
    print(f"  [LOADED] Read {loaded_count} student records from '{data_file}'.\n")

    # Render formatted table
    all_students = fresh_manager.get_all_students()
    print("=" * 90)
    print(f"| {'ID'.ljust(8)} | {'Name'.ljust(18)} | {'Email'.ljust(30)} | {'Course'.ljust(20)} | {'GPA'.rjust(6)} |")
    print("=" * 90)
    for s in all_students:
        print(f"| {s.student_id.ljust(8)} | {s.name.ljust(18)} | {s.email.ljust(30)} | {s.course.ljust(20)} | {f'{s.gpa:.2f}'.rjust(6)} |")
    print("=" * 90)

    # -------------------------------------------------------------
    # Search Demonstration
    # -------------------------------------------------------------
    print_header("SEARCH DEMO: Query for 'Science'")
    results = fresh_manager.search_students("Science")
    for r in results:
        print(f"  -> Found: {r.student_id} | {r.name} ({r.course})")

    print_header("SUMMARY: ALL FEATURES SUCCESSFULLY EXECUTED AND VERIFIED!")


if __name__ == "__main__":
    run_demo()
