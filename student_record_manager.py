"""Student Record Manager (All-in-One Standalone Version)

A complete, self-contained Python program for managing student records.
Features:
1. Add Student (with unique ID and email check)
2. Validate Email using Regex (RFC 5322 compliant)
3. Save Data to File (atomic JSON storage)
4. Read Student Data (table format & search)
5. Handle Invalid Input using Custom Exceptions
"""

import json
import os
from pathlib import Path
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


# =====================================================================
# 1. CUSTOM EXCEPTION HIERARCHY
# =====================================================================

class StudentRecordError(Exception):
    """Base exception for all Student Record Manager errors."""
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(StudentRecordError):
    """Base exception for invalid input data."""
    pass


class InvalidEmailError(ValidationError):
    """Raised when an email fails regex validation."""
    def __init__(self, email: str, reason: str = "Invalid email format") -> None:
        super().__init__(f"Invalid Email '{email}': {reason}")
        self.email = email
        self.reason = reason


class InvalidStudentIdError(ValidationError):
    """Raised when a student ID does not conform to required format."""
    def __init__(self, student_id: str, reason: str = "ID must be 3-20 alphanumeric characters") -> None:
        super().__init__(f"Invalid Student ID '{student_id}': {reason}")
        self.student_id = student_id


class InvalidNameError(ValidationError):
    """Raised when a student name is empty, too short, or contains numbers/illegal symbols."""
    def __init__(self, name: str, reason: str = "Name must contain only letters and spaces (min 2 chars)") -> None:
        super().__init__(f"Invalid Name '{name}': {reason}")
        self.name = name


class InvalidAgeError(ValidationError):
    """Raised when age is non-integer or outside academic range [10, 120]."""
    def __init__(self, age: Any, reason: str = "Age must be an integer between 10 and 120") -> None:
        super().__init__(f"Invalid Age '{age}': {reason}")
        self.age = age


class InvalidGPAError(ValidationError):
    """Raised when GPA is not a number or outside [0.0, 4.0]."""
    def __init__(self, gpa: Any, reason: str = "GPA must be a decimal between 0.0 and 4.0") -> None:
        super().__init__(f"Invalid GPA '{gpa}': {reason}")
        self.gpa = gpa


class DuplicateStudentError(StudentRecordError):
    """Raised when adding a student whose ID or Email is already registered."""
    def __init__(self, field: str, value: str) -> None:
        super().__init__(f"Duplicate record: A student with {field} '{value}' already exists.")
        self.field = field
        self.value = value


class StudentNotFoundError(StudentRecordError):
    """Raised when a query for a student ID yields no results."""
    def __init__(self, student_id: str) -> None:
        super().__init__(f"Student with ID '{student_id}' was not found.")
        self.student_id = student_id


class StorageError(StudentRecordError):
    """Raised when reading or writing to the storage file fails."""
    def __init__(self, operation: str, path: str, err: Exception | None = None) -> None:
        msg = f"Failed to {operation} student records at '{path}'"
        if err:
            msg += f": {err}"
        super().__init__(msg)


# =====================================================================
# 2. VALIDATION UTILITIES (REGEX & TYPE CHECKS)
# =====================================================================

# Regex explanation:
# ^[a-zA-Z0-9]                     : Starts with alphanumeric
# ([a-zA-Z0-9._%+-]*[a-zA-Z0-9])?  : Allowed special chars internally, no trailing dot before @
# @                                : Mandatory @ separator
# [a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])? : Domain name with optional hyphens
# (?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)* : Optional subdomains (e.g. .edu.in)
# \.[a-zA-Z]{2,}$                  : Valid Top-Level Domain of 2 or more letters
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9._%+-]*[a-zA-Z0-9])?"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$"
)

STUDENT_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{3,20}$")
NAME_REGEX = re.compile(r"^[A-Za-z\s'\-\.]{2,100}$")


