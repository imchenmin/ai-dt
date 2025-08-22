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

## Code Structure (Current)

```
ai-dt/
├── src/
│   ├── parser/          # Code parsing (compile_commands.json analysis)
│   │   ├── __init__.py
│   │   └── compilation_db.py
│   ├── analyzer/        # Function identification and filtering
│   │   ├── __init__.py
│   │   ├── call_analyzer.py
│   │   ├── clang_analyzer.py
│   │   └── function_analyzer.py
│   ├── generator/       # Test case generation (directory exists)
│   ├── utils/           # Utility functions
│   │   ├── compile_db_generator.py
│   │   └── path_converter.py
│   ├── __init__.py
│   └── main.py
├── config/              # Configuration files
├── templates/           # Test template files
├── tests/               # Unit tests for the tool itself
├── test_projects/       # Sample test projects
│   ├── c/              # C language test project
│   └── cpp/            # C++ language test project
├── docs/                # Documentation
├── requirements.txt     # Python dependencies
└── requirements.md      # Requirements documentation
```

## Key Constraints

- **Model Limitations**: 16K context window, 20K token maximum
- **Testing Framework**: Google Test (gtest) + MockCpp only
- **Resource Constraints**: Designed for nightly runs in resource-limited environments
- **Language Support**: C and C++ codebases

## Validation Status

### ✅ Verified Features
- **libclang Integration**: Successfully parses C/C++ AST
- **Function Signature Extraction**: Correctly extracts return types and parameters
- **Testable Function Identification**: 
  - C: Non-static functions correctly identified
  - C++: Public methods and free functions identified
- **Call Site Analysis**: Detects function call locations across project
- **Compile Commands Processing**: Handles compile_commands.json with relative paths

### ⚠️ Pending Improvements
- C++ class method analysis needs enhancement
- Function deduplication across translation units
- Better handling of complex template types

## Important Patterns

- Function filtering: Non-static (C), public/static methods (C++)
- Context minimization: Extract only essential information for test generation
- Mock generation: Automatically mock external function dependencies
- Traceability: Include timestamps, source version, and model parameters in generated tests