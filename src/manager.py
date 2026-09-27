"""Core business logic for managing student records."""

from typing import Dict, List, Optional
from src.models import Student
from src.storage import JSONStorage
from src.exceptions import DuplicateStudentError, StudentNotFoundError


class StudentRecordManager:
    """Manages the lifecycle, queries, and persistence of Student records."""

    def __init__(self, storage: Optional[JSONStorage] = None):
        self._students: Dict[str, Student] = {}
        self.storage = storage or JSONStorage()

    def add_student(self, student: Student) -> Student:
        """
        Add a new student to the in-memory registry.

        Args:
            student: Student instance to register.

        Returns:
            The added Student instance.

        Raises:
            DuplicateStudentError: If a student with the same ID already exists.
        """
        if student.student_id in self._students:
            raise DuplicateStudentError(student.student_id)

        self._students[student.student_id] = student
        return student

    def get_student(self, student_id: str) -> Student:
        """
        Retrieve a student by their ID.

        Args:
            student_id: The ID of the student.

        Returns:
            Student instance.

        Raises:
            StudentNotFoundError: If no student matches the ID.
        """
        norm_id = student_id.strip().upper()
        if norm_id not in self._students:
            raise StudentNotFoundError(norm_id)
        return self._students[norm_id]

    def get_all_students(self) -> List[Student]:
        """Return all registered students sorted by Student ID."""
        return sorted(self._students.values(), key=lambda s: s.student_id)

    def delete_student(self, student_id: str) -> Student:
        """
        Remove a student by ID.

        Args:
            student_id: The ID of the student to remove.

        Returns:
            The removed Student instance.

        Raises:
            StudentNotFoundError: If the student does not exist.
        """
        norm_id = student_id.strip().upper()
        if norm_id not in self._students:
            raise StudentNotFoundError(norm_id)
        return self._students.pop(norm_id)

    def search_students(self, query: str) -> List[Student]:
        """
        Search for students matching a query string across ID, Name, Email, or Course.

        Args:
            query: Search query string.

        Returns:
            List of matching Student instances.
        """
        q = query.strip().lower()
        if not q:
            return self.get_all_students()

        results = []
        for s in self._students.values():
            if (
                q in s.student_id.lower()
                or q in s.name.lower()
                or q in s.email.lower()
                or q in s.course.lower()
            ):
                results.append(s)
        return sorted(results, key=lambda s: s.student_id)

    def save_to_file(self) -> int:
        """
        Save all in-memory student records to disk.

        Returns:
            The number of students saved.
        """
        students = self.get_all_students()
        self.storage.save(students)
        return len(students)

    def load_from_file(self) -> int:
        """
        Load student records from disk into memory.

        Returns:
            The number of students loaded.
        """
        loaded = self.storage.load()
        self._students = {s.student_id: s for s in loaded}
        return len(loaded)

    def count(self) -> int:
        """Return the count of students currently in memory."""
        return len(self._students)
