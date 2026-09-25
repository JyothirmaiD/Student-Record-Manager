"""Core manager orchestrating student record lifecycle and queries."""

from typing import Any
from student_manager.exceptions import (
    StudentNotFoundError,
    DuplicateStudentError,
    StudentRecordError,
)
from student_manager.models import Student
from student_manager.storage import BaseStorageHandler, JsonStorageHandler
from student_manager.validator import (
    validate_student_id,
    validate_email,
    validate_name,
    validate_age,
    validate_gpa,
)


class StudentRecordManager:
    """Business logic coordinator for student record CRUD operations."""

    def __init__(
        self,
        storage: BaseStorageHandler | None = None,
        auto_save: bool = True,
    ) -> None:
        self.storage = storage or JsonStorageHandler()
        self.auto_save = auto_save
        self._students: dict[str, Student] = {}
        self._email_index: dict[str, str] = {}
        self.load_from_file()

    def load_from_file(self) -> None:
        """Load student records from the configured storage handler."""
        self._students.clear()
        self._email_index.clear()
        records = self.storage.load()
        for student in records:
            self._students[student.student_id] = student
            self._email_index[student.email.lower()] = student.student_id

    def save_to_file(self) -> None:
        """Persist in-memory student records to storage."""
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
        """Validate and add a new student record to the system.

        Args:
            student_id: Unique identifier for student.
            name: Full name.
            email: Primary contact email.
            age: Student age.
            course: Academic program.
            gpa: Grade Point Average (0.0 to 4.0).

        Returns:
            The created and persisted Student instance.

        Raises:
            DuplicateStudentError: If student_id or email already exists.
            ValidationError: If any input fails validation.
        """
        # Create student (performs all validation and normalization)
        new_student = Student.create(
            student_id=student_id,
            name=name,
            email=email,
            age=age,
            course=course,
            gpa=gpa,
        )

        # Check uniqueness constraints
        if new_student.student_id in self._students:
            raise DuplicateStudentError("Student ID", new_student.student_id)

        email_key = new_student.email.lower()
        if email_key in self._email_index:
            raise DuplicateStudentError("Email address", new_student.email)

        # Store in-memory
        self._students[new_student.student_id] = new_student
        self._email_index[email_key] = new_student.student_id

        if self.auto_save:
            self.save_to_file()

        return new_student

    def get_student(self, student_id: str) -> Student:
        """Retrieve a student by their unique ID.

        Args:
            student_id: The ID of the student to fetch.

        Returns:
            The corresponding Student instance.

        Raises:
            StudentNotFoundError: If no student matches the given ID.
        """
        clean_id = validate_student_id(student_id)
        if clean_id not in self._students:
            raise StudentNotFoundError(clean_id)
        return self._students[clean_id]

    def get_all_students(self, sort_by: str = "id") -> list[Student]:
        """Return all student records sorted by specified field.

        Args:
            sort_by: One of 'id', 'name', 'gpa', or 'course'.

        Returns:
            List of student objects.
        """
        students = list(self._students.values())
        if sort_by == "name":
            return sorted(students, key=lambda s: s.name.lower())
        if sort_by == "gpa":
            return sorted(students, key=lambda s: s.gpa, reverse=True)
        if sort_by == "course":
            return sorted(students, key=lambda s: s.course.lower())
        # Default: sort by student ID
        return sorted(students, key=lambda s: s.student_id)

    def search_students(self, query: str) -> list[Student]:
        """Perform fuzzy matching across ID, name, email, and course.

        Args:
            query: Search keyword string.

        Returns:
            Matching list of students.
        """
        q = query.strip().lower()
        if not q:
            return self.get_all_students()

        matches = []
        for s in self._students.values():
            if (
                q in s.student_id.lower()
                or q in s.name.lower()
                or q in s.email.lower()
                or q in s.course.lower()
            ):
                matches.append(s)
        return matches

    def update_student(self, student_id: str, **updates: Any) -> Student:
        """Update fields of an existing student.

        Args:
            student_id: The ID of the student to update.
            **updates: Keyword arguments matching Student attributes.

        Returns:
            The updated Student record.

        Raises:
            StudentNotFoundError: If student does not exist.
            DuplicateStudentError: If updating to an email already in use.
            ValidationError: If any updated value is invalid.
        """
        existing = self.get_student(student_id)

        # Prepare updated values with fallback to existing
        new_name = validate_name(updates["name"]) if "name" in updates else existing.name
        new_age = validate_age(updates["age"]) if "age" in updates else existing.age
        new_course = (
            updates["course"].strip()
            if "course" in updates and str(updates["course"]).strip()
            else existing.course
        )
        new_gpa = validate_gpa(updates["gpa"]) if "gpa" in updates else existing.gpa

        new_email = existing.email
        if "email" in updates:
            candidate_email = validate_email(updates["email"])
            if (
                candidate_email != existing.email
                and candidate_email in self._email_index
                and self._email_index[candidate_email] != existing.student_id
            ):
                raise DuplicateStudentError("Email address", candidate_email)
            new_email = candidate_email

        # Remove old email index mapping if email changed
        if new_email != existing.email:
            self._email_index.pop(existing.email.lower(), None)
            self._email_index[new_email.lower()] = existing.student_id

        # Update student record
        updated_student = Student(
            student_id=existing.student_id,
            name=new_name,
            email=new_email,
            age=new_age,
            course=new_course,
            gpa=new_gpa,
            created_at=existing.created_at,
        )
        self._students[existing.student_id] = updated_student

        if self.auto_save:
            self.save_to_file()

        return updated_student

    def delete_student(self, student_id: str) -> Student:
        """Delete student record by ID.

        Args:
            student_id: ID of student to remove.

        Returns:
            The deleted Student object.

        Raises:
            StudentNotFoundError: If ID is not found.
        """
        target = self.get_student(student_id)
        del self._students[target.student_id]
        self._email_index.pop(target.email.lower(), None)

        if self.auto_save:
            self.save_to_file()

        return target

    def get_statistics(self) -> dict[str, Any]:
        """Calculate summary statistics over all enrolled students."""
        students = list(self._students.values())
        total = len(students)
        if total == 0:
            return {
                "total_students": 0,
                "average_gpa": 0.0,
                "highest_gpa": 0.0,
                "lowest_gpa": 0.0,
                "courses": {},
            }

        gpas = [s.gpa for s in students]
        courses: dict[str, int] = {}
        for s in students:
            courses[s.course] = courses.get(s.course, 0) + 1

        return {
            "total_students": total,
            "average_gpa": round(sum(gpas) / total, 2),
            "highest_gpa": max(gpas),
            "lowest_gpa": min(gpas),
            "courses": courses,
        }
