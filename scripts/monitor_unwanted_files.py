#!/usr/bin/env python3
"""
Monitor and automatically remove unwanted auto-generated files.
This script runs in the background to prevent file recreation.
"""

import os
import time
import shutil
from pathlib import Path

# Define unwanted paths relative to project root
UNWANTED_PATHS = [
    "src/Api/schemas/",
    "src/Services/", 
    "src/Api/Controllers/",
    "src/Models/Enums/",
    "src/database/",
    "celerybeat/",
    "CELERY_SETUP.md",
    "LESSON_FEATURE_IMPLEMENTATION.md", 
    "PGVECTOR_SETUP.md",
    "postman_collection.json",
    "test_lesson.pdf",
    "test_lesson.txt",
    "test_pgvector.py",
    "src/Tasks/example_to_clarify.py",
    "src/Models/DBSchemes/Schemes/parent_student_association.py",
    "src/Models/repositories/academic_term_repository_new.py",
    "src/Models/usage_examples.py",
    "src/Models/USAGE_GUIDE.md",
    "src/Api/Schemes/token.py",
    "src/Api/Schemes/user.py",
    "src/Api/routers/auth_route.py",
    "Docker/docker-compose.dev.yml"
]

def remove_unwanted_files(project_root: Path):
    """Remove unwanted files and directories"""
    removed_items = []
    
    for unwanted_path in UNWANTED_PATHS:
        full_path = project_root / unwanted_path
        
        if full_path.exists():
            try:
                if full_path.is_dir():
                    shutil.rmtree(full_path)
                    removed_items.append(f"Removed directory: {unwanted_path}")
                else:
                    full_path.unlink()
                    removed_items.append(f"Removed file: {unwanted_path}")
            except Exception as e:
                print(f"Error removing {unwanted_path}: {e}")
    
    return removed_items

def main():
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent.resolve()
    print(f"Monitoring unwanted files in: {project_root}")
    print("Press Ctrl+C to stop monitoring")
    
    try:
        while True:
            removed_items = remove_unwanted_files(project_root)
            
            if removed_items:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Detected and removed unwanted files:")
                for item in removed_items:
                    print(f"  - {item}")
            
            # Check every 5 seconds
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nFile monitoring stopped.")

if __name__ == "__main__":
    main()
