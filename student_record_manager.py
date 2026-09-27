"""Student Record Manager (All-in-One Standalone Version)

A complete, self-contained Python program for managing student records.
Features:
1. Add Student (with unique ID, email check, and all extra attributes)
2. Validate Email & Phone using Regular Expressions (RFC 5322)
3. Save Data to File (atomic JSON storage with crash safety)
4. Read Student Data (table format, multi-criteria search & statistics)
5. Handle Invalid Input using Custom Exceptions Hierarchy
6. Extensible attributes (Phone, Gender, Semester, Status, Attendance %, Tags, Custom Notes)
"""

import json
import os
from pathlib import Path
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


# =====================================================================
# 1. CUSTOM EXCEPTION HIERARCHY
# =====================================================================

class StudentRecordError(Exception):
    """Base exception for all Student Record Manager errors."""
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(StudentRecordError):
    """Base exception for invalid input data."""
    pass


class InvalidEmailError(ValidationError):
    """Raised when an email fails regex validation."""
    def __init__(self, email: str, reason: str = "Invalid email format") -> None:
        super().__init__(f"Invalid Email '{email}': {reason}", {"email": email, "reason": reason})
        self.email = email
        self.reason = reason


class InvalidStudentIdError(ValidationError):
    """Raised when a student ID does not conform to required format."""
    def __init__(self, student_id: str, reason: str = "ID must be 3-20 alphanumeric characters") -> None:
        super().__init__(f"Invalid Student ID '{student_id}': {reason}", {"student_id": student_id, "reason": reason})
        self.student_id = student_id
        self.reason = reason


class InvalidNameError(ValidationError):
    """Raised when a student name is empty, too short, or contains numbers/illegal symbols."""
    def __init__(self, name: str, reason: str = "Name must contain only letters and spaces (min 2 chars)") -> None:
        super().__init__(f"Invalid Name '{name}': {reason}", {"name": name, "reason": reason})
        self.name = name
        self.reason = reason


class InvalidAgeError(ValidationError):
    """Raised when age is non-integer or outside academic range [10, 120]."""
    def __init__(self, age: Any, reason: str = "Age must be an integer between 10 and 120") -> None:
        super().__init__(f"Invalid Age '{age}': {reason}", {"age": str(age), "reason": reason})
        self.age = age
        self.reason = reason


class InvalidGPAError(ValidationError):
    """Raised when GPA is not a number or outside [0.0, 4.0]."""
    def __init__(self, gpa: Any, reason: str = "GPA must be a decimal between 0.0 and 4.0") -> None:
        super().__init__(f"Invalid GPA '{gpa}': {reason}", {"gpa": str(gpa), "reason": reason})
        self.gpa = gpa
        self.reason = reason


class InvalidPhoneError(ValidationError):
    """Raised when phone number fails regex or digit count validation."""
    def __init__(self, phone: str, reason: str = "Invalid phone format") -> None:
        super().__init__(f"Invalid Phone '{phone}': {reason}", {"phone": phone, "reason": reason})
        self.phone = phone
        self.reason = reason


class InvalidAttendanceError(ValidationError):
    """Raised when attendance percentage is outside [0.0, 100.0]."""
    def __init__(self, attendance: Any, reason: str = "Attendance must be between 0.0% and 100.0%") -> None:
        super().__init__(f"Invalid Attendance '{attendance}': {reason}", {"attendance": str(attendance), "reason": reason})
        self.attendance = attendance
        self.reason = reason


class InvalidStatusError(ValidationError):
    """Raised when enrollment status is not one of Active, Graduated, On Leave, Probation."""
    def __init__(self, status: str, reason: str = "Unrecognized status") -> None:
        super().__init__(f"Invalid Status '{status}': {reason}", {"status": status, "reason": reason})
        self.status = status
        self.reason = reason


class DuplicateStudentError(StudentRecordError):
    """Raised when adding a student whose ID or Email is already registered."""
    def __init__(self, field: str, value: str) -> None:
        super().__init__(f"Duplicate record: A student with {field} '{value}' already exists.", {"field": field, "value": value})
        self.field = field
        self.value = value


class StudentNotFoundError(StudentRecordError):
    """Raised when a query for a student ID yields no results."""
    def __init__(self, student_id: str) -> None:
        super().__init__(f"Student with ID '{student_id}' was not found.", {"student_id": student_id})
        self.student_id = student_id


