#!/usr/bin/env python3
"""
Syntax check for the GUI app.
"""

import ast
import sys

def check_syntax(file_path):
    """Check Python syntax without importing modules"""
    try:
        with open(file_path, 'r') as f:
            source = f.read()
        
        # Parse the AST to check syntax
        ast.parse(source)
        print(f"✓ Syntax OK: {file_path}")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax Error in {file_path}:")
        print(f"  Line {e.lineno}: {e.text}")
        print(f"  {e.msg}")
        return False
    except Exception as e:
        print(f"✗ Error checking {file_path}: {e}")
        return False

if __name__ == "__main__":
    if check_syntax("src/gui/app.py"):
        print("The GUI app file has correct syntax!")
    else:
        print("There are syntax errors that need to be fixed.")
        sys.exit(1)