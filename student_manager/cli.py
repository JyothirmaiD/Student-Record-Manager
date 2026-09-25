"""Command Line Interface for Student Record Manager.

Offers an interactive terminal menu with exception-safe input loops,
formatted table views, and non-interactive command-line argument support.
"""

import argparse
import sys
from student_manager.exceptions import (
    StudentRecordError,
    ValidationError,
    InvalidEmailError,
    InvalidStudentIdError,
    InvalidNameError,
    InvalidAgeError,
    InvalidGPAError,
    StudentNotFoundError,
    DuplicateStudentError,
    StorageError,
)
from student_manager.manager import StudentRecordManager
from student_manager.storage import JsonStorageHandler, CsvStorageHandler
from student_manager.models import Student

# Terminal ANSI styling helpers (safe fallback on plain terminals)
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def style(text: str, color: str) -> str:
    """Format text with ANSI codes if stdout supports it."""
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        return f"{color}{text}{RESET}"
    return text


def print_banner() -> None:
    """Print the application header."""
    banner = f"""
{style("=" * 68, CYAN)}
{style("           STUDENT RECORD MANAGER - ACADEMIC SYSTEM", BOLD + CYAN)}
{style("   Regex Email Validation * Exception Handling * Persistent File I/O", YELLOW)}
{style("=" * 68, CYAN)}"""
    print(banner)


def render_student_table(students: list[Student]) -> None:
    """Render a clean ASCII table of student records."""
    if not students:
        print(style("\nNo student records found.", YELLOW))
        return

    col_id = 12
    col_name = 20
    col_email = 28
    col_age = 5
    col_course = 18
    col_gpa = 6

    sep = (
        "+"
        + "-" * (col_id + 2)
        + "+"
        + "-" * (col_name + 2)
        + "+"
        + "-" * (col_email + 2)
        + "+"
        + "-" * (col_age + 2)
        + "+"
        + "-" * (col_course + 2)
        + "+"
        + "-" * (col_gpa + 2)
        + "+"
    )

    header = (
        f"| {'ID'.ljust(col_id)} "
        f"| {'NAME'.ljust(col_name)} "
        f"| {'EMAIL'.ljust(col_email)} "
        f"| {'AGE'.rjust(col_age)} "
        f"| {'COURSE'.ljust(col_course)} "
        f"| {'GPA'.rjust(col_gpa)} |"
    )

    print("\n" + sep)
    print(style(header, BOLD))
    print(sep)

    for s in students:
        row = (
            f"| {s.student_id[:col_id].ljust(col_id)} "
            f"| {s.name[:col_name].ljust(col_name)} "
            f"| {s.email[:col_email].ljust(col_email)} "
            f"| {str(s.age).rjust(col_age)} "
            f"| {s.course[:col_course].ljust(col_course)} "
            f"| {f'{s.gpa:.2f}'.rjust(col_gpa)} |"
        )
        print(row)
    print(sep)
    print(f"Total Records: {style(str(len(students)), BOLD + GREEN)}\n")


def prompt_with_validation(prompt_text: str, validator_fn, allow_cancel: bool = True):
    """Prompt user repeatedly until valid input is given or canceled."""
    while True:
        try:
            user_input = input(prompt_text).strip()
            if allow_cancel and user_input.lower() == "cancel":
                return None
            return validator_fn(user_input)
        except ValidationError as e:
            print(f"  {style('Validation Error:', RED + BOLD)} {e.message}")
            if allow_cancel:
                print(style("  (Type 'cancel' to abort and return to menu)", YELLOW))