class StorageError(StudentRecordError):
    """Raised when reading or writing to the storage file fails."""
    def __init__(self, operation: str, path: str, err: Exception | None = None) -> None:
        msg = f"Failed to {operation} student records at '{path}'"
        if err:
            msg += f": {err}"
        super().__init__(msg, {"operation": operation, "path": path, "error": str(err)})


# =====================================================================
# 2. VALIDATION UTILITIES (REGEX & TYPE CHECKS)
# =====================================================================

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9._%+-]*[a-zA-Z0-9])?"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$"
)

STUDENT_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{3,20}$")
NAME_REGEX = re.compile(r"^[A-Za-z\s'\-\.]{2,100}$")
PHONE_REGEX = re.compile(r"^(?:\+?[0-9]{1,4}[-.\s]*)?(?:\([0-9]{1,6}\)[-.\s]*)?[0-9]{1,6}(?:[-.\s]?[0-9]{1,6})*$")
VALID_STATUSES = {"Active", "Graduated", "On Leave", "Probation"}


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


def validate_phone(phone_val: str | None, optional: bool = True) -> str:
    """Validate student phone number using Regex."""
    if phone_val is None or (isinstance(phone_val, str) and not phone_val.strip()):
        if optional:
            return ""
        raise InvalidPhoneError("", "Phone number cannot be empty")
    cleaned = str(phone_val).strip()
    digits_only = re.sub(r"\D", "", cleaned)
    if len(digits_only) < 7 or len(digits_only) > 15:
        raise InvalidPhoneError(cleaned, "Phone number must contain between 7 and 15 digits")
    if not PHONE_REGEX.match(cleaned):
        raise InvalidPhoneError(cleaned, "Phone format invalid (e.g. +1-555-0143 or 9876543210)")
    return cleaned


def validate_attendance(attendance_val: float | int | str) -> float:
    """Validate student attendance percentage."""
    try:
        att = float(attendance_val)
    except (ValueError, TypeError):
        raise InvalidAttendanceError(attendance_val, "Attendance must be a numeric percentage")
    if att < 0.0 or att > 100.0:
        raise InvalidAttendanceError(att, "Attendance percentage must be between 0.0% and 100.0%")
    return round(att, 1)


def validate_status(status_val: str) -> str:
    """Validate student enrollment status."""
    if not isinstance(status_val, str):
        raise InvalidStatusError(str(status_val), "Status must be a string")
    cleaned = status_val.strip().title()
    if cleaned.lower() in ("on-leave", "on leave", "leave"):
        cleaned = "On Leave"
    if cleaned not in VALID_STATUSES:
        raise InvalidStatusError(status_val, f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}")
    return cleaned


def calculate_grade_letter(gpa: float) -> str:
    """Calculate letter grade from GPA."""
    if gpa >= 3.85: return "A+"
    if gpa >= 3.50: return "A"
    if gpa >= 3.00: return "B+"
    if gpa >= 2.50: return "B"
    if gpa >= 2.00: return "C"
    if gpa >= 1.00: return "D"
    return "F"


# =====================================================================
# 3. STUDENT DOMAIN MODEL
# =====================================================================

@dataclass
class Student:
    """Represents a student academic record with extensible attributes."""
    student_id: str
    name: str
    email: str
    age: int
    course: str
    gpa: float
    created_at: str
    phone: str = ""
    gender: str = ""
    semester: str = ""
    status: str = "Active"
    attendance: float = 100.0
    emergency_contact: str = ""
    city: str = ""
    tags: list[str] = field(default_factory=list)
    extra_attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def grade_letter(self) -> str:
        return calculate_grade_letter(self.gpa)

    @property
    def is_honor_roll(self) -> bool:
        return self.gpa >= 3.8

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
        phone: str = "",
        gender: str = "",
        semester: str = "",
        status: str = "Active",
        attendance: float | int | str = 100.0,
        emergency_contact: str = "",
        city: str = "",
        tags: list[str] | None = None,
        extra_attributes: dict[str, Any] | None = None,
    ) -> "Student":
        valid_id = validate_student_id(student_id)
        valid_name = validate_name(name)
        valid_email = validate_email(email)
        valid_age = validate_age(age)
        valid_gpa = validate_gpa(gpa)
        valid_phone = validate_phone(phone, optional=True)
        valid_att = validate_attendance(attendance if attendance is not None else 100.0)
        valid_stat = validate_status(status if status else "Active")

        clean_course = course.strip() if isinstance(course, str) and course.strip() else "General"
        timestamp = created_at or datetime.now(timezone.utc).isoformat()
        clean_tags = [str(t).strip() for t in (tags or []) if str(t).strip()]
        clean_extras = dict(extra_attributes) if extra_attributes and isinstance(extra_attributes, dict) else {}

        return cls(
            student_id=valid_id,
            name=valid_name,
            email=valid_email,
            age=valid_age,
            course=clean_course,
            gpa=valid_gpa,
            created_at=timestamp,
            phone=valid_phone,
            gender=str(gender or "").strip(),
            semester=str(semester or "").strip(),
            status=valid_stat,
            attendance=valid_att,
            emergency_contact=str(emergency_contact or "").strip(),
            city=str(city or "").strip(),
            tags=clean_tags,
            extra_attributes=clean_extras,
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["grade_letter"] = self.grade_letter
        data["is_honor_roll"] = self.is_honor_roll
        return data

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
            phone=data.get("phone", ""),
            gender=data.get("gender", ""),
            semester=data.get("semester", ""),
            status=data.get("status", "Active"),
            attendance=data.get("attendance", 100.0),
            emergency_contact=data.get("emergency_contact", ""),
            city=data.get("city", ""),
            tags=data.get("tags") or [],
            extra_attributes=data.get("extra_attributes") or {},
        )


