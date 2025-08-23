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
- **libclang Integration**: Successfully parses C/C++ AST (supports clang-10)
- **Function Signature Extraction**: Correctly extracts return types and parameters
- **Function Body Extraction**: Extracts complete function implementation code
- **Testable Function Identification**: 
  - C: Non-static functions correctly identified
  - C++: Public methods and free functions identified
- **Call Site Analysis**: Detects function call locations across project with deduplication
- **Compile Commands Processing**: Handles compile_commands.json with relative paths
- **LLM Integration**: Complete OpenAI and DeepSeek API support
  - OpenAI: GPT-3.5-turbo, GPT-4 models
  - DeepSeek: deepseek-chat, deepseek-coder models (tested and working)
  - Multi-provider configuration management
  - Context compression for token optimization

### ⚠️ Pending Improvements
- C++ class method analysis needs enhancement
- Better handling of complex template types
- Enhanced error handling for different LLM providers
- Batch processing optimization for large codebases

## Claude Code Integration Notes

### libclang Configuration (IMPORTANT - Setup Required)

**⚠️ CRITICAL SETUP STEP**: libclang configuration is required before using any clang functionality.

#### Unified Configuration Approach (Recommended)
```python
# In any file that uses clang functionality:
from src.utils.libclang_config import ensure_libclang_configured
ensure_libclang_configured()  # Auto-discovers libclang library

# Now safe to use clang functionality
```

#### Manual Configuration (Alternative)
For Ubuntu with clang-10:
```python
import clang.cindex
clang.cindex.Config.set_library_file('/usr/lib/llvm-10/lib/libclang.so.1')
```

#### Environment Variable Approach
```bash
# Set environment variable
export LIBCLANG_PATH=/usr/lib/llvm-10/lib/libclang.so.1
```

### DeepSeek API Setup
- Set `DEEPSEEK_API_KEY` in environment or `.env` file
- Tested and verified working with both deepseek-chat and deepseek-coder models
- Generated tests saved in `generated_tests_deepseek_*/` directories

### Quick Test Generation
```bash
DEEPSEEK_API_KEY="your_key" python demo_deepseek_integration.py
```

## Important Patterns

- Function filtering: Non-static (C), public/static methods (C++)
- Context minimization: Extract only essential information for test generation
- Mock generation: Automatically mock external function dependencies
- Traceability: Include timestamps, source version, and model parameters in generated tests