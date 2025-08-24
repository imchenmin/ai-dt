# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python-based C/C++ unit test generation tool that automatically generates Google Test (gtest) + MockCpp test cases using AI models with constrained resources.

## Key Technologies

- **Programming Language**: Python
- **Code Analysis**: Clang, libclang, tree-sitter
- **Test Generation**: OpenAI API (GPT models), DeepSeek API
- **Configuration**: YAML
- **Testing Framework**: Google Test + MockCpp

## Architecture Components

- **Parser**: Analyzes compile_commands.json, extracts dependencies and compilation flags
- **Function Analyzer**: Identifies testable functions (non-static C, public/static C++ methods)
- **Context Extractor**: Gathers function signatures, dependencies, macros, and data structures
- **Test Generator**: Creates comprehensive test cases with boundary conditions and exception handling

## Quick Start

### Setup
```bash
pip install -r requirements.txt
cp .env.example .env  # Add OPENAI_API_KEY and/or DEEPSEEK_API_KEY
```

### Test Generation
```bash
# Simple mode (recommended)
python -m src.main --simple --project test_projects/c --output ./experiment/generated_tests

# Configuration mode
python -m src.main --config simple_c

# List available projects
python -m src.main --list-projects
```

## Development Commands

- `python -m venv venv` - Create virtual environment
- `python -m pytest tests/` - Run tests
- `python -m src.main` - Unified test generation interface
- `python src/main.py` - Alternative execution (requires PYTHONPATH=.)

## Key Constraints

- **Model Limitations**: 16K context window, 20K token maximum
- **Resource Constraints**: Designed for nightly runs in resource-limited environments
- **Language Support**: C and C++ codebases

## Validation Status

### ✅ Verified Features
- libclang Integration with clang-10 support
- Function analysis and signature extraction
- Cross-project function call detection with deduplication
- Complete OpenAI and DeepSeek API support
- Multi-module C project support
- Automated test generation for large codebases
- Comprehensive testing coverage
- Automatic function filtering (excludes stdlib functions)

### ⚠️ Pending Improvements
- C++ class method analysis enhancement
- Better handling of complex template types
- Enhanced error handling for different LLM providers
- Optimization for very large codebases (>1000 functions)

## Critical Setup Notes

### libclang Configuration
```python
from src.utils.libclang_config import ensure_libclang_configured
ensure_libclang_configured()  # Auto-discovers libclang library
```

### Manual Configuration (Ubuntu clang-10)
```python
import clang.cindex
clang.cindex.Config.set_library_file('/usr/lib/llvm-10/lib/libclang.so.1')
```

### Environment Variable
```bash
export LIBCLANG_PATH=/usr/lib/llvm-10/lib/libclang.so.1
```

## Prompt Template System

### Language-Specific Prompts
- **C functions**: Specialized for C language testing patterns
- **C++ functions**: Focus on exceptions, memory management, templates
- Automatic detection based on file extension

### Specialized Templates
- **Memory functions**: Extra safety guidance for allocation/deletion
- **Dynamic Mock requirements**: Only when external dependencies exist
- **Safety emphasis**: Avoid testing undefined behavior

### Key Features
- Clear language identification (C++ instead of CPP)
- Context-aware prompt generation
- Enhanced safety guidance for memory operations
- Reduced confusion in LLM instructions

## Test Directory Organization

All generated tests are organized under `experiment/` with timestamp-based naming:
```bash
experiment/generated_tests/c_20240824_092434/  # project_timestamp format
experiment/generated_tests_complex_c/complex_c_20240824_150045/
```

## Complex C Project Reference

The complex C project in `test_projects/complex_c_project/` demonstrates:
- Multi-module architecture (linked lists, hash tables, memory utilities)
- Cross-module function calls and dependency analysis
- 31+ testable functions with varied complexity
- Real-world patterns for memory management and error handling

## Best Practices

1. **Always use absolute paths** for file operations
2. **Implement comprehensive error handling** in LLM interactions
3. **Use environment isolation** for reliable API connectivity
4. **Batch processing** for large-scale test generation
5. **Fallback mechanisms** when LLM generation fails
6. **Proper mocking** of external dependencies
7. **Memory safety** in all test cases

## Common Issues & Solutions

- **Proxy issues**: Clear malformed proxy variables
- **Python path**: Use `python -m src.main` for consistent execution
- **libclang setup**: Use unified configuration approach
- **API timeouts**: Implement batch processing with delays
- **Function analysis**: Maintain consistent access patterns

## Recent Improvements

### ✅ Completed Enhancements
- **Enhanced Logging**: Added timestamp functionality and log saving to experiment directories
- **MockCpp Guidance**: Fixed prompt templates to handle C vs C++ mocking requirements appropriately
- **Batch Processing**: Implemented two-phase processing (prompt generation first, then LLM processing)
- **Progress Tracking**: Added real-time progress, ETA, and generation statistics
- **Language-Specific Mocking**: C projects no longer include MockCpp references, C++ projects use proper MockCpp guidance

### 🚧 Pending Enhancements
- **Enhanced Logging System**: Add timestamp support and save logs to experiment directories
- **MockCpp Documentation**: Create comprehensive MockCpp usage guide for C++ projects and remove MockCpp references from C projects
- **Batch Processing Optimization**: Implement concurrent processing with prompt-first generation approach
- **Progress Statistics**: Add generation rate tracking and ETA estimation
- **Concurrent Processing**: Support for parallel LLM requests to improve generation speed
- **Enhanced Error Handling**: Better retry mechanisms and error recovery
- **Log Analysis**: Automated log parsing and performance reporting
- **Template Optimization**: Further refinement of prompt templates based on generation results

- 每一次完成整个大的工作量并测试完成后，将工作日志写到 @docs/work_logs/ 中