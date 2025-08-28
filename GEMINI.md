# Project Overview

This project is a command-line tool for automatically generating unit tests for C/C++ projects. It leverages the power of Clang for accurate code parsing and Large Language Models (LLMs) for intelligent test case generation.

## Key Technologies

*   **Programming Language:** Python
*   **Code Analysis:** Clang, libclang, tree-sitter
*   **Test Generation:** OpenAI API (GPT models), Dify API (various models)
*   **Configuration:** YAML
*   **Dependencies:** See `requirements.txt` for a full list of Python packages.

## Architecture

The tool follows a modular architecture:

*   **`src/parser`:** Handles parsing of the compilation database (`compile_commands.json`) to understand the project's structure and compiler flags.
*   **`src/analyzer`:** Uses Clang to analyze the C/C++ source code, extract information about functions, and build a context for test generation.
*   **`src/generator`:** Contains the logic for interacting with the LLM, sending the code context, and generating the unit test files. This now includes support for Dify API.
*   **`src/utils`:** Provides utility functions for file handling, configuration loading, and other common tasks.
*   **`main.py`:** The main entry point for the command-line tool, orchestrating the parsing, analysis, and generation process.

# Building and Running

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up Environment Variables:**
    Create a `.env` file by copying the `.env.example` and add your OpenAI API key and/or Dify API key:
    ```bash
    cp .env.example .env
    # Edit .env and add your OPENAI_API_KEY and/or DIFY_API_KEY
    ```

## Running the Tool

The main entry point is `src/main.py`. It takes arguments to specify the project to analyze and the output directory for the generated tests.

**Example Usage:**

To run a project defined in `config/test_generation.yaml` (e.g., `complex_c_project`):

```bash
python3 -m src.main --config complex_c_project
```

If using the Dify API, ensure the `DIFY_API_KEY` environment variable is set:

```bash
export DIFY_API_KEY="your_dify_api_key_here"
python3 -m src.main --config complex_c_project
```

*Note: The exact command-line arguments can be inspected by running `python3 -m src.main --help`.*

## Running Tests

The project uses `pytest` for its own tests.

```bash
pytest
```

# Development Conventions

*   **Coding Style:** The code follows standard Python conventions (PEP 8).
*   **Testing:** The project has a `tests` directory with unit, integration, and functional tests. New code should be accompanied by corresponding tests.
*   **Configuration:** Project-specific configurations for test generation are defined in YAML files in the `config` directory.

## `src/main.py` Method Breakdown

The `main.py` script serves as the primary entry point and orchestrator for the test generation pipeline. Here are its key components:

*   **`main()`**: The main function that parses command-line arguments (`--config`, `--simple`, `--prompt-only`, etc.) and directs the program flow based on the selected mode.

*   **`class TestGenerationConfig`**: A dedicated class responsible for loading and managing the `test_generation.yaml` configuration file. It handles merging project-specific settings with defaults.

*   **`analyze_project_functions(...)`**: This function takes a project configuration and performs the entire code analysis phase. It uses `CompilationDatabaseParser` to read the project's build commands and `FunctionAnalyzer` to traverse the source code, ultimately identifying all testable functions.

*   **`should_include_function(...)`**: A crucial filtering function that determines whether a given function should be included for test generation. It applies a series of rules based on the project configuration, such as skipping `static` functions, private methods, or functions matching specific exclusion patterns.

*   **`generate_tests_with_config(...)`**: This function orchestrates the test generation phase. It initializes the `TestGenerator` with the correct LLM provider (or the `MockLLMClient` if `--prompt-only` is used) and manages the overall generation process for the list of analyzed functions.

*   **`generate_tests_simple_mode(...)`**: Contains the logic for the `--simple` mode, providing a way to run the tool with basic command-line arguments instead of a full configuration file.

*   **`print_results(...)`**: A utility function to display a summary of the test generation results, including successful and failed generations.

*   **`generate_output_directory(...)`**: A helper function that creates a unique, timestamped output directory for each test generation run, ensuring that results from different runs are kept separate.

# Roadmap

Here are the planned enhancements for the C/C++ unit test generation tool:

1.  **Enhanced Logging System:**
    *   Implement a robust logging system that includes timestamps for all log entries.
    *   Save a copy of the log file to the corresponding run directory within `experiment/` for better traceability and debugging.

2.  **Improved Prompt Engineering for C Projects:**
    *   The current prompt templates incorrectly suggest `gmock` for pure C projects.
    *   Research and document the correct usage of `MockCpp` for mocking in C.
    *   Update the prompt generation logic to provide accurate and helpful `MockCpp` instructions for C language test generation.

3.  **Parallelization and Asynchronous Workflow:**
    *   Refactor the test generation process to handle multiple functions concurrently, improving overall performance.
    *   Modify the workflow to first generate and save all necessary prompt files in a batch, before sending any requests to the LLM.

4.  **Progress Tracking and Performance Metrics:**
    *   Implement a progress indicator to provide real-time feedback during the test generation process.
    *   Calculate and display key metrics, such as the generation rate (e.g., functions per minute) and estimated time to completion.