class CommandLineApp:
    """Coordinates interactive user workflows."""

    def __init__(self, manager: StudentRecordManager) -> None:
        self.manager = manager

    def add_student_flow(self) -> None:
        """Interactive workflow to enroll a new student with exception handling."""
        print(f"\n{style('--- Add New Student ---', BOLD + CYAN)}")
        print(style("Note: Type 'cancel' at any prompt to return to the menu.\n", YELLOW))

        from student_manager.validator import (
            validate_student_id,
            validate_name,
            validate_email,
            validate_age,
            validate_gpa,
        )

        try:
            student_id = prompt_with_validation("Enter Student ID (e.g., STU-101): ", validate_student_id)
            if student_id is None:
                print("Operation canceled.")
                return

            # Early check for duplicate ID
            if student_id in self.manager._students:
                raise DuplicateStudentError("Student ID", student_id)

            name = prompt_with_validation("Enter Student Full Name: ", validate_name)
            if name is None:
                print("Operation canceled.")
                return

            email = prompt_with_validation("Enter Student Email (Regex validated): ", validate_email)
            if email is None:
                print("Operation canceled.")
                return

            # Early check for duplicate Email
            if email in self.manager._email_index:
                raise DuplicateStudentError("Email address", email)

            age = prompt_with_validation("Enter Student Age (10 - 120): ", validate_age)
            if age is None:
                print("Operation canceled.")
                return

            course_input = input("Enter Course/Department [General]: ").strip()
            course = course_input if course_input else "General"

            gpa = prompt_with_validation("Enter Cumulative GPA (0.00 - 4.00) [0.0]: ", lambda val: validate_gpa(val or 0.0))
            if gpa is None:
                print("Operation canceled.")
                return

            new_student = self.manager.add_student(
                student_id=student_id,
                name=name,
                email=email,
                age=age,
                course=course,
                gpa=gpa,
            )

            print(f"\n{style('Success:', GREEN + BOLD)} Student record added and saved!")
            print(f"  ID:     {new_student.student_id}")
            print(f"  Name:   {new_student.name}")
            print(f"  Email:  {new_student.email}")
            print(f"  Age:    {new_student.age}")
            print(f"  Course: {new_student.course}")
            print(f"  GPA:    {new_student.gpa:.2f}")

        except DuplicateStudentError as e:
            print(f"\n{style('Duplicate Error:', RED + BOLD)} {e.message}")
        except StorageError as e:
            print(f"\n{style('Storage Error:', RED + BOLD)} {e.message}")
        except Exception as e:
            print(f"\n{style('Unexpected Error:', RED + BOLD)} {e}")

    def view_all_students_flow(self) -> None:
        """Display all student records."""
        students = self.manager.get_all_students()
        render_student_table(students)

    def search_students_flow(self) -> None:
        """Search student records by search query."""
        query = input("\nEnter search query (ID, name, email, or course): ").strip()
        matches = self.manager.search_students(query)
        print(f"\nFound {len(matches)} matching records:")
        render_student_table(matches)

    def find_by_id_flow(self) -> None:
        """Find a single student by ID."""
        student_id = input("\nEnter Student ID to find: ").strip()
        try:
            student = self.manager.get_student(student_id)
            render_student_table([student])
        except StudentNotFoundError as e:
            print(f"{style('Error:', RED + BOLD)} {e.message}")
        except ValidationError as e:
            print(f"{style('Validation Error:', RED + BOLD)} {e.message}")

    def update_student_flow(self) -> None:
        """Update existing student attributes with validation."""
        student_id = input("\nEnter Student ID to update: ").strip()
        try:
            existing = self.manager.get_student(student_id)
            print(f"\nUpdating Record for {style(existing.name, BOLD)} (Leave blank to keep existing value):")

            name_in = input(f"New Name [{existing.name}]: ").strip()
            email_in = input(f"New Email [{existing.email}]: ").strip()
            age_in = input(f"New Age [{existing.age}]: ").strip()
            course_in = input(f"New Course [{existing.course}]: ").strip()
            gpa_in = input(f"New GPA [{existing.gpa}]: ").strip()

            updates = {}
            if name_in:
                updates["name"] = name_in
            if email_in:
                updates["email"] = email_in
            if age_in:
                updates["age"] = age_in
            if course_in:
                updates["course"] = course_in
            if gpa_in:
                updates["gpa"] = gpa_in

            if not updates:
                print("No changes specified.")
                return

            updated = self.manager.update_student(student_id, **updates)
            print(f"\n{style('Success:', GREEN + BOLD)} Student record updated successfully!")
            render_student_table([updated])

        except StudentRecordError as e:
            print(f"{style('Update Failed:', RED + BOLD)} {e.message}")

    def delete_student_flow(self) -> None:
        """Delete student record with confirmation."""
        student_id = input("\nEnter Student ID to delete: ").strip()
        try:
            existing = self.manager.get_student(student_id)
            confirm = input(
                f"Are you sure you want to delete {style(existing.name, BOLD)} ({existing.student_id})? (y/N): "
            ).strip().lower()
            if confirm == "y":
                deleted = self.manager.delete_student(student_id)
                print(f"{style('Success:', GREEN + BOLD)} Deleted student record '{deleted.name}' ({deleted.student_id}).")
            else:
                print("Deletion aborted.")
        except StudentRecordError as e:
            print(f"{style('Error:', RED + BOLD)} {e.message}")

    def view_statistics_flow(self) -> None:
        """Display analytical breakdown of student records."""
        stats = self.manager.get_statistics()
        print(f"\n{style('--- Student Academic Statistics ---', BOLD + CYAN)}")
        print(f"Total Students:  {style(str(stats['total_students']), BOLD)}")
        print(f"Average GPA:     {stats['average_gpa']:.2f}")
        print(f"Highest GPA:     {stats['highest_gpa']:.2f}")
        print(f"Lowest GPA:      {stats['lowest_gpa']:.2f}")
        print("\nCourse Enrollment Breakdown:")
        if stats["courses"]:
            for course, count in sorted(stats["courses"].items()):
                print(f"  - {course.ljust(22)}: {count} student(s)")
        else:
            print("  (No courses registered)")
        print()

    def export_csv_flow(self) -> None:
        """Export current records to a CSV file."""
        path_in = input("Enter export CSV file path [data/students_export.csv]: ").strip()
        target_path = path_in if path_in else "data/students_export.csv"
        try:
            csv_handler = CsvStorageHandler(target_path)
            students = self.manager.get_all_students()
            csv_handler.save(students)
            print(f"{style('Success:', GREEN + BOLD)} Exported {len(students)} records to '{target_path}'.")
        except StorageError as e:
            print(f"{style('Export Failed:', RED + BOLD)} {e.message}")

    def interactive_menu(self) -> None:
        """Run main interactive CLI event loop."""
        while True:
            print_banner()
            print(" 1. Add Student (with Regex Email & Input Validation)")
            print(" 2. View All Students (Table View)")
            print(" 3. Search Student Records")
            print(" 4. Find Student by ID")
            print(" 5. Update Student Record")
            print(" 6. Delete Student Record")
            print(" 7. View Academic Statistics")
            print(" 8. Export Records to CSV")
            print(" 9. Reload Data from File")
            print(" 0. Exit")
            print(style("-" * 68, CYAN))

            try:
                choice = input(style("Enter your choice (0-9): ", BOLD)).strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n{style('Exiting Student Record Manager. Goodbye!', YELLOW)}")
                break

            if choice == "1":
                self.add_student_flow()
            elif choice == "2":
                self.view_all_students_flow()
            elif choice == "3":
                self.search_students_flow()
            elif choice == "4":
                self.find_by_id_flow()
            elif choice == "5":
                self.update_student_flow()
            elif choice == "6":
                self.delete_student_flow()
            elif choice == "7":
                self.view_statistics_flow()
            elif choice == "8":
                self.export_csv_flow()
            elif choice == "9":
                try:
                    self.manager.load_from_file()
                    print(style("\nRecords successfully reloaded from file.", GREEN))
                except StorageError as e:
                    print(style(f"\nFailed to reload: {e.message}", RED))
            elif choice == "0":
                print(f"\n{style('Exiting Student Record Manager. Have a great day!', GREEN)}")
                break
            else:
                print(style("\nInvalid choice. Please select an option between 0 and 9.", RED))

            input(style("\nPress Enter to continue...", YELLOW))


