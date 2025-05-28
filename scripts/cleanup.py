#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cleanup Script for FitBrainLab

This script removes temporary files, cache files, and other artifacts
to prepare the project for deployment.
"""

import os
import sys
import shutil
from pathlib import Path

# Project root directory
ROOT_DIR = Path(__file__).parent

def print_with_color(text, color_code):
    """Print text with ANSI color code"""
    print(f"\033[{color_code}m{text}\033[0m")

def clean_pycache():
    """Remove Python cache files and directories"""
    print_with_color("Cleaning Python cache files...", 36)  # Cyan
    
    # Find and remove __pycache__ directories
    count = 0
    for pycache_dir in ROOT_DIR.glob("**/__pycache__"):
        if pycache_dir.is_dir():
            print(f"Removing {pycache_dir}")
            shutil.rmtree(pycache_dir)
            count += 1
    
    # Find and remove .pyc and .pyo files
    pyc_count = 0
    for pyc_file in ROOT_DIR.glob("**/*.py[co]"):
        print(f"Removing {pyc_file}")
        pyc_file.unlink()
        pyc_count += 1
    
    print_with_color(f"Removed {count} __pycache__ directories and {pyc_count} .pyc/.pyo files", 32)  # Green

def clean_temp_files():
    """Remove temporary and system files"""
    print_with_color("Cleaning temporary files...", 36)  # Cyan
    
    # List of patterns to remove
    patterns = [
        "**/.DS_Store",        # macOS system files
        "**/*.log",            # Log files
        "**/*.bak",            # Backup files
        "**/*.~",              # Temp files
        "**/*.swp",            # Vim swap files
        "**/*.swo",            # Vim swap files
        "**/*.db-journal"      # SQLite journal files
    ]
    
    count = 0
    for pattern in patterns:
        for file_path in ROOT_DIR.glob(pattern):
            if file_path.is_file():
                print(f"Removing {file_path}")
                file_path.unlink()
                count += 1
    
    print_with_color(f"Removed {count} temporary files", 32)  # Green

def clean_database_files():
    """Remove SQLite database files"""
    print_with_color("Cleaning database files...", 36)  # Cyan
    
    # Check for SQLite database
    db_path = ROOT_DIR / "instance" / "fitbrainlab.db"
    if db_path.exists():
        print(f"Found SQLite database at {db_path}")
        print(f"Removing {db_path}")
        db_path.unlink()
        print_with_color("Database removed", 32)  # Green
    else:
        print("No SQLite database found")

def create_data_directory():
    """Create data directory for JSON data files"""
    print_with_color("Creating data directory...", 36)  # Cyan
    
    data_dir = ROOT_DIR / "data"
    if not data_dir.exists():
        data_dir.mkdir()
        print_with_color(f"Created data directory at {data_dir}", 32)  # Green
    else:
        print_with_color(f"Data directory already exists at {data_dir}", 33)  # Yellow

def ensure_deployment_files():
    """Ensure necessary files for deployment exist"""
    print_with_color("Checking deployment files...", 36)  # Cyan
    
    # List of files to check
    deployment_files = [
        (ROOT_DIR / "requirements.txt", "Dependencies file"),
        (ROOT_DIR / "Procfile", "Heroku Procfile"),
        (ROOT_DIR / "wsgi.py", "WSGI entry point")
    ]
    
    for file_path, description in deployment_files:
        if file_path.exists():
            print_with_color(f"✓ {description} found: {file_path}", 32)  # Green
        else:
            print_with_color(f"✗ {description} missing: {file_path}", 31)  # Red

def main():
    print_with_color("\n=== FitBrainLab Cleanup Utility ===", 35)  # Purple
    
    # Perform cleanup tasks
    clean_pycache()
    clean_temp_files()
    clean_database_files()
    create_data_directory()
    ensure_deployment_files()
    
    print_with_color("\nCleanup complete! Your project is ready for deployment.", 35)  # Purple

if __name__ == "__main__":
    main()
