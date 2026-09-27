"""Core manager orchestrating student record lifecycle, queries, and analytics."""

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
    validate_phone,
    validate_attendance,
    validate_status,
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
        """Validate and add a new student record to the system.

        Args:
            student_id: Unique identifier for student.
            name: Full legal name.
            email: Primary contact email (regex validated).
            age: Student age.
            course: Academic department or major.
            gpa: Grade Point Average (0.0 to 4.0).
            phone: Optional contact phone (regex validated).
            gender: Gender / identity string.
            semester: Academic term / semester.
            status: Enrollment status ('Active', 'Graduated', etc.).
            attendance: Overall attendance percentage (0.0 to 100.0).
            emergency_contact: Emergency contact name and phone.
            city: City / Address.
            tags: List of skill badges / clubs.
            extra_attributes: Dynamic dictionary for custom attributes.

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
        """Retrieve a student by their unique ID."""
        clean_id = validate_student_id(student_id)
        if clean_id not in self._students:
            raise StudentNotFoundError(clean_id)
        return self._students[clean_id]

    def get_all_students(self, sort_by: str = "id", reverse: bool = False) -> list[Student]:
        """Return all student records sorted by specified field.

        Args:
            sort_by: One of 'id', 'name', 'gpa', 'course', 'age', or 'attendance'.
            reverse: Sort order direction.

        Returns:
            List of student objects.
        """
        students = list(self._students.values())
        if sort_by == "name":
            return sorted(students, key=lambda s: s.name.lower(), reverse=reverse)
        if sort_by == "gpa":
            return sorted(students, key=lambda s: s.gpa, reverse=True if not reverse else False)
        if sort_by == "course":
            return sorted(students, key=lambda s: s.course.lower(), reverse=reverse)
        if sort_by == "age":
            return sorted(students, key=lambda s: s.age, reverse=reverse)
        if sort_by == "attendance":
            return sorted(students, key=lambda s: s.attendance, reverse=reverse)
        # Default: sort by student ID
        return sorted(students, key=lambda s: s.student_id, reverse=reverse)

    def search_students(
        self,
        query: str = "",
        department: str = "",
        status: str = "",
        min_gpa: float = 0.0,
        max_gpa: float = 4.0,
    ) -> list[Student]:
        """Multi-criteria search across student attributes.

        Args:
            query: Keyword matched against ID, Name, Email, Phone, City, or Course.
            department: Filter by specific course/department.
            status: Filter by status ('Active', 'Graduated', etc.).
            min_gpa: Minimum GPA threshold.
            max_gpa: Maximum GPA threshold.

        Returns:
            Filtered list of student records.
        """
        q = query.strip().lower()
        dept_filter = department.strip().lower()
        status_filter = status.strip().lower()

        matches = []
        for s in self._students.values():
            # GPA Range
            if not (min_gpa <= s.gpa <= max_gpa):
                continue

            # Department filter
            if dept_filter and dept_filter not in s.course.lower():
                continue

            # Status filter
            if status_filter and status_filter != s.status.lower():
                continue

            # Text query
            if q:
                in_core = (
                    q in s.student_id.lower()
                    or q in s.name.lower()
                    or q in s.email.lower()
                    or q in s.course.lower()
                    or q in s.phone.lower()
                    or q in s.city.lower()
                )
                in_tags = any(q in t.lower() for t in s.tags)
                in_extras = any(q in str(k).lower() or q in str(v).lower() for k, v in s.extra_attributes.items())
                if not (in_core or in_tags or in_extras):
                    continue

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

        # Extra fields
        new_phone = validate_phone(updates["phone"], optional=True) if "phone" in updates else existing.phone
        new_attendance = validate_attendance(updates["attendance"]) if "attendance" in updates else existing.attendance
        new_status = validate_status(updates["status"]) if "status" in updates else existing.status
        new_gender = str(updates.get("gender", existing.gender)).strip()
        new_semester = str(updates.get("semester", existing.semester)).strip()
        new_emergency = str(updates.get("emergency_contact", existing.emergency_contact)).strip()
        new_city = str(updates.get("city", existing.city)).strip()

        new_tags = existing.tags
        if "tags" in updates and updates["tags"] is not None:
            new_tags = [str(t).strip() for t in updates["tags"] if str(t).strip()]

        new_extras = existing.extra_attributes.copy()
        if "extra_attributes" in updates and isinstance(updates["extra_attributes"], dict):
            new_extras = updates["extra_attributes"]

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
            phone=new_phone,
            gender=new_gender,
            semester=new_semester,
            status=new_status,
            attendance=new_attendance,
            emergency_contact=new_emergency,
            city=new_city,
            tags=new_tags,
            extra_attributes=new_extras,
        )
        self._students[existing.student_id] = updated_student

        if self.auto_save:
            self.save_to_file()

        return updated_student

    def delete_student(self, student_id: str) -> Student:
        """Delete student record by ID."""
        target = self.get_student(student_id)
        del self._students[target.student_id]
        self._email_index.pop(target.email.lower(), None)

        if self.auto_save:
            self.save_to_file()

        return target

    def get_statistics(self) -> dict[str, Any]:
        """Calculate comprehensive summary statistics and analytics."""
        students = list(self._students.values())
        total = len(students)
        if total == 0:
            return {
                "total_students": 0,
                "average_gpa": 0.0,
                "highest_gpa": 0.0,
                "lowest_gpa": 0.0,
                "average_attendance": 0.0,
                "honor_roll_count": 0,
                "grade_distribution": {"A+": 0, "A": 0, "B+": 0, "B": 0, "C": 0, "D": 0, "F": 0},
                "courses": {},
                "statuses": {"Active": 0, "Graduated": 0, "On Leave": 0, "Probation": 0},
            }

        gpas = [s.gpa for s in students]
        attendances = [s.attendance for s in students]

        grade_distribution = {"A+": 0, "A": 0, "B+": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        courses: dict[str, int] = {}
        statuses: dict[str, int] = {}
        honor_count = 0

        for s in students:
            # Grade
            grade_distribution[s.grade_letter] = grade_distribution.get(s.grade_letter, 0) + 1
            # Course
            courses[s.course] = courses.get(s.course, 0) + 1
            # Status
            statuses[s.status] = statuses.get(s.status, 0) + 1
            # Honor Roll
            if s.is_honor_roll:
                honor_count += 1

        return {
            "total_students": total,
            "average_gpa": round(sum(gpas) / total, 2),
            "highest_gpa": max(gpas),
            "lowest_gpa": min(gpas),
            "average_attendance": round(sum(attendances) / total, 1),
            "honor_roll_count": honor_count,
            "grade_distribution": grade_distribution,
            "courses": courses,
            "statuses": statuses,
        }

    def seed_sample_students(self) -> list[Student]:
        """Seed a rich set of realistic sample students with diverse attributes."""
        samples = [
            {
                "student_id": "STU-1001",
                "name": "Sarah Connor",
                "email": "sarah.connor@cyberdyne.edu",
                "age": 21,
                "course": "Computer Science",
                "gpa": 3.95,
                "phone": "+1-555-0143",
                "gender": "Female",
                "semester": "Semester 6",
                "status": "Active",
                "attendance": 98.5,
                "emergency_contact": "John Connor (+1-555-0199)",
                "city": "Los Angeles",
                "tags": ["Dean's List", "AI Lab", "President"],
                "extra_attributes": {"blood_group": "O+", "github": "sarah-c", "advisor": "Dr. Silberman"},
            },
            {
                "student_id": "STU-1002",
                "name": "Marcus Vance",
                "email": "m.vance@stanford.edu",
                "age": 22,
                "course": "Artificial Intelligence",
                "gpa": 3.88,
                "phone": "+1-555-0284",
                "gender": "Male",
                "semester": "Semester 7",
                "status": "Active",
                "attendance": 96.0,
                "emergency_contact": "Elena Vance (+1-555-0211)",
                "city": "Palo Alto",
                "tags": ["Neural Networks", "Robotics Club"],
                "extra_attributes": {"research_paper": "LLM Optimization", "scholarship": "Tech Fellowship"},
            },
            {
                "student_id": "STU-1003",
                "name": "Amina Al-Mansoor",
                "email": "amina.mansoor@oxford.ac.uk",
                "age": 20,
                "course": "Data Science",
                "gpa": 3.75,
                "phone": "+44-20-7946-0912",
                "gender": "Female",
                "semester": "Semester 4",
                "status": "Active",
                "attendance": 94.2,
                "emergency_contact": "Tariq Al-Mansoor (+44-20-7946-0913)",
                "city": "Oxford",
                "tags": ["Python", "Big Data", "Hackathon Winner"],
                "extra_attributes": {"kaggle_rank": "Master", "blood_group": "A+"},
            },
            {
                "student_id": "STU-1004",
                "name": "Ethan Wright",
                "email": "ethan.wright@mit.edu",
                "age": 23,
                "course": "Mechanical Engineering",
                "gpa": 3.42,
                "phone": "+1-555-0931",
                "gender": "Male",
                "semester": "Semester 8",
                "status": "Active",
                "attendance": 91.0,
                "emergency_contact": "Robert Wright (+1-555-0900)",
                "city": "Cambridge",
                "tags": ["CAD Design", "Formula Student"],
                "extra_attributes": {"capstone_project": "Aerodynamic Wing Design"},
            },
            {
                "student_id": "STU-1005",
                "name": "Maya Lin",
                "email": "maya.lin@berkeley.edu",
                "age": 19,
                "course": "Biotechnology",
                "gpa": 3.91,
                "phone": "+1-555-0812",
                "gender": "Female",
                "semester": "Semester 2",
                "status": "Active",
                "attendance": 99.0,
                "emergency_contact": "David Lin (+1-555-0800)",
                "city": "Berkeley",
                "tags": ["Dean's List", "Genomics", "Scholarship"],
                "extra_attributes": {"lab": "Crispr Gene Editing Group"},
            },
            {
                "student_id": "STU-1006",
                "name": "Liam O'Connor",
                "email": "liam.oconnor@tcd.ie",
                "age": 24,
                "course": "Business Analytics",
                "gpa": 3.15,
                "phone": "+353-1-496-0123",
                "gender": "Male",
                "semester": "Semester 8",
                "status": "Graduated",
                "attendance": 88.5,
                "emergency_contact": "Maeve O'Connor (+353-1-496-0124)",
                "city": "Dublin",
                "tags": ["Alumni", "Fintech", "Consulting"],
                "extra_attributes": {"employed_at": "Stripe Ireland"},
            },
            {
                "student_id": "STU-1007",
                "name": "Chloe Dupont",
                "email": "chloe.dupont@sorbonne.fr",
                "age": 21,
                "course": "Computer Science",
                "gpa": 2.85,
                "phone": "+33-1-4268-5500",
                "gender": "Female",
                "semester": "Semester 5",
                "status": "On Leave",
                "attendance": 78.0,
                "emergency_contact": "Pierre Dupont (+33-1-4268-5501)",
                "city": "Paris",
                "tags": ["Exchange Student", "Graphic Design"],
                "extra_attributes": {"leave_reason": "Overseas Internship"},
            },
            {
                "student_id": "STU-1008",
                "name": "Devin Kumar",
                "email": "devin.kumar@iitb.ac.in",
                "age": 22,
                "course": "Cybersecurity",
                "gpa": 3.82,
                "phone": "+91-98765-43210",
                "gender": "Male",
                "semester": "Semester 6",
                "status": "Active",
                "attendance": 97.4,
                "emergency_contact": "Sanjay Kumar (+91-98765-43211)",
                "city": "Mumbai",
                "tags": ["Dean's List", "Ethical Hacking", "CTF Champ"],
                "extra_attributes": {"certifications": "OSCP, CISSP", "blood_group": "B+"},
            },
        ]

        added = []
        for s in samples:
            if s["student_id"] not in self._students and s["email"].lower() not in self._email_index:
                created = self.add_student(**s)
                added.append(created)
        return added