def main() -> None:
    """CLI entrypoint with argparse support."""
    parser = argparse.ArgumentParser(
        description="Student Record Manager with Regex Validation & Exception Handling"
    )
    parser.add_argument("--data-file", default="data/students.json", help="Path to JSON data storage file")
    parser.add_argument("--list", action="store_true", help="List all students and exit")
    parser.add_argument("--search", type=str, help="Search students by keyword and exit")
    parser.add_argument("--stats", action="store_true", help="Display summary statistics and exit")
    parser.add_argument(
        "--add",
        nargs=6,
        metavar=("ID", "NAME", "EMAIL", "AGE", "COURSE", "GPA"),
        help="Add a student directly: ID NAME EMAIL AGE COURSE GPA",
    )
    parser.add_argument("--export-csv", type=str, help="Export all records to specified CSV path and exit")

    args = parser.parse_args()

    storage = JsonStorageHandler(args.data_file)
    manager = StudentRecordManager(storage=storage)
    app = CommandLineApp(manager)

    # Process CLI flags if passed
    if args.list:
        app.view_all_students_flow()
        return

    if args.search is not None:
        matches = manager.search_students(args.search)
        render_student_table(matches)
        return

    if args.stats:
        app.view_statistics_flow()
        return

    if args.export_csv:
        csv_handler = CsvStorageHandler(args.export_csv)
        csv_handler.save(manager.get_all_students())
        print(f"Exported records to {args.export_csv}")
        return

    if args.add:
        sid, name, email, age, course, gpa = args.add
        try:
            new_student = manager.add_student(
                student_id=sid,
                name=name,
                email=email,
                age=age,
                course=course,
                gpa=gpa,
            )
            print(f"{style('Success:', GREEN + BOLD)} Added student '{new_student.name}' ({new_student.student_id}).")
        except StudentRecordError as e:
            print(f"{style('Error:', RED + BOLD)} {e.message}")
            sys.exit(1)
        return

    # Default: launch interactive menu
    app.interactive_menu()


if __name__ == "__main__":
    main()
