"""
Script to run PyLint on the project and generate a report.
This demonstrates code quality using PyLint as required for the course.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_pylint():
    """Run PyLint on main project files and display results."""

    # Change to parent directory first (project root)
    original_dir = os.getcwd()
    parent_dir = Path(__file__).parent.parent
    os.chdir(parent_dir)

    # Files and directories to check (from project root)
    targets = [
        'ticket_management_system/__init__.py',
        'ticket_management_system/app.py',
        'ticket_management_system/models.py',
        'ticket_management_system/exceptions.py',
        'ticket_management_system/extensions.py',
        'ticket_management_system/utils.py',
        'ticket_management_system/resources/',
        'ticket_management_system/static/schema/'
    ]

    print("=" * 70)
    print("Running PyLint Code Quality Check")
    print("=" * 70)
    print()
    print(f"Working directory: {os.getcwd()}")
    print()

    # Run pylint with ignoring specific warnings as per course requirements
    cmd = [
        'python', '-m', 'pylint'
    ] + targets + [
        '--score=yes',
        '--disable=no-member,import-outside-toplevel,no-self-use',
        '--max-line-length=120'
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        # Save to file
        output_file = Path('ticket_management_system/pylint_report.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)

        print()
        print("=" * 70)
        print(f"Report saved to: {output_file.absolute()}")
        print("=" * 70)

        # Extract score
        for line in result.stdout.split('\n'):
            if 'rated at' in line:
                print()
                print("SCORE:", line.strip())
                print()

                # Check if score is good enough
                try:
                    score = float(line.split('rated at ')[1].split('/')[0])
                    if score >= 9.0:
                        print("✅ EXCELLENT! Score is 9.0 or higher")
                        print("   (Course requirement: 9.0+ for full points)")
                    elif score >= 8.0:
                        print("⚠️  WARNING: Score is below 9.0")
                        print("   (Course requirement: 9.0+ for full points)")
                    else:
                        print("❌ NEEDS IMPROVEMENT: Score is below 8.0")
                        print("   (Course requirement: 9.0+ for full points)")
                except (ValueError, IndexError):
                    pass

        # Change back to original directory
        os.chdir(original_dir)

        return result.returncode

    except Exception as e:
        print(f"Error running PyLint: {e}")
        os.chdir(original_dir)
        return 1

if __name__ == '__main__':
    sys.exit(run_pylint())
