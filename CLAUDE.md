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
- `python -m src.main` - Unified test generation interface (module execution)
- `python src/main.py` - Alternative execution (requires proper PYTHONPATH setup)

### Unified Test Generation Interface

The main application now provides a unified interface for all test generation scenarios:

```bash
# Simple mode - direct project specification (recommended)
python -m src.main --simple --project test_projects/c --output ./experiment/generated_tests

# Configuration mode - use project from config
python -m src.main --config simple_c

# List available projects from configuration
python -m src.main --list-projects

# Use custom configuration file
python -m src.main --config complex_example --config-file config/custom_config.yaml

# Alternative execution with PYTHONPATH (if needed)
PYTHONPATH=. python src/main.py --simple --project test_projects/c
```

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
│   ├── generator/       # Test case generation
│   │   ├── __init__.py
│   │   ├── test_generator.py
│   │   └── llm_client.py
│   ├── utils/           # Utility functions
│   │   ├── __init__.py
│   │   ├── compile_db_generator.py
│   │   ├── path_converter.py
│   │   ├── context_compressor.py
│   │   └── libclang_config.py
│   ├── __init__.py
│   └── main.py
├── scripts/             # Demo and utility scripts
│   ├── demo_llm_integration.py
│   ├── demo_complex_c_integration.py
│   └── batch_test_generation.py
├── config/              # Configuration files
│   └── complex_c_test_generation.yaml
├── templates/           # Test template files
├── tests/               # Unit tests for the tool itself
├── test_projects/       # Sample test projects for validation
│   ├── c/              # Simple C math utilities project
│   └── complex_c_project/  # Complex C project with data structures
├── experiment/          # Experimental test generation results
│   ├── generated_tests/            # Auto-generated test directories
│   ├── generated_tests_complex_c/  # Complex project tests
│   ├── generated_tests_deepseek/   # DeepSeek generated tests
│   └── generated_tests_demo/       # Demo test files
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
- **Complex C Project Support**: Full support for multi-module C projects with:
  - Linked list data structures (12 functions)
  - Hash table implementations (10 functions) 
  - Memory pool utilities (9 functions)
  - Cross-module function call analysis
- **Batch Processing**: Automated batch test generation for large codebases
- **Comprehensive Test Generation**: AI-powered generation of:
  - Normal case testing
  - Boundary condition testing
  - Exception handling scenarios
  - Mocking of external dependencies (malloc, etc.)
  - Multiple call scenario testing

### ⚠️ Pending Improvements
- C++ class method analysis needs enhancement
- Better handling of complex template types
- Enhanced error handling for different LLM providers
- Optimization for very large codebases (>1000 functions)

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
- Generated tests saved in `experiment/generated_tests_deepseek_*/` directories
- **Proxy Configuration Note**: If encountering proxy issues, clear malformed proxy environment variables:
  ```bash
  unset https_proxy http_proxy all_proxy
  ```

### Quick Test Generation
```bash
# Simple project test generation (using unified interface)
DEEPSEEK_API_KEY="your_key" python -m src.main --config simple_c

# Complex project test generation
DEEPSEEK_API_KEY="your_key" python -m src.main --config complex_example

# Direct project specification (without config)
python -m src.main --simple --project test_projects/c --output ./experiment/generated_tests

# List available projects
python -m src.main --list-projects
```

### Test Directory Organization

All generated test directories are now organized under the `experiment/` directory. New test generations should follow a timestamp-based naming convention:

```bash
# Example of timestamp-based test directory naming
experiment/generated_tests/c_20240824_092434/  # project_timestamp format
experiment/generated_tests_complex_c/complex_c_20240824_150045/
```

This organization helps:
- Keep the root directory clean
- Provide clear versioning of test generation experiments
- Enable easy comparison between different test generation runs
- Maintain historical test generation results for analysis

## Complex C Project Details

The complex C project located in `test_projects/complex_c_project/` demonstrates the tool's capabilities with:

### **Data Structures Implemented**
- **Linked List Module** (`data_structures/linked_list.{h,c}`):
  - 12 functions including create, destroy, append, prepend, insert/remove at index
  - Comprehensive memory management with proper error handling
  - Iterator pattern implementation

- **Hash Table Module** (`data_structures/hash_table.{h,c}`):
  - 10 functions with DJB2 hashing algorithm
  - Dynamic resizing and collision handling
  - Key-value storage with efficient lookup

- **Memory Pool Module** (`utils/memory_pool.{h,c}`):
  - 9 functions implementing best-fit allocation
  - Memory usage tracking and validation
  - Error code enumeration for robust error handling

### **Test Generation Features**
- **Comprehensive Coverage**: Tests generated for all 31 testable functions
- **Mocking Support**: Automatic mocking of external dependencies (malloc, etc.)
- **Boundary Testing**: Tests for normal, boundary, and exception scenarios
- **Multi-call Scenarios**: Testing functions under multiple invocation patterns
- **Structure Validation**: Verification of data structure initialization

## Important Patterns

- **Function filtering**: Non-static (C), public/static methods (C++)
- **Context minimization**: Extract only essential information for test generation
- **Mock generation**: Automatically mock external function dependencies
- **Traceability**: Include timestamps, source version, and model parameters in generated tests
- **Batch processing**: Automated generation for large codebases with rate limiting
- **Error resilience**: Fallback to mock tests when LLM generation fails

## Code Cleanup and Refactoring

### ✅ Completed Refactoring
- **Unified Interface**: All test generation functionality consolidated into `src/main.py`
- **Removed Redundancy**: Eliminated duplicate scripts (`generate_tests.py`, `run_test_generation.py`, `analyze_complex_project.py`, etc.)
- **Clean Root Directory**: Reduced clutter by removing redundant Python scripts
- **Consistent Architecture**: Single entry point with multiple operation modes

### Operation Modes
1. **Simple Mode**: Direct project specification without configuration
2. **Configuration Mode**: Use pre-configured projects from YAML config
3. **Project Listing**: Discover available configured projects

## Lessons Learned and Common Pitfalls

### 🔧 Repeated Issues and Solutions

1. **Proxy Configuration Issues**:
   - **Problem**: Malformed proxy environment variables causing "Invalid IPv4 address" errors
   - **Solution**: Clear proxy variables before running LLM integration:
     ```bash
     unset https_proxy http_proxy all_proxy
     # Or use clean environment:
     env -i DEEPSEEK_API_KEY="your_key" python script.py
     ```

2. **Python Path Configuration**:
   - **Problem**: Module import errors due to incorrect Python path
   - **Solution**: Use module execution (`python -m src.main`) or ensure proper path setup:
     ```python
     import sys
     from pathlib import Path
     sys.path.insert(0, str(Path(__file__).parent.parent))
     ```
   - **Recommended**: Always use `python -m src.main` for consistent execution

3. **libclang Configuration**:
   - **Problem**: libclang not found or improperly configured
   - **Solution**: Use unified configuration approach:
     ```python
     from src.utils.libclang_config import ensure_libclang_configured
     ensure_libclang_configured()
     ```

4. **LLM API Timeouts**:
   - **Problem**: Long-running test generation timing out
   - **Solution**: Implement batch processing with delays:
     ```python
     # Add delays between API calls
     time.sleep(2)  # Between individual generations
     time.sleep(10) # Between batches
     ```

5. **Function Analysis Errors**:
   - **Problem**: Dictionary vs object attribute access issues
   - **Solution**: Consistent access patterns and proper error handling

### 🚀 Best Practices Established

1. **Always use absolute paths** for file operations
2. **Implement comprehensive error handling** in all LLM interactions
3. **Use environment isolation** for reliable API connectivity
4. **Batch processing** for large-scale test generation
5. **Fallback mechanisms** when LLM generation fails
6. **Proper mocking** of external dependencies in tests
7. **Memory safety** in all test cases (proper cleanup)