def validate_email(email: str) -> str:
    """Validate student email using Regular Expressions."""
    if not isinstance(email, str):
        raise InvalidEmailError(str(email), "Email must be text")
    cleaned = email.strip()
    if not cleaned:
        raise InvalidEmailError("", "Email cannot be empty")
    if len(cleaned) > 254:
        raise InvalidEmailError(cleaned, "Email exceeds 254 characters")
    if ".." in cleaned:
        raise InvalidEmailError(cleaned, "Email cannot contain consecutive dots ('..')")
    if not EMAIL_REGEX.match(cleaned):
        raise InvalidEmailError(cleaned, "Must follow standard format (e.g., student@domain.com)")
    return cleaned.lower()


def validate_student_id(student_id: str) -> str:
    """Validate student ID format."""
    if not isinstance(student_id, str):
        raise InvalidStudentIdError(str(student_id), "ID must be a string")
    cleaned = student_id.strip()
    if not cleaned:
        raise InvalidStudentIdError("", "Student ID cannot be empty")
    if not STUDENT_ID_REGEX.match(cleaned):
        raise InvalidStudentIdError(cleaned, "Must be 3-20 alphanumeric characters, hyphens, or underscores (e.g., STU-101)")
    return cleaned.upper()


def validate_name(name: str) -> str:
    """Validate student full name."""
    if not isinstance(name, str):
        raise InvalidNameError(str(name), "Name must be a string")
    cleaned = name.strip()
    if not cleaned:
        raise InvalidNameError("", "Name cannot be empty")
    if len(cleaned) < 2:
        raise InvalidNameError(cleaned, "Name must be at least 2 characters long")
    if not NAME_REGEX.match(cleaned):
        raise InvalidNameError(cleaned, "Name may only contain letters, spaces, hyphens, and apostrophes")
    return " ".join(cleaned.split())


def validate_age(age_val: int | str) -> int:
    """Validate student age."""
    if isinstance(age_val, float):
        raise InvalidAgeError(age_val, "Age must be an integer, not a float")
    if isinstance(age_val, str) and "." in age_val:
        raise InvalidAgeError(age_val, "Age must be a whole number without decimals")
    try:
        age = int(age_val)
    except (ValueError, TypeError):
        raise InvalidAgeError(age_val, "Age must be a valid integer number")
    if age < 10 or age > 120:
        raise InvalidAgeError(age, "Age must be between 10 and 120 years")
    return age


def validate_gpa(gpa_val: float | int | str) -> float:
    """Validate student Grade Point Average (GPA)."""
    try:
        gpa = float(gpa_val)
    except (ValueError, TypeError):
        raise InvalidGPAError(gpa_val, "GPA must be a valid decimal number")
    if gpa < 0.0 or gpa > 4.0:
        raise InvalidGPAError(gpa, "GPA must be between 0.00 and 4.00")
    return round(gpa, 2)


# =====================================================================
# 3. STUDENT DOMAIN MODEL
# =====================================================================

