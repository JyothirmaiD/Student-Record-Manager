"""Storage handlers for persisting and reading student data."""

from abc import ABC, abstractmethod
import csv
import json
import os
from pathlib import Path
from student_manager.exceptions import StorageError
from student_manager.models import Student


class BaseStorageHandler(ABC):
    """Abstract interface for student persistence handlers."""

    @abstractmethod
    def save(self, students: list[Student]) -> None:
        """Save a list of student records to file."""
        pass

    @abstractmethod
    def load(self) -> list[Student]:
        """Load and return student records from file."""
        pass


class JsonStorageHandler(BaseStorageHandler):
    """Handles JSON file persistence with atomic write safety."""

    def __init__(self, file_path: str | Path = "data/students.json") -> None:
        self.file_path = Path(file_path)

    def _ensure_directory(self) -> None:
        """Ensure parent directory exists."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise StorageError("create directory", str(self.file_path.parent), e) from e

    def save(self, students: list[Student]) -> None:
        """Save student records to JSON file with atomic write.

        Args:
            students: List of Student domain objects.

        Raises:
            StorageError: If disk write or serialization fails.
        """
        self._ensure_directory()
        tmp_path = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
        try:
            payload = [student.to_dict() for student in students]
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            # Atomic replacement on Windows and POSIX
            os.replace(tmp_path, self.file_path)
        except (OSError, TypeError, ValueError) as e:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise StorageError("save", str(self.file_path), e) from e

    def load(self) -> list[Student]:
        """Load student records from the JSON file.

        Returns:
            List of Student domain instances.

        Raises:
            StorageError: If reading or JSON parsing fails.
        """
        if not self.file_path.exists():
            return []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                records = json.loads(content)

            if not isinstance(records, list):
                raise ValueError("Root JSON element must be an array of student records")

            students: list[Student] = []
            for item in records:
                students.append(Student.from_dict(item))
            return students
        except Exception as e:
            raise StorageError("load", str(self.file_path), e) from e


class CsvStorageHandler(BaseStorageHandler):
    """Optional CSV persistence and export handler."""

    def __init__(self, file_path: str | Path = "data/students.csv") -> None:
        self.file_path = Path(file_path)

    def save(self, students: list[Student]) -> None:
        """Export student records to CSV format with all extra fields."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            fieldnames = [
                "student_id",
                "name",
                "email",
                "age",
                "course",
                "gpa",
                "grade_letter",
                "status",
                "attendance",
                "phone",
                "gender",
                "semester",
                "emergency_contact",
                "city",
                "tags",
                "created_at",
            ]
            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                for s in students:
                    row = s.to_dict()
                    row["tags"] = "; ".join(s.tags) if s.tags else ""
                    writer.writerow(row)
        except OSError as e:
            raise StorageError("save (CSV)", str(self.file_path), e) from e

    def load(self) -> list[Student]:
        """Load student records from CSV."""
        if not self.file_path.exists():
            return []

        try:
            students: list[Student] = []
            with open(self.file_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data = dict(row)
                    if "tags" in data and isinstance(data["tags"], str):
                        data["tags"] = [t.strip() for t in data["tags"].split(";") if t.strip()]
                    students.append(Student.from_dict(data))
            return students
        except Exception as e:
            raise StorageError("load (CSV)", str(self.file_path), e) from e