# =====================================================================
# 4. FILE STORAGE (CRASH-SAFE ATOMIC JSON)
# =====================================================================

class JsonStorage:
    """Handles JSON file persistence with atomic write safety."""
    def __init__(self, file_path: str = "data/students.json") -> None:
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
        self._students.clear()
        self._email_index.clear()
        for s in self.storage.load():
            self._students[s.student_id] = s
            self._email_index[s.email.lower()] = s.student_id

    def save_to_file(self) -> None:
        self.storage.save(list(self._students.values()))

    def add_student(
        self,
        student_id: str,
        name: str,
        email: str,
        age: int | str,
        course: str = "General",
        gpa: float | str = 0.0,
        phone: str = "",
        gender: str = "",
        semester: str = "",
        status: str = "Active",
        attendance: float | int | str = 100.0,
        emergency_contact: str = "",
        city: str = "",
        tags: list[str] | None = None,
        extra_attributes: dict[str, Any] | None = None,
    ) -> Student:
        new_student = Student.create(
            student_id=student_id,
            name=name,
            email=email,
            age=age,
            course=course,
            gpa=gpa,
            phone=phone,
            gender=gender,
            semester=semester,
            status=status,
            attendance=attendance,
            emergency_contact=emergency_contact,
            city=city,
            tags=tags,
            extra_attributes=extra_attributes,
        )

        if new_student.student_id in self._students:
            raise DuplicateStudentError("Student ID", new_student.student_id)
        if new_student.email.lower() in self._email_index:
            raise DuplicateStudentError("Email address", new_student.email)

        self._students[new_student.student_id] = new_student
        self._email_index[new_student.email.lower()] = new_student.student_id
        self.save_to_file()
        return new_student

    def get_student(self, student_id: str) -> Student:
        clean_id = validate_student_id(student_id)
        if clean_id not in self._students:
            raise StudentNotFoundError(clean_id)
        return self._students[clean_id]

    def get_all_students(self, sort_by: str = "id", reverse: bool = False) -> list[Student]:
        students = list(self._students.values())
        if sort_by == "name":
            return sorted(students, key=lambda s: s.name.lower(), reverse=reverse)
        if sort_by == "gpa":
            return sorted(students, key=lambda s: s.gpa, reverse=True if not reverse else False)
        if sort_by == "course":
            return sorted(students, key=lambda s: s.course.lower(), reverse=reverse)
        return sorted(students, key=lambda s: s.student_id, reverse=reverse)

    def search_students(self, keyword: str = "") -> list[Student]:
        q = keyword.strip().lower()
        if not q:
            return self.get_all_students()
        matches = []
        for s in self._students.values():
            in_core = (
                q in s.student_id.lower()
                or q in s.name.lower()
                or q in s.email.lower()
                or q in s.course.lower()
                or q in s.phone.lower()
                or q in s.city.lower()
            )
            in_tags = any(q in t.lower() for t in s.tags)
            if in_core or in_tags:
                matches.append(s)
        return matches

    def delete_student(self, student_id: str) -> Student:
        target = self.get_student(student_id)
        del self._students[target.student_id]
        self._email_index.pop(target.email.lower(), None)
        self.save_to_file()
        return target

    def get_statistics(self) -> dict[str, Any]:
        students = list(self._students.values())
        total = len(students)
        if total == 0:
            return {
                "total_students": 0, "average_gpa": 0.0, "highest_gpa": 0.0,
                "lowest_gpa": 0.0, "average_attendance": 0.0, "honor_roll_count": 0,
            }
        gpas = [s.gpa for s in students]
        atts = [s.attendance for s in students]
        return {
            "total_students": total,
            "average_gpa": round(sum(gpas) / total, 2),
            "highest_gpa": max(gpas),
            "lowest_gpa": min(gpas),
            "average_attendance": round(sum(atts) / total, 1),
            "honor_roll_count": sum(1 for s in students if s.is_honor_roll),
        }

    def seed_sample_students(self) -> list[Student]:
        samples = [
            {"student_id": "STU-1001", "name": "Sarah Connor", "email": "sarah.connor@cyberdyne.edu", "age": 21, "course": "Computer Science", "gpa": 3.95, "phone": "+1-555-0143", "gender": "Female", "semester": "Sem 6", "status": "Active", "attendance": 98.5, "city": "Los Angeles", "tags": ["Dean's List", "AI Lab"]},
            {"student_id": "STU-1002", "name": "Marcus Vance", "email": "m.vance@stanford.edu", "age": 22, "course": "Artificial Intelligence", "gpa": 3.88, "phone": "+1-555-0284", "gender": "Male", "semester": "Sem 7", "status": "Active", "attendance": 96.0, "city": "Palo Alto", "tags": ["Robotics"]},
            {"student_id": "STU-1003", "name": "Amina Mansoor", "email": "amina.m@oxford.ac.uk", "age": 20, "course": "Data Science", "gpa": 3.75, "phone": "+44-20-7946-0912", "gender": "Female", "semester": "Sem 4", "status": "Active", "attendance": 94.2, "city": "Oxford", "tags": ["Python", "Hackathon"]},
        ]
        added = []
        for s in samples:
            if s["student_id"] not in self._students and s["email"].lower() not in self._email_index:
                added.append(self.add_student(**s))
        return added


