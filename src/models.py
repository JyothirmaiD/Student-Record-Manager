"""Data models for Student Record Manager."""

from dataclasses import dataclass, asdict
from typing import Any, Dict
from src.validator import (
    validate_student_id,
    validate_name,
    validate_email,
    validate_course,
    validate_gpa,
)


@dataclass
class Student:
    """Represents an enrolled student record."""

    student_id: str
    name: str
    email: str
    course: str
    gpa: float

    @classmethod
    def create(
        cls,
        student_id: str,
        name: str,
        email: str,
        course: str,
        gpa: float | int | str,
    ) -> "Student":
        """
        Factory method to construct a validated Student instance.

        Raises:
            InvalidEmailError: When email is malformed.
            InvalidInputError: When any other input fails validation constraints.
        """
        valid_id = validate_student_id(student_id)
        valid_name = validate_name(name)
        valid_email = validate_email(email)
        valid_course = validate_course(course)
        valid_gpa = validate_gpa(gpa)

        return cls(
            student_id=valid_id,
            name=valid_name,
            email=valid_email,
            course=valid_course,
            gpa=valid_gpa,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Student instance to a JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Student":
        """Reconstruct a Student instance from a dictionary representation."""
        return cls.create(
            student_id=data["student_id"],
            name=data["name"],
            email=data["email"],
            course=data["course"],
            gpa=data["gpa"],
        )

    def __str__(self) -> str:
        return f"[{self.student_id}] {self.name} | {self.email} | {self.course} | GPA: {self.gpa:.2f}"
