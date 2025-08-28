# AI-DT MCP Integration Guide

This document describes how to integrate the AI-DT prompt generation service with VS Code Continue using the Model Context Protocol (MCP).

## Overview

The AI-DT MCP server provides three main tools for C/C++ test generation:

1. **generate_test_prompt** - Generate Google Test + MockCpp prompt for a specific function
2. **analyze_function_dependencies** - Analyze function dependencies and context
3. **get_function_signature** - Get detailed function signature information

## Installation and Setup

### 1. Install Dependencies

Ensure you have the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure VS Code Continue

Add the following configuration to your VS Code Continue settings (`~/.continue/config.json` or workspace settings):

```json
{
  "mcpServers": {
    "ai-dt-prompt-generator": {
      "command": "python",
      "args": [
        "-m",
        "src.mcp_server"
      ],
      "env": {
        "PYTHONPATH": ".",
        "LIBCLANG_PATH": "/usr/lib/llvm-10/lib/libclang.so.1"
      },
      "cwd": "/path/to/ai-dt",
      "description": "AI-DT Prompt Generator for Google Test + MockCpp"
    }
  }
}
```

**Important**: Update the `cwd` path to point to your AI-DT project directory.

### 3. Environment Variables

Set the required environment variables:
```bash
export PYTHONPATH="/path/to/ai-dt"
export LIBCLANG_PATH="/usr/lib/llvm-10/lib/libclang.so.1"
```

## Usage Examples

### Using the MCP Tools

Once configured, you can use the AI-DT tools directly in VS Code Continue:

#### 1. Generate Test Prompt

```json
{
  "name": "generate_test_prompt",
  "arguments": {
    "file_path": "/path/to/your/file.c",
    "function_name": "your_function_name",
    "project_root": "/path/to/project",
    "compilation_db_path": "/path/to/compile_commands.json"
  }
}
```

#### 2. Analyze Function Dependencies

```json
{
  "name": "analyze_function_dependencies",
  "arguments": {
    "file_path": "/path/to/your/file.c",
    "function_name": "your_function_name",
    "project_root": "/path/to/project"
  }
}
```

#### 3. Get Function Signature

```json
{
  "name": "get_function_signature",
  "arguments": {
    "file_path": "/path/to/your/file.c",
    "function_name": "your_function_name"
  }
}
```

### Example: Generating Tests for a C Function

1. Open your C/C++ file in VS Code
2. Use Continue's command palette to call the MCP tools
3. Select the function you want to test
4. Generate comprehensive Google Test + MockCpp test cases

## Response Format

### generate_test_prompt Response

```json
{
  "prompt": "Full LLM prompt for test generation",
  "function_info": {
    "name": "function_name",
    "signature": "return_type function_name(parameters)",
    "return_type": "return_type",
    "parameters": [...],
    "body": "full function body",
    "location": "file:line",
    "language": "c/cpp"
  },
  "dependencies": {
    "called_functions": [...],
    "macros": [...],
    "macro_definitions": [...],
    "data_structures": [...],
    "dependency_definitions": [...]
  },
  "language": "c"
}
```

### analyze_function_dependencies Response

```json
{
  "function": {
    "name": "function_name",
    "return_type": "return_type",
    "parameters": [...],
    "file": "file_path",
    "line": 123
  },
  "dependencies": {
    "called_functions": [...],
    "macros_used": [...],
    "data_structures": [...],
    "include_directives": [...]
  },
  "called_functions": [...],
  "macros_used": [...],
  "data_structures": [...]
}
```

### get_function_signature Response

```json
{
  "signature": "return_type function_name(type param1, type param2)",
  "return_type": "return_type",
  "parameters": [
    {"name": "param1", "type": "type"},
    {"name": "param2", "type": "type"}
  ],
  "location": "file:line",
  "language": "c/cpp"
}
```

## Advanced Configuration

### Custom libclang Path

If you have a different libclang installation, update the `LIBCLANG_PATH` environment variable:

```bash
export LIBCLANG_PATH="/usr/lib/llvm-15/lib/libclang.so.1"
```

### Project-Specific Configuration

For large projects, you can use selective parsing:

```json
{
  "name": "generate_test_prompt",
  "arguments": {
    "file_path": "src/module/file.c",
    "function_name": "target_function",
    "project_root": "/large/project",
    "compilation_db_path": "/large/project/compile_commands.json",
    "include_patterns": ["src/module/", "src/utils/"],
    "exclude_patterns": ["third_party/", "vendor/"]
  }
}
```

## Troubleshooting

### Common Issues

1. **libclang not found**: Ensure `LIBCLANG_PATH` is set correctly
2. **File not found**: Check file paths and project root configuration
3. **Function not found**: Verify function name and file content
4. **Compilation database issues**: Ensure compile_commands.json exists and is valid

### Debug Mode

Enable debug logging by setting the log level:

```bash
export LOG_LEVEL=DEBUG
```

## Features

- ✅ Full function body preservation (no truncation)
- ✅ Static function implementation inclusion
- ✅ Intelligent dependency ranking and selection
- ✅ Token-aware context compression
- ✅ Support for both C and C++ codebases
- ✅ Integration with Google Test + MockCpp
- ✅ VS Code Continue compatibility
- ✅ Selective parsing for large projects

## Limitations

- Requires libclang for C/C++ analysis
- Compilation database (compile_commands.json) recommended for accurate analysis
- Large projects may require selective parsing for optimal performance

## Support

For issues and questions, please refer to the AI-DT project documentation or create an issue in the project repository.