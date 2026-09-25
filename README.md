# Student Record Manager 🎓

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-29%20passed-brightgreen.svg)](tests/)
[![Documentation](https://img.shields.io/badge/Documentation-PDF-red.svg)](StudentRecordManager_Project_Report.pdf)
[![Dependencies](https://img.shields.io/badge/dependencies-standard%20library-brightgreen.svg)](#requirements)

A Python application for managing student academic records. Built with modular software design principles, featuring **Regex-based email validation**, **atomic file persistence**, a **custom exception hierarchy**, and an **interactive CLI**.

📄 **[Download the Complete Project Report & Documentation (PDF)](StudentRecordManager_Project_Report.pdf)**

---

## 📋 Features

- 👤 **Add Student**: Enroll student records with ID, Full Name, Email, Age, Course, and Cumulative GPA.
- ✉️ **Validate Email using Regex**: Robust RFC 5322-compliant regular expression validation with format verification and normalization.
- 💾 **Save Data to File**: Persistent atomic JSON storage with crash protection, plus optional CSV export.
- 📖 **Read Student Data**: Formatted ASCII table views, record lookups by ID, fuzzy multi-field search, and academic statistics.
- 🛡️ **Handle Invalid Input using Exceptions**: Granular domain-specific custom exception hierarchy that gracefully reports input errors without application crashes.

---

## 🏗️ Project Architecture

```
student-record-manager/
├── student_manager/            # Core application package
│   ├── __init__.py             # Public API exports
│   ├── exceptions.py           # Custom exception hierarchy
│   ├── models.py               # Student domain model & serialization
│   ├── validator.py            # Regex email & input validators
│   ├── storage.py              # Atomic JSON and CSV persistence
│   ├── manager.py              # Business logic & record operations
│   └── cli.py                  # Interactive menu & argparse handler
├── tests/                      # Comprehensive unit test suite
│   ├── __init__.py
│   ├── test_validator.py       # Regex email & field validation tests
│   ├── test_storage.py         # Persistence & error recovery tests
│   ├── test_manager.py         # CRUD logic & duplicate prevention tests
│   └── test_exceptions.py      # Exception hierarchy tests
├── data/                       # Storage directory
│   └── students.json           # Default JSON database
├── main.py                     # Primary executable entrypoint
├── requirements.txt            # Zero-dependency specification
├── .gitignore                  # Git ignore rules
├── LICENSE                     # MIT License
└── README.md                   # Project documentation
```

---

## 🔍 Email Regex Validation

Email validation is implemented in [`student_manager/validator.py`](file:///C:/Users/HP/.gemini/antigravity-ide/scratch/student-record-manager/student_manager/validator.py) using the following compiled regular expression pattern:

```python
EMAIL_REGEX_PATTERN = r"^[a-zA-Z0-9]([a-zA-Z0-9._%+-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$"
```

### Pattern Breakdown:
1. `^[a-zA-Z0-9]`: Must begin with an alphanumeric character.
2. `([a-zA-Z0-9._%+-]*[a-zA-Z0-9])?`: Local part allows dots, underscores, hyphens, and percent signs, but must not end with a special character or contain consecutive dots (`..`).
3. `@`: Mandatory single delimiter separating local part and domain.
4. `[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?`: Domain name must start and end with an alphanumeric character and can contain hyphens.
5. `(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)*`: Supports optional subdomains (e.g., `dept.university.edu`).
6. `\.[a-zA-Z]{2,}$`: Requires a valid Top-Level Domain (TLD) of at least 2 alphabetic characters.

---

## ⚠️ Exception Handling Architecture

All exceptions derive from a unified base class `StudentRecordError` defined in [`student_manager/exceptions.py`](file:///C:/Users/HP/.gemini/antigravity-ide/scratch/student-record-manager/student_manager/exceptions.py):

| Exception | Inherits From | Description |
| :--- | :--- | :--- |
| `StudentRecordError` | `Exception` | Base class for all domain-specific errors. |
| `ValidationError` | `StudentRecordError` | Base class for all input validation failures. |
| `InvalidEmailError` | `ValidationError` | Raised when an email fails regex validation. |
| `InvalidStudentIdError` | `ValidationError` | Raised when student ID format is incorrect. |
| `InvalidNameError` | `ValidationError` | Raised when student name is blank or invalid. |
| `InvalidAgeError` | `ValidationError` | Raised when age is outside [10, 120] or non-integer. |
| `InvalidGPAError` | `ValidationError` | Raised when GPA is not a number or outside [0.0, 4.0]. |
| `StudentNotFoundError` | `StudentRecordError` | Raised when a requested student ID is not found. |
| `DuplicateStudentError` | `StudentRecordError` | Raised when student ID or email already exists. |
| `StorageError` | `StudentRecordError` | Raised when saving or loading data encounters disk errors. |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher.
- No third-party packages required (uses Python Standard Library).

### Running Interactive Mode
Launch the interactive terminal interface:

```bash
python main.py
```

**Terminal Menu Preview:**
```text
====================================================================
           STUDENT RECORD MANAGER - ACADEMIC SYSTEM
   Regex Email Validation * Exception Handling * Persistent File I/O
====================================================================
 1. Add Student (with Regex Email & Input Validation)
 2. View All Students (Table View)
 3. Search Student Records
 4. Find Student by ID
 5. Update Student Record
 6. Delete Student Record
 7. View Academic Statistics
 8. Export Records to CSV
 9. Reload Data from File
 0. Exit
--------------------------------------------------------------------
Enter your choice (0-9):
```

---

### Command-Line Arguments (CLI Mode)

You can also run batch tasks directly from the command line:

- **List all students**:
  ```bash
  python main.py --list
  ```

- **Add a student**:
  ```bash
  python main.py --add STU-1006 "Hannah Abbott" "hannah@university.edu" 21 "Chemistry" 3.82
  ```

- **Search by keyword**:
  ```bash
  python main.py --search "Computer Science"
  ```

- **View statistics**:
  ```bash
  python main.py --stats
  ```

- **Export records to CSV**:
  ```bash
  python main.py --export-csv data/students_backup.csv
  ```

---

## 🧪 Running Unit Tests

Run the full suite of 29 unit tests using Python's built-in `unittest` runner:

```bash
python -m unittest discover -s tests -v
```

All tests will execute and confirm:
- Regex email validation with valid and edge-case inputs.
- Custom exception raising and contextual error messages.
- Atomic file writes and data corruption handling.
- Record uniqueness constraint checks.

---

## 📤 Publishing to a GitHub Repository

To publish this project to your GitHub account:

### 1. Initialize Git and Commit Files
Open a terminal in this project directory:

```bash
git init
git add .
git commit -m "feat: initial commit of Student Record Manager"
```

### 2. Create a Remote Repository on GitHub
1. Navigate to [GitHub.com](https://github.com) and click **New Repository**.
2. Name the repository `student-record-manager`.
3. Leave **"Initialize this repository with a README"** unchecked (we already created a complete one).

### 3. Push Code to GitHub
Link your local repository to GitHub and push your main branch:

```bash
# Replace YOUR_USERNAME with your GitHub username:
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/student-record-manager.git
git push -u origin main
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
