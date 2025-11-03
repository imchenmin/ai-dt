# Project Wiki: AI-Driven Test Generator (ai_dt)

This document provides a comprehensive overview of the `ai_dt` project, an AI-Driven Test Generator for C/C++ code.

## 1. Project Overview

`ai_dt` is a command-line tool designed to automate the process of writing unit tests for C and C++ projects. It leverages the power of Large Language Models (LLMs) to analyze source code and generate meaningful tests, helping developers improve code quality and reduce manual testing effort.

The tool is built in Python and uses the Clang library for accurate C/C++ code parsing and analysis.

## 2. Key Features

*   **Automated Test Generation**: Automatically creates unit test files for specified C/C++ source files.
*   **LLM-Powered**: Integrates with various LLM providers to generate human-like and relevant test code.
*   **Clang-Based Analysis**: Uses `libclang` to build an accurate Abstract Syntax Tree (AST) of the code, ensuring a deep understanding of functions, data structures, and dependencies.
*   **Flexible Modes**: Offers multiple modes of operation, from a simple, zero-configuration mode for quick tasks to a powerful configuration-driven mode for complex projects.
*   **Context-Aware Prompts**: Intelligently gathers context for each function (including its body, dependencies, and related types) to create effective prompts for the LLM.
*   **Extensible**: The architecture allows for adding new LLM providers and customizing prompt templates.

## 3. How it Works

The test generation process follows a clear pipeline:

1.  **Code Analysis**: The tool parses the C/C++ project using a `compile_commands.json` file. It traverses the Abstract Syntax Tree (AST) to identify functions suitable for testing.
2.  **Context Extraction**: For each identified function, it extracts relevant context, such as the function's signature and body, dependent types, and macros.
3.  **Prompt Generation**: Using Jinja2 templates, it constructs a detailed prompt containing the function's context and instructions for the LLM on how to generate a test.
4.  **LLM Interaction**: The generated prompt is sent to a configured LLM (e.g., via the Dify client or another provider).
5.  **Test Code Generation**: The LLM returns a block of C/C++ code containing the unit test.
6.  **Output**: The tool saves the generated test code into a specified output directory, organizing the tests in a logical structure.

## 4. Usage

`ai_dt` is a command-line tool. You can run it using the `ai-dt` script after installation.

```bash
# General syntax
ai-dt [MODE] [OPTIONS]
```

### Modes of Operation

#### a) Simple Mode (`--simple`)

For quick, on-the-fly test generation without a configuration file.

```bash
ai-dt --simple \
      --project /path/to/your/project \
      --output /path/to/generated_tests \
      --compile-commands /path/to/your/project/compile_commands.json \
      --include "src/utils/*.c"
```

**Arguments:**
*   `--project`: Path to the project's root directory.
*   `--output`: Directory where generated tests will be saved.
*   `--compile-commands`: Path to the `compile_commands.json` file.
*   `--include`/`--exclude`: (Optional) Patterns to include or exclude specific files.

#### b) Configuration Mode (`--config`)

The most powerful mode, driven by a `test_generation.yaml` file. This is ideal for managing multiple complex projects.

```bash
ai-dt --config my_project_name --profile comprehensive
```

**Arguments:**
*   `--config <PROJECT_NAME>`: Specifies the project to test, as defined in your YAML config file.
*   `--profile <PROFILE_NAME>`: (Optional) Selects an execution profile (e.g., `quick`, `comprehensive`) from the config.
*   `--config-file`: (Optional) Path to a custom configuration file.
*   `--prompt-only`: (Optional) Generates prompts but does not call the LLM, allowing you to review the prompts.

#### c) Single File Mode (`--single-file`)

Quickly generate tests for a single source file.

```bash
ai-dt --single-file src/my_module/my_file.c \
      --project /path/to/your/project \
      --output /path/to/generated_tests
```

**Arguments:**
*   `--single-file <FILE_PATH>`: The path to the specific file you want to test.
*   `--project`: The root directory of the project (needed for context).
*   `--output`: Directory to save the generated test.

#### d) List Projects (`--list-projects`)

Lists all projects defined in the configuration file.

```bash
ai-dt --list-projects
```

## 5. Repository Components

This repository contains several key components:

*   **`ai_dt` (Core Logic)**: Located in `src/`, this is the main test generation application.
*   **Dify API Client**: A Python client for interacting with the Dify platform, likely used as one of the LLM backends for the service.
*   **`mock++` Framework**: A C++ mocking framework documented in `docs/`. This may be used by the LLM to generate tests involving mocks, or it might be a reference for test patterns.
