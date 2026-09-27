"""Desktop Graphical User Interface (GUI) for Student Record Manager.
Uses Python's built-in Tkinter library (zero external dependencies).
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.models import Student
from src.manager import StudentRecordManager
from src.storage import JSONStorage
from src.exceptions import (
    InvalidEmailError,
    InvalidInputError,
    DuplicateStudentError,
    StudentNotFoundError,
    StorageError,
)


class StudentManagerGUI:
    """Tkinter-based GUI for Student Record Manager."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Student Record Manager (v1.0)")
        self.root.geometry("900x650")
        self.root.minsize(800, 550)

        # Style configuration
        self.setup_styles()

        # Business logic setup
        data_path = os.path.join(os.path.dirname(__file__), "data", "students.json")
        self.storage = JSONStorage(filepath=data_path)
        self.manager = StudentRecordManager(storage=self.storage)

        # Build UI layout
        self.create_widgets()

        # Load initial data
        self.load_data()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Fonts & colors
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"), foreground="#1e3a8a")
        style.configure("Header.TLabel", font=("Helvetica", 11, "bold"), foreground="#334155")
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), background="#e2e8f0")
        style.configure("Treeview", font=("Helvetica", 10), rowheight=26)

    def create_widgets(self):
        # 1. Header Banner
        header_frame = tk.Frame(self.root, bg="#1e3a8a", height=60)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        title_label = tk.Label(
            header_frame,
            text="🎓 Student Record Manager",
            font=("Helvetica", 18, "bold"),
            fg="white",
            bg="#1e3a8a",
            pady=12,
        )
        title_label.pack()

        # 2. Main Container
        main_container = ttk.Frame(self.root, padding="15")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Top Frame: Left = Input Form, Right = Actions
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.X, pady=(0, 15))

        # Form Frame
        form_frame = ttk.LabelFrame(top_frame, text=" Add New Student ", padding="12")
        form_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Inputs
        ttk.Label(form_frame, text="Student ID:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.id_entry = ttk.Entry(form_frame, width=15)
        self.id_entry.grid(row=0, column=1, sticky=tk.W, pady=4, padx=5)

        ttk.Label(form_frame, text="Full Name:").grid(row=0, column=2, sticky=tk.W, pady=4, padx=(10, 0))
        self.name_entry = ttk.Entry(form_frame, width=25)
        self.name_entry.grid(row=0, column=3, sticky=tk.W, pady=4, padx=5)

        ttk.Label(form_frame, text="Email (Regex Validated):").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.email_entry = ttk.Entry(form_frame, width=25)
        self.email_entry.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=4, padx=5)

        ttk.Label(form_frame, text="Course:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.course_entry = ttk.Entry(form_frame, width=20)
        self.course_entry.grid(row=2, column=1, sticky=tk.W, pady=4, padx=5)

        ttk.Label(form_frame, text="GPA (0.0 - 4.0):").grid(row=2, column=2, sticky=tk.W, pady=4, padx=(10, 0))
        self.gpa_entry = ttk.Entry(form_frame, width=10)
        self.gpa_entry.grid(row=2, column=3, sticky=tk.W, pady=4, padx=5)

        # Add Button
        add_btn = tk.Button(
            form_frame,
            text="➕ Add Student",
            command=self.add_student,
            bg="#2563eb",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
        )
        add_btn.grid(row=3, column=0, columnspan=4, pady=(10, 0), sticky=tk.EW)

        # Action Buttons Frame
        action_frame = ttk.LabelFrame(top_frame, text=" File & Quick Actions ", padding="12")
        action_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))

        save_btn = tk.Button(
            action_frame,
            text="💾 Save to File",
            command=self.save_data,
            bg="#059669",
            fg="white",
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        save_btn.pack(fill=tk.X, pady=3)

        reload_btn = tk.Button(
            action_frame,
            text="🔄 Reload File",
            command=self.load_data,
            bg="#d97706",
            fg="white",
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        reload_btn.pack(fill=tk.X, pady=3)

        delete_btn = tk.Button(
            action_frame,
            text="🗑️ Delete Selected",
            command=self.delete_selected,
            bg="#dc2626",
            fg="white",
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        delete_btn.pack(fill=tk.X, pady=3)

        # 3. Search Bar
        search_frame = ttk.Frame(main_container)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="🔍 Search:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda event: self.filter_records())

        clear_search_btn = ttk.Button(search_frame, text="Clear", command=self.clear_search)
        clear_search_btn.pack(side=tk.RIGHT)

        # 4. Table Frame (Treeview)
        table_frame = ttk.Frame(main_container)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "name", "email", "course", "gpa")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="Student ID")
        self.tree.heading("name", text="Full Name")
        self.tree.heading("email", text="Email Address")
        self.tree.heading("course", text="Course / Major")
        self.tree.heading("gpa", text="GPA")

        self.tree.column("id", width=100, anchor=tk.CENTER)
        self.tree.column("name", width=180, anchor=tk.W)
        self.tree.column("email", width=240, anchor=tk.W)
        self.tree.column("course", width=180, anchor=tk.W)
        self.tree.column("gpa", width=80, anchor=tk.CENTER)

        # Scrollbars
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 5. Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, padx=8, pady=3, bg="#f1f5f9")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def populate_table(self, students):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in students:
            self.tree.insert("", tk.END, values=(s.student_id, s.name, s.email, s.course, f"{s.gpa:.2f}"))
        self.status_var.set(f"Displaying {len(students)} student record(s).")

    def add_student(self):
        s_id = self.id_entry.get().strip()
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        course = self.course_entry.get().strip()
        gpa = self.gpa_entry.get().strip()

        try:
            student = Student.create(student_id=s_id, name=name, email=email, course=course, gpa=gpa)
            self.manager.add_student(student)
            self.populate_table(self.manager.get_all_students())

            # Clear inputs
            self.id_entry.delete(0, tk.END)
            self.name_entry.delete(0, tk.END)
            self.email_entry.delete(0, tk.END)
            self.course_entry.delete(0, tk.END)
            self.gpa_entry.delete(0, tk.END)

            messagebox.showinfo("Success", f"Student {student.name} ({student.student_id}) added successfully!")
        except InvalidEmailError as e:
            messagebox.showerror("Invalid Email (Regex Validation)", str(e))
        except InvalidInputError as e:
            messagebox.showerror("Invalid Input Error", str(e))
        except DuplicateStudentError as e:
            messagebox.showerror("Duplicate Student Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add student: {e}")

    def delete_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Required", "Please select a student row to delete.")
            return

        values = self.tree.item(selected_item[0], "values")
        student_id = values[0]
        student_name = values[1]

        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {student_name} ({student_id})?"):
            try:
                self.manager.delete_student(student_id)
                self.populate_table(self.manager.get_all_students())
                messagebox.showinfo("Deleted", f"Student {student_id} removed.")
            except StudentNotFoundError as e:
                messagebox.showerror("Error", str(e))

    def filter_records(self):
        query = self.search_entry.get().strip()
        results = self.manager.search_students(query)
        self.populate_table(results)

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.populate_table(self.manager.get_all_students())

    def save_data(self):
        try:
            count = self.manager.save_to_file()
            messagebox.showinfo("Saved", f"Successfully saved {count} student record(s) to JSON file.")
        except StorageError as e:
            messagebox.showerror("Storage Error", str(e))

    def load_data(self):
        try:
            count = self.manager.load_from_file()
            self.populate_table(self.manager.get_all_students())
            self.status_var.set(f"Loaded {count} student records from file.")
        except StorageError as e:
            messagebox.showerror("Storage Error", str(e))


def main():
    root = tk.Tk()
    app = StudentManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
