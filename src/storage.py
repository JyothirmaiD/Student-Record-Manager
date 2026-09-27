"""File persistence storage engine for Student Record Manager."""

import json
import os
from typing import List
from src.models import Student
from src.exceptions import StorageError


class JSONStorage:
    """Handles saving and loading student records to and from a JSON file."""

    def __init__(self, filepath: str = "data/students.json"):
        self.filepath = filepath

    def save(self, students: List[Student]) -> None:
        """
        Persist a list of student records to the JSON file.

        Args:
            students: List of Student instances to save.

        Raises:
            StorageError: If the file cannot be written.
        """
        try:
            # Ensure target directory exists
            directory = os.path.dirname(self.filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            data = [student.to_dict() for student in students]

            # Write to a temporary file first for atomic safety
            temp_filepath = f"{self.filepath}.tmp"
            with open(temp_filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # Atomic replace
            os.replace(temp_filepath, self.filepath)
        except Exception as e:
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except OSError:
                    pass
            raise StorageError(self.filepath, "save", str(e)) from e

    def load(self) -> List[Student]:
        """
        Read and deserialize student records from the JSON file.

        Returns:
            List of Student instances. Returns an empty list if file does not exist.

        Raises:
            StorageError: If the file exists but cannot be read or contains invalid JSON.
        """
        if not os.path.exists(self.filepath):
            return []

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                raw_data = json.loads(content)

            if not isinstance(raw_data, list):
                raise ValueError("Root element of students data must be a list")

            students: List[Student] = []
            for item in raw_data:
                students.append(Student.from_dict(item))
            return students
        except Exception as e:
            raise StorageError(self.filepath, "load", str(e)) from e
