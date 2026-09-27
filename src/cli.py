"""Interactive Command-Line Interface for Student Record Manager."""

import sys
from src.manager import StudentRecordManager
from src.models import Student
from src.exceptions import (
    StudentRecordException,
    InvalidEmailError,
    InvalidInputError,
    DuplicateStudentError,
    StudentNotFoundError,
    StorageError,
)


class StudentRecordCLI:
    """Console-based user interface for managing student records."""

    def __init__(self, manager: StudentRecordManager):
        self.manager = manager
        self.has_unsaved_changes = False

    def print_banner(self) -> None:
        banner = """
============================================================
              STUDENT RECORD MANAGER (v1.0)
============================================================
 Features: Add Student | Regex Email Validation | File I/O
           Custom Exception Handling | GitHub Ready
============================================================
"""
        print(banner)

    def print_menu(self) -> None:
        status = " [Unsaved changes]" if self.has_unsaved_changes else ""
        print(f"\n--- MAIN MENU{status} ---")
        print("1. Add New Student")
        print("2. View All Students")
        print("3. Search Students")
        print("4. Delete Student")
        print("5. Save Records to File")
        print("6. Reload Records from File")
        print("7. Exit")
        print("-" * 30)

    def render_student_table(self, students: list[Student]) -> None:
        """Display a list of students in an aligned ASCII table."""
        if not students:
            print("\n[i] No student records found.")
            return

        id_w = max(len("ID"), max((len(s.student_id) for s in students), default=2)) + 2
        name_w = max(len("Name"), max((len(s.name) for s in students), default=4)) + 2
        email_w = max(len("Email"), max((len(s.email) for s in students), default=5)) + 2
        course_w = max(len("Course"), max((len(s.course) for s in students), default=6)) + 2
        gpa_w = 8

        total_w = id_w + name_w + email_w + course_w + gpa_w + 6

        print("\n" + "=" * total_w)
        header = (
            f"| {'ID'.ljust(id_w-2)} "
            f"| {'Name'.ljust(name_w-2)} "
            f"| {'Email'.ljust(email_w-2)} "
            f"| {'Course'.ljust(course_w-2)} "
            f"| {'GPA'.rjust(gpa_w-2)} |"
        )
        print(header)
        print("=" * total_w)

        for s in students:
            row = (
                f"| {s.student_id.ljust(id_w-2)} "
                f"| {s.name.ljust(name_w-2)} "
                f"| {s.email.ljust(email_w-2)} "
                f"| {s.course.ljust(course_w-2)} "
                f"| {f'{s.gpa:.2f}'.rjust(gpa_w-2)} |"
            )
            print(row)

        print("-" * total_w)
        print(f" Total records: {len(students)}")
        print("=" * total_w)

    def handle_add_student(self) -> None:
        """Prompt user for student details with robust exception handling."""
        print("\n[+] ADD NEW STUDENT")
        print("Enter student details below (type 'cancel' at any prompt to abort):")

        # Prompt Student ID
        while True:
            student_id = input("  Student ID (e.g., STU101): ").strip()
            if student_id.lower() == "cancel":
                print("[-] Operation cancelled.")
                return
            try:
                # Check for existing before proceeding
                if student_id.upper() in self.manager._students:
                    raise DuplicateStudentError(student_id.upper())
                break
            except DuplicateStudentError as e:
                print(f"  [ERROR] {e}")

        # Prompt Name
        name = input("  Full Name: ").strip()
        if name.lower() == "cancel":
            print("[-] Operation cancelled.")
            return

        # Prompt Email with explicit regex error handling loop
        email = ""
        while True:
            email_input = input("  Email Address (e.g., alex@university.edu): ").strip()
            if email_input.lower() == "cancel":
                print("[-] Operation cancelled.")
                return
            try:
                # Validate immediately with regex
                from src.validator import validate_email
                email = validate_email(email_input)
                break
            except InvalidEmailError as e:
                print(f"  [ERROR] {e.message}")
                print("  Please enter a valid email address.")

        # Prompt Course
        course = input("  Course / Major (e.g., Computer Science): ").strip()
        if course.lower() == "cancel":
            print("[-] Operation cancelled.")
            return

        # Prompt GPA
        gpa = ""
        while True:
            gpa_input = input("  GPA (0.00 - 4.00): ").strip()
            if gpa_input.lower() == "cancel":
                print("[-] Operation cancelled.")
                return
            try:
                from src.validator import validate_gpa
                gpa = validate_gpa(gpa_input)
                break
            except InvalidInputError as e:
                print(f"  [ERROR] {e.message}")

        # Assemble and register student
        try:
            student = Student.create(
                student_id=student_id,
                name=name,
                email=email,
                course=course,
                gpa=gpa,
            )
            self.manager.add_student(student)
            self.has_unsaved_changes = True
            print(f"\n[OK] Successfully added student: {student}")
        except StudentRecordException as e:
            print(f"\n[ERROR] Failed to add student: {e}")

    def handle_view_all(self) -> None:
        """Display all students."""
        students = self.manager.get_all_students()
        self.render_student_table(students)

    def handle_search(self) -> None:
        """Search student records by query."""
        print("\n[?] SEARCH STUDENTS")
        query = input("Enter search keyword (ID, Name, Email, or Course): ").strip()
        matches = self.manager.search_students(query)
        print(f"\nFound {len(matches)} match(es) for '{query}':")
        self.render_student_table(matches)

    def handle_delete(self) -> None:
        """Delete student record with confirmation."""
        print("\n[-] DELETE STUDENT RECORD")
        student_id = input("Enter Student ID to delete: ").strip()
        try:
            student = self.manager.get_student(student_id)
            confirm = input(f"Are you sure you want to delete {student.name} ({student.student_id})? [y/N]: ").strip().lower()
            if confirm in ("y", "yes"):
                self.manager.delete_student(student_id)
                self.has_unsaved_changes = True
                print(f"[OK] Student {student_id} successfully deleted.")
            else:
                print("[-] Deletion aborted.")
        except StudentNotFoundError as e:
            print(f"[ERROR] {e}")

    def handle_save(self) -> None:
        """Save records to file."""
        try:
            count = self.manager.save_to_file()
            self.has_unsaved_changes = False
            print(f"[OK] Successfully saved {count} student record(s) to '{self.manager.storage.filepath}'.")
        except StorageError as e:
            print(f"[ERROR] {e}")

    def handle_reload(self) -> None:
        """Reload records from storage file."""
        if self.has_unsaved_changes:
            confirm = input("You have unsaved changes. Overwrite with file contents? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("[-] Reload cancelled.")
                return

        try:
            count = self.manager.load_from_file()
            self.has_unsaved_changes = False
            print(f"[OK] Successfully loaded {count} student record(s) from '{self.manager.storage.filepath}'.")
        except StorageError as e:
            print(f"[ERROR] {e}")

    def run(self) -> None:
        """Main application loop."""
        self.print_banner()

        # Attempt to auto-load existing file
        try:
            count = self.manager.load_from_file()
            if count > 0:
                print(f"[i] Automatically loaded {count} record(s) from file.")
        except Exception:
            pass

        while True:
            self.print_menu()
            choice = input("Select an option (1-7): ").strip()

            try:
                if choice == "1":
                    self.handle_add_student()
                elif choice == "2":
                    self.handle_view_all()
                elif choice == "3":
                    self.handle_search()
                elif choice == "4":
                    self.handle_delete()
                elif choice == "5":
                    self.handle_save()
                elif choice == "6":
                    self.handle_reload()
                elif choice == "7":
                    if self.has_unsaved_changes:
                        save_choice = input("You have unsaved changes. Save before exiting? [Y/n]: ").strip().lower()
                        if save_choice not in ("n", "no"):
                            self.handle_save()
                    print("\nThank you for using Student Record Manager. Goodbye!\n")
                    sys.exit(0)
                else:
                    raise InvalidInputError("Menu Option", choice, "Please choose a number between 1 and 7")
            except InvalidInputError as e:
                print(f"[ERROR] {e.message}")
            except KeyboardInterrupt:
                print("\n\nOperation interrupted by user. Exiting...")
                sys.exit(0)
            except Exception as e:
                print(f"[ERROR] An unexpected error occurred: {e}")
