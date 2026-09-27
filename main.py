#!/usr/bin/env python3
"""
Student Record Manager
Main entry point for starting the application.
"""

import os
import sys

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.manager import StudentRecordManager
from src.storage import JSONStorage
from src.cli import StudentRecordCLI


def main() -> None:
    """Initialize application components and run CLI loop."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    data_file = os.path.join(data_dir, "students.json")

    storage = JSONStorage(filepath=data_file)
    manager = StudentRecordManager(storage=storage)
    cli = StudentRecordCLI(manager=manager)

    cli.run()


if __name__ == "__main__":
    main()
