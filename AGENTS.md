# Repository Guidelines

## Project Structure & Module Organization
Core logic sits in `src/`: `analyzer/` reads project metadata, `generator/` and `services/` drive LLM-powered test creation, `llm/` wraps providers, and `utils/` manages configuration/logging. Use `src/main.py` for the CLI and `src/mcp_server.py` when hosting an MCP endpoint. Configurations live in `config/` (`test_generation.yaml` for projects, `mcp_config.yaml` for adapters). Reference material is in `docs/`. Automated tests are segmented across `tests/unit`, `tests/integration`, and `tests/functional`; reusable fixtures and golden assets stay in `test_projects/` and `test_output/`. Helper scripts reside in `scripts/`, and packaging aids are in `create_package.sh` and `ai-dt-*/`.

## Build, Test, and Development Commands
Set up a virtual env: `python3 -m venv .venv && source .venv/bin/activate`. Install dependencies with `pip install -r requirements.txt`, then confirm prerequisites via `python scripts/check_env.py`. List configured projects using `python -m src.main --list-projects`, and run generation with `python -m src.main --config <project> --profile <profile>` or `--simple` flags for ad hoc runs. Demo provider integrations as needed (`python scripts/demo_llm_integration.py`). Execute the full suite with `pytest`; target specific layers with `pytest tests/unit -q` or `pytest tests/integration`.

## Coding Style & Naming Conventions
Follow the prevailing Python style: 4-space indentation, type hints, concise docstrings, and `snake_case` for functions and modules. Reserve `PascalCase` for classes and `UPPER_SNAKE_CASE` for constants. Route logging through `src/utils/logging_utils.get_logger`. Configuration keys stay lowercase with underscores and must be mirrored in accompanying documentation.

## Testing Guidelines
Add new coverage where behavior changes: unit logic in `tests/unit`, cross-component flows in `tests/integration`, and end-to-end checks in `tests/functional`. Name files `test_<feature>.py` and keep assertions deterministic. Use `pytest.mark.asyncio` for asynchronous code and share fixtures through `tests/conftest.py`. When generation output is non-deterministic, assert on structured fields rather than verbatim prompts.

## Commit & Pull Request Guidelines
Commits use Conventional Commit prefixes (`feat:`, `fix:`, `chore:`) and focus on a single concern. Each pull request should explain motivation, highlight modified configs or docs, and include `pytest` results. Link issues, capture manual validation steps when relevant, and request reviewers for architecture or prompt-template changes.

## Configuration & Security
Keep secrets out of version control: load credentials via `.env` and reference them from `config/mcp_config.yaml`. Document new project stanzas in `config/test_generation.yaml` and avoid committing `compile_commands.json`. Re-run `python scripts/check_env.py` whenever you add provider settings.

## Reply Rules
- Always reply in Chinese