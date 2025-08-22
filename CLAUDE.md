# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based C/C++ unit test generation tool that automatically generates Google Test (gtest) + MockCpp test cases. The tool analyzes C/C++ codebases and generates comprehensive test suites using AI models with constrained resources.

## Key Architecture Components

- **Parser Module**: Analyzes compile_commands.json, extracts file dependencies and compilation flags
- **Function Analyzer**: Identifies testable functions (non-static for C, public/static methods for C++)
- **Context Extractor**: Gathers function signatures, dependencies, macros, and data structures
- **Test Generator**: Creates gtest + MockCpp test cases with boundary conditions and exception handling

## Development Commands

Since this is a new Python project, typical development commands will include:
- `python -m venv venv` - Create virtual environment
- `pip install -r requirements.txt` - Install dependencies
- `python -m pytest tests/` - Run tests
- `python src/main.py` - Run the main application

## Code Structure (Planned)

```
ai-dt/
├── src/
│   ├── parser/          # Code parsing (compile_commands.json analysis)
│   ├── analyzer/        # Function identification and filtering
│   ├── generator/       # Test case generation
│   └── utils/           # Utility functions
├── config/              # Configuration files
├── templates/           # Test template files
├── tests/               # Unit tests for the tool itself
└── docs/                # Documentation
```

## Key Constraints

- **Model Limitations**: 16K context window, 20K token maximum
- **Testing Framework**: Google Test (gtest) + MockCpp only
- **Resource Constraints**: Designed for nightly runs in resource-limited environments
- **Language Support**: C and C++ codebases

## Important Patterns

- Function filtering: Non-static (C), public/static methods (C++)
- Context minimization: Extract only essential information for test generation
- Mock generation: Automatically mock external function dependencies
- Traceability: Include timestamps, source version, and model parameters in generated tests