# =====================================================================
# 6. TERMINAL USER INTERFACE (CLI)
# =====================================================================

def render_table(students: list[Student]) -> None:
    if not students:
        print("\n[!] No student records found.")
        return
    col_id, col_name, col_email, col_course, col_gpa, col_status = 12, 18, 26, 18, 8, 10
    sep = f"+{'-'*(col_id+2)}+{'-'*(col_name+2)}+{'-'*(col_email+2)}+{'-'*(col_course+2)}+{'-'*(col_gpa+2)}+{'-'*(col_status+2)}+"
    print("\n" + sep)
    print(f"| {'ID'.ljust(col_id)} | {'NAME'.ljust(col_name)} | {'EMAIL'.ljust(col_email)} | {'COURSE'.ljust(col_course)} | {'GPA'.rjust(col_gpa)} | {'STATUS'.ljust(col_status)} |")
    print(sep)
    for s in students:
        gpa_str = f"{s.gpa:.2f} ({s.grade_letter})"
        print(f"| {s.student_id[:col_id].ljust(col_id)} | {s.name[:col_name].ljust(col_name)} | {s.email[:col_email].ljust(col_email)} | {s.course[:col_course].ljust(col_course)} | {gpa_str.rjust(col_gpa)} | {s.status[:col_status].ljust(col_status)} |")
    print(sep)
    print(f"Total: {len(students)} student(s)\n")


def prompt_validated(label: str, validator_fn):
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
        print("\n" + "=" * 60)
        print("       🎓 STUDENT RECORD MANAGER (PYTHON BACKEND) 🎓")
        print("=" * 60)
        print(" 1. Add Student (with Regex Email, Phone & Extra Details)")
        print(" 2. View All Students (Read from File)")
        print(" 3. Search Student Records (by Name, ID, Course, Tags)")
        print(" 4. Find Student Details by ID (Full Dossier)")
        print(" 5. View Academic Analytics & Statistics")
        print(" 6. Seed Realistic Sample Students")
        print(" 7. Delete Student Record")
        print(" 0. Exit")
        print("-" * 60)

        try:
            choice = input("Enter choice (0-7): ").strip()
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
                course = input("Course/Department [General]: ").strip() or "General"
                gpa = prompt_validated("GPA (0.00 - 4.00) [0.0]: ", lambda v: validate_gpa(v or 0.0))
                if gpa is None: continue

                # Extra Possibilities
                print("\n  [Extra Possibilities - Press Enter to Skip]")
                phone_in = input("  Phone (Regex validated): ").strip()
                phone = validate_phone(phone_in, optional=True) if phone_in else ""
                gender = input("  Gender: ").strip()
                semester = input("  Semester (e.g. Semester 4): ").strip()
                status_in = input("  Status [Active]: ").strip()
                status = validate_status(status_in) if status_in else "Active"
                att_in = input("  Attendance % [100.0]: ").strip()
                att = validate_attendance(att_in) if att_in else 100.0
                emergency = input("  Emergency Contact: ").strip()
                city = input("  City/Address: ").strip()
                tags_in = input("  Tags/Skills (comma-separated): ").strip()
                tags = [t.strip() for t in tags_in.split(",") if t.strip()] if tags_in else []

                new_s = manager.add_student(
                    student_id=sid, name=name, email=email, age=age,
                    course=course, gpa=gpa, phone=phone, gender=gender,
                    semester=semester, status=status, attendance=att,
                    emergency_contact=emergency, city=city, tags=tags,
                )
                print(f"\n[+] Success: Student '{new_s.name}' ({new_s.student_id}) enrolled and saved to file!")
                if new_s.is_honor_roll:
                    print("    🎉 Honor Roll Student (GPA >= 3.8)!")
            except ValidationError as e:
                print(f"\n[!] Validation Error: {e.message}")
            except DuplicateStudentError as e:
                print(f"\n[!] Duplicate Error: {e.message}")
            except StorageError as e:
                print(f"\n[!] Storage Error: {e.message}")

        elif choice == "2":
            render_table(manager.get_all_students())

        elif choice == "3":
            kw = input("\nEnter search keyword: ").strip()
            matches = manager.search_students(kw)
            render_table(matches)

        elif choice == "4":
            sid = input("\nEnter Student ID: ").strip()
            try:
                s = manager.get_student(sid)
                print("\n" + "=" * 50)
                print(f"  STUDENT DOSSIER: {s.name} ({s.student_id})")
                print("=" * 50)
                print(f"  Email:              {s.email}")
                print(f"  Phone:              {s.phone or 'N/A'}")
                print(f"  Age:                {s.age}")
                print(f"  Gender:             {s.gender or 'N/A'}")
                print(f"  Course/Dept:        {s.course}")
                print(f"  Semester:           {s.semester or 'N/A'}")
                print(f"  Status:             {s.status}")
                print(f"  GPA:                {s.gpa:.2f} (Grade: {s.grade_letter})")
                print(f"  Attendance:         {s.attendance:.1f}%")
                print(f"  Emergency Contact:  {s.emergency_contact or 'N/A'}")
                print(f"  City:               {s.city or 'N/A'}")
                print(f"  Tags:               {', '.join(s.tags) if s.tags else 'None'}")
                if s.extra_attributes:
                    print("  Custom Attributes:")
                    for k, v in s.extra_attributes.items():
                        print(f"    - {k}: {v}")
                print("=" * 50)
            except StudentNotFoundError as e:
                print(f"[!] Error: {e.message}")
            except ValidationError as e:
                print(f"[!] Error: {e.message}")

        elif choice == "5":
            stats = manager.get_statistics()
            print("\n" + "=" * 45)
            print("         ACADEMIC ANALYTICS")
            print("=" * 45)
            print(f" Total Students:     {stats['total_students']}")
            print(f" Average GPA:        {stats['average_gpa']:.2f}")
            print(f" Highest GPA:        {stats['highest_gpa']:.2f}")
            print(f" Lowest GPA:         {stats['lowest_gpa']:.2f}")
            print(f" Average Attendance: {stats['average_attendance']:.1f}%")
            print(f" Honor Roll (>=3.8): {stats['honor_roll_count']}")
            print("=" * 45)

        elif choice == "6":
            added = manager.seed_sample_students()
            print(f"\n[+] Seeded {len(added)} realistic student record(s) with full extra attributes into file!")

        elif choice == "7":
            sid = input("\nEnter Student ID to delete: ").strip()
            try:
                deleted = manager.delete_student(sid)
                print(f"[+] Success: Removed '{deleted.name}' ({deleted.student_id}) and updated file.")
            except StudentNotFoundError as e:
                print(f"[!] Error: {e.message}")

        elif choice == "0":
            print("\nExiting Student Record Manager. Goodbye!")
            sys.exit(0)

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
