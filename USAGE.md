# Usage Guide - AI Test Generation Tool

## 📋 Environment Setup

### 1. Install Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root:
```bash
# OpenAI API (optional)
OPENAI_API_KEY=your_openai_api_key_here

# DeepSeek API (recommended) - Tested and working
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Anthropic API (future support)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Project configuration
PROJECT_ROOT=./test_projects/c
COMPILE_COMMANDS=compile_commands.json

# LLM Provider Selection (optional)
LLM_PROVIDER=deepseek  # deepseek, openai, anthropic, or mock
```

Or set environment variables directly:
```bash
# Windows
set DEEPSEEK_API_KEY=your_deepseek_api_key_here
set OPENAI_API_KEY=your_openai_api_key_here

# Linux/Mac
export DEEPSEEK_API_KEY=your_deepseek_api_key_here
export OPENAI_API_KEY=your_openai_api_key_here
```

### libclang Setup (Ubuntu clang-10)
```bash
# Install clang-10 development package
sudo apt install -y libclang-10-dev clang-10

# Configure Python clang bindings
python -c "import clang.cindex; clang.cindex.Config.set_library_file('/usr/lib/llvm-10/lib/libclang.so.1')"
```

## 🚀 Available Scripts

### 1. DeepSeek Integration Demo
```bash
# Basic usage (requires DEEPSEEK_API_KEY)
python demo_deepseek_integration.py

# With environment variable
set DEEPSEEK_API_KEY=your_deepseek_api_key_here
python demo_deepseek_integration.py

# One-line execution (Linux/Mac)
DEEPSEEK_API_KEY="your_key" python demo_deepseek_integration.py
```

**Output**: Generates tests in `generated_tests_deepseek_*/` directories

### 2. General LLM Integration Demo
```bash
# Uses configured providers (OpenAI, DeepSeek, or Mock)
python demo_llm_integration.py

# Force specific provider
set LLM_PROVIDER=deepseek
python demo_llm_integration.py
```

### 3. Test Generated Tests
```bash
# Validate generated test files
python test_generated_tests.py
```

### 4. Context Extraction Test
```bash
# Test context extraction functionality
python test_context_extraction.py
```

### 5. LLM Integration Test
```bash
# Test LLM client functionality
python test_llm_integration.py
```

## 🔧 Configuration

### Supported LLM Providers

| Provider | Models | Environment Variable | Status |
|----------|--------|---------------------|---------|
| OpenAI | gpt-3.5-turbo, gpt-4, gpt-4-turbo | `OPENAI_API_KEY` | ✅ Working |
| DeepSeek | deepseek-chat, deepseek-coder | `DEEPSEEK_API_KEY` | ✅ Working |
| Anthropic | claude-3 models | `ANTHROPIC_API_KEY` | ⏳ Planned |
| Mock | mock-gpt-3.5-turbo | (none) | ✅ Working |

### Provider Configuration

The tool automatically detects available providers:
```bash
# Check provider status
python -c "from src.utils.config_loader import ConfigLoader; ConfigLoader.print_provider_status()"
```

## 🎯 Example Usage

### 1. Using DeepSeek API
```bash
# Set API key
export DEEPSEEK_API_KEY="sk-your-deepseek-key"

# Run DeepSeek demo
python demo_deepseek_integration.py

# Output: Generated tests for divide() function
# Files: generated_tests_deepseek_deepseek-chat/test_divide.cpp
#        generated_tests_deepseek_deepseek-coder/test_divide.cpp
```

### 2. Using OpenAI API
```bash
# Set API key  
export OPENAI_API_KEY="sk-your-openai-key"

# Run general demo (will use OpenAI)
python demo_llm_integration.py
```

### 3. Using Mock Mode (No API Key)
```bash
# No API keys needed - uses mock responses
python demo_llm_integration.py

# Or explicitly set mock mode
export LLM_PROVIDER=mock
python demo_llm_integration.py
```

## 📁 Project Structure

```
ai-dt/
├── src/                    # Source code
│   ├── generator/         # Test generation
│   │   ├── llm_client.py     # Multi-provider LLM client
│   │   └── test_generator.py # Test generation logic
│   ├── utils/             # Utilities
│   │   ├── config_loader.py    # LLM provider configuration
│   │   └── context_compressor.py # Token optimization
│   └── analyzer/          # Code analysis
├── test_projects/         # Sample projects
│   └── c/                # C language project
│       ├── math_utils.c     # Target source file
│       └── compile_commands.json
├── generated_tests_*/     # Generated test files
├── demo_*.py             # Demonstration scripts
└── test_*.py             # Test scripts
```

## ⚙️ Advanced Configuration

### Custom Model Selection
```python
# In your code:
from src.generator.test_generator import TestGenerator

# Use specific model
test_gen = TestGenerator(
    llm_provider="deepseek",
    api_key="your_key",
    model="deepseek-coder"  # or "deepseek-chat"
)
```

### Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API key | For DeepSeek | None |
| `OPENAI_API_KEY` | OpenAI API key | For OpenAI | None |
| `ANTHROPIC_API_KEY` | Anthropic API key | For Anthropic | None |
| `LLM_PROVIDER` | Force specific provider | No | Auto-detect |
| `PROJECT_ROOT` | Project root path | No | `./test_projects/c` |
| `COMPILE_COMMANDS` | Compilation database | No | `compile_commands.json` |

## 🐛 Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```bash
   # Error: DEEPSEEK_API_KEY not found
   # Solution: Set the environment variable
   export DEEPSEEK_API_KEY="your_key"
   ```

2. **Unicode Encoding Error (Windows)**
   ```bash
   # Error: 'gbk' codec can't encode character
   # Solution: Scripts already fixed, but ensure:
   set PYTHONIOENCODING=utf-8
   ```

3. **Model Not Found**
   ```bash
   # Error: Model Not Exist
   # Solution: Use supported models only
   # Supported: deepseek-chat, deepseek-coder
   ```

### Getting Help

Check provider status:
```bash
python -c "from src.utils.config_loader import ConfigLoader; ConfigLoader.print_provider_status()"
```

Test API connectivity:
```bash
python test_llm_integration.py
```

---

## 📝 License & Attribution

This tool uses:
- Google Test framework for C++ testing
- MockCpp for mocking
- Various LLM APIs for test generation

Ensure you comply with each provider's terms of service when using their APIs.

*Last Updated: 2025-08-23*