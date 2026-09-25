"""Student domain model and serialization."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from student_manager.validator import (
    validate_email,
    validate_student_id,
    validate_name,
    validate_age,
    validate_gpa,
)


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
        course: str,
        gpa: float | str = 0.0,
        created_at: str | None = None,
    ) -> "Student":
        """Factory method that validates all inputs before instantiating.

        Args:
            student_id: Unique student identification string.
            name: Full legal student name.
            email: Primary email address (validated with Regex).
            age: Student age in years.
            course: Department or enrolled program of study.
            gpa: Cumulative GPA on a 4.0 scale.
            created_at: Optional ISO 8601 creation timestamp.

        Returns:
            A validated Student instance.

        Raises:
            InvalidStudentIdError: If student_id format is invalid.
            InvalidNameError: If name format is invalid.
            InvalidEmailError: If email format fails regex.
            InvalidAgeError: If age is invalid.
            InvalidGPAError: If GPA is invalid.
        """
        valid_id = validate_student_id(student_id)
        valid_name = validate_name(name)
        valid_email = validate_email(email)
        valid_age = validate_age(age)
        valid_gpa = validate_gpa(gpa)
        clean_course = course.strip() if isinstance(course, str) and course.strip() else "Undeclared"
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
        """Convert student record to serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        """Reconstruct Student instance from a dictionary with validation.

        Args:
            data: Dictionary containing student attributes.

        Returns:
            A validated Student instance.
        """
        return cls.create(
            student_id=data["student_id"],
            name=data["name"],
            email=data["email"],
            age=data["age"],
            course=data.get("course", "Undeclared"),
            gpa=data.get("gpa", 0.0),
            created_at=data.get("created_at"),
        )
