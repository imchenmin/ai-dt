#!/usr/bin/env python3
"""
Main entry point for AI-Driven Test Generator when run as a module
"""

from src.main import main

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)