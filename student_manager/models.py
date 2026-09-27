"""Student domain model and serialization with comprehensive extensible fields."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
from student_manager.validator import (
    validate_email,
    validate_student_id,
    validate_name,
    validate_age,
    validate_gpa,
    validate_phone,
    validate_attendance,
    validate_status,
    calculate_grade_letter,
)


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
        """Calculate letter grade from GPA."""
        return calculate_grade_letter(self.gpa)

    @property
    def is_honor_roll(self) -> bool:
        """Check if student qualifies for Dean's Honor Roll (GPA >= 3.8)."""
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
        """Factory method that validates all inputs before instantiating.

        Args:
            student_id: Unique student identification string.
            name: Full legal student name.
            email: Primary email address (validated with Regex).
            age: Student age in years.
            course: Department or enrolled program of study.
            gpa: Cumulative GPA on a 4.0 scale.
            created_at: Optional ISO 8601 creation timestamp.
            phone: Optional contact phone number (Regex validated).
            gender: Student gender / identity.
            semester: Academic term (e.g. 'Semester 1', 'Year 3').
            status: Enrollment status ('Active', 'Graduated', 'On Leave', 'Probation').
            attendance: Overall attendance percentage (0.0 to 100.0).
            emergency_contact: Emergency contact name and phone.
            city: Residential city or location.
            tags: List of custom tags or skill badges.
            extra_attributes: Dynamic dictionary for custom key-value pairs.

        Returns:
            A validated Student instance.
        """
        valid_id = validate_student_id(student_id)
        valid_name = validate_name(name)
        valid_email = validate_email(email)
        valid_age = validate_age(age)
        valid_gpa = validate_gpa(gpa)
        valid_phone = validate_phone(phone, optional=True)
        valid_attendance = validate_attendance(attendance if attendance is not None else 100.0)
        valid_status = validate_status(status if status else "Active")

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
            status=valid_status,
            attendance=valid_attendance,
            emergency_contact=str(emergency_contact or "").strip(),
            city=str(city or "").strip(),
            tags=clean_tags,
            extra_attributes=clean_extras,
        )

    def to_dict(self) -> dict:
        """Convert student record to serializable dictionary including computed helpers."""
        data = asdict(self)
        data["grade_letter"] = self.grade_letter
        data["is_honor_roll"] = self.is_honor_roll
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        """Reconstruct Student instance from a dictionary with validation."""
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