@dataclass
class Student:
    """Represents a student academic record."""
    student_id: str
    name: str
    email: str
    age: int
    course: str
    gpa: float
    created_at: str

    @classmethod
    def create(
        cls,
        student_id: str,
        name: str,
        email: str,
        age: int | str,
        course: str = "General",
        gpa: float | str = 0.0,
        created_at: str | None = None,
    ) -> "Student":
        """Factory method that validates all inputs before creating instance."""
        valid_id = validate_student_id(student_id)
        valid_name = validate_name(name)
        valid_email = validate_email(email)
        valid_age = validate_age(age)
        valid_gpa = validate_gpa(gpa)
        clean_course = course.strip() if isinstance(course, str) and course.strip() else "General"
        timestamp = created_at or datetime.now(timezone.utc).isoformat()

        return cls(
            student_id=valid_id,
            name=valid_name,
            email=valid_email,
            age=valid_age,
            course=clean_course,
            gpa=valid_gpa,
            created_at=timestamp,
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        return cls.create(
            student_id=data["student_id"],
            name=data["name"],
            email=data["email"],
            age=data["age"],
            course=data.get("course", "General"),
            gpa=data.get("gpa", 0.0),
            created_at=data.get("created_at"),
        )


# =====================================================================
# 4. FILE STORAGE (CRASH-SAFE ATOMIC JSON)
# =====================================================================

class JsonStorage:
    """Handles JSON file persistence with atomic write safety."""
    def __init__(self, file_path: str = "students.json") -> None:
        self.file_path = Path(file_path)

    def save(self, students: list[Student]) -> None:
        """Atomically save student records to file using temporary buffer."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
            payload = [s.to_dict() for s in students]
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.file_path)
        except Exception as e:
            raise StorageError("save", str(self.file_path), e) from e

    def load(self) -> list[Student]:
        """Read student records from file."""
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                records = json.loads(content)
            return [Student.from_dict(item) for item in records]
        except Exception as e:
            raise StorageError("load", str(self.file_path), e) from e


# =====================================================================
# 5. STUDENT RECORD MANAGER (BUSINESS LOGIC)
# =====================================================================

class StudentRecordManager:
    """Coordinates student CRUD operations, queries, and file persistence."""
    def __init__(self, storage: JsonStorage | None = None) -> None:
        self.storage = storage or JsonStorage()
        self._students: dict[str, Student] = {}
        self._email_index: dict[str, str] = {}
        self.load_from_file()

    def load_from_file(self) -> None:
        """Read data from file into memory."""
        self._students.clear()
        self._email_index.clear()
        for s in self.storage.load():
            self._students[s.student_id] = s
            self._email_index[s.email.lower()] = s.student_id

    def save_to_file(self) -> None:
        """Write in-memory data to file."""
        self.storage.save(list(self._students.values()))

    def add_student(
        self,
        student_id: str,
        name: str,
        email: str,
        age: int | str,
        course: str = "General",
        gpa: float | str = 0.0,
    ) -> Student:
        """Validate, add, and persist a new student."""
        new_student = Student.create(
            student_id=student_id,
            name=name,
            email=email,
            age=age,
            course=course,
            gpa=gpa,
        )

        # Check for duplicates
        if new_student.student_id in self._students:
            raise DuplicateStudentError("Student ID", new_student.student_id)
        if new_student.email.lower() in self._email_index:
            raise DuplicateStudentError("Email address", new_student.email)

        self._students[new_student.student_id] = new_student
        self._email_index[new_student.email.lower()] = new_student.student_id
        self.save_to_file()
        return new_student

    def get_student(self, student_id: str) -> Student:
        """Look up a student by ID."""
        clean_id = validate_student_id(student_id)
        if clean_id not in self._students:
            raise StudentNotFoundError(clean_id)
        return self._students[clean_id]

    def get_all_students(self) -> list[Student]:
        """Return all student records."""
        return sorted(self._students.values(), key=lambda s: s.student_id)

    def search_students(self, keyword: str) -> list[Student]:
        """Search students by ID, Name, Email, or Course."""
        q = keyword.strip().lower()
        if not q:
            return self.get_all_students()
        return [
            s for s in self._students.values()
            if q in s.student_id.lower() or q in s.name.lower() or q in s.email.lower() or q in s.course.lower()
        ]

    def delete_student(self, student_id: str) -> Student:
        """Delete student record by ID."""
        target = self.get_student(student_id)
        del self._students[target.student_id]
        self._email_index.pop(target.email.lower(), None)
        self.save_to_file()
        return target


# =====================================================================
# 6. TERMINAL USER INTERFACE (CLI)
# =====================================================================

def render_table(students: list[Student]) -> None:
    """Print student records in formatted ASCII table."""
    if not students:
        print("\n[!] No student records found.")
        return

    col_id, col_name, col_email, col_age, col_course, col_gpa = 12, 20, 28, 5, 18, 6
    sep = f"+{'-'*(col_id+2)}+{'-'*(col_name+2)}+{'-'*(col_email+2)}+{'-'*(col_age+2)}+{'-'*(col_course+2)}+{'-'*(col_gpa+2)}+"
    print("\n" + sep)
    print(f"| {'ID'.ljust(col_id)} | {'NAME'.ljust(col_name)} | {'EMAIL'.ljust(col_email)} | {'AGE'.rjust(col_age)} | {'COURSE'.ljust(col_course)} | {'GPA'.rjust(col_gpa)} |")
    print(sep)
    for s in students:
        print(f"| {s.student_id[:col_id].ljust(col_id)} | {s.name[:col_name].ljust(col_name)} | {s.email[:col_email].ljust(col_email)} | {str(s.age).rjust(col_age)} | {s.course[:col_course].ljust(col_course)} | {f'{s.gpa:.2f}'.rjust(col_gpa)} |")
    print(sep)
    print(f"Total: {len(students)} student(s)\n")


def prompt_validated(label: str, validator_fn):
    """Prompt user repeatedly until input passes validation or user types 'cancel'."""
    while True:
        try:
            val = input(label).strip()
            if val.lower() == "cancel":
                return None
            return validator_fn(val)
        except ValidationError as e:
            print(f"  [X] Error: {e.message}")
            print("  (Type 'cancel' to abort and return to menu)")


def main():
    manager = StudentRecordManager()

    while True:
        print("\n" + "=" * 55)
        print("          STUDENT RECORD MANAGER (CLI)")
        print("=" * 55)
        print(" 1. Add Student (with Regex Email & Input Validation)")
        print(" 2. View All Students (Read from File)")
        print(" 3. Search Student Records")
        print(" 4. Find Student by ID")
        print(" 5. Delete Student Record")
        print(" 0. Exit")
        print("-" * 55)

        try:
            choice = input("Enter choice (0-5): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break

        if choice == "1":
            print("\n--- Add New Student --- (Type 'cancel' to abort)")
            try:
                sid = prompt_validated("Student ID (e.g. STU-101): ", validate_student_id)
                if sid is None: continue
                name = prompt_validated("Full Name: ", validate_name)
                if name is None: continue
                email = prompt_validated("Email (Regex validated): ", validate_email)
                if email is None: continue
                age = prompt_validated("Age (10 - 120): ", validate_age)
                if age is None: continue
                course = input("Course [General]: ").strip() or "General"
                gpa = prompt_validated("GPA (0.00 - 4.00) [0.0]: ", lambda v: validate_gpa(v or 0.0))
                if gpa is None: continue

                new_s = manager.add_student(sid, name, email, age, course, gpa)
                print(f"\n[+] Success: Student '{new_s.name}' ({new_s.student_id}) enrolled and saved to file!")
            except DuplicateStudentError as e:
                print(f"\n[!] Duplicate Error: {e.message}")
            except StorageError as e:
                print(f"\n[!] Storage Error: {e.message}")

        elif choice == "2":
            render_table(manager.get_all_students())

        elif choice == "3":
            kw = input("\nEnter search keyword (name/ID/email/course): ").strip()
            matches = manager.search_students(kw)
            render_table(matches)

        elif choice == "4":
            sid = input("\nEnter Student ID to find: ").strip()
            try:
                s = manager.get_student(sid)
                render_table([s])
            except StudentNotFoundError as e:
                print(f"[!] Error: {e.message}")
            except ValidationError as e:
                print(f"[!] Error: {e.message}")

        elif choice == "5":
            sid = input("\nEnter Student ID to delete: ").strip()
            try:
                deleted = manager.delete_student(sid)
                print(f"[+] Success: Removed '{deleted.name}' ({deleted.student_id}) and updated file.")
            except StudentNotFoundError as e:
                print(f"[!] Error: {e.message}")

        elif choice == "0":
            print("\nExiting Student Record Manager. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid choice. Enter 0, 1, 2, 3, 4, or 5.")

        input("Press Enter to continue...")


if __name__ == "__main__":
    main()
