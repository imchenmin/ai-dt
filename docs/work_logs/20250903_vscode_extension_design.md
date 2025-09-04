# VS Code Extension Design Work Log

## Date: 2025-09-03
## Author: Claude Code

## Overview
This document outlines the design thinking process for creating a VS Code extension that provides online function test generation capabilities based on the existing AI-DT codebase.

## Current Architecture Analysis

### Core Components Identified:
1. **TestGenerationService** (`src/test_generation/service.py`): Main orchestrator
2. **LLMClient** (`src/llm/client.py`): Unified interface for AI model interactions
3. **FunctionAnalyzer**: Parses C/C++ code and extracts testable functions
4. **CompilationDatabaseParser**: Handles compile_commands.json parsing
5. **Configuration System**: YAML-based project and LLM configuration

### Key Integration Points:
- **Project Analysis**: Function extraction from compilation databases
- **LLM Integration**: Support for multiple providers (OpenAI, DeepSeek, Dify)
- **Test Generation**: Google Test + MockCpp template generation
- **Configuration Management**: Project-specific settings and LLM credentials

## VS Code Extension Requirements Design

### Primary User Stories:
1. **As a developer**, I want to generate unit tests for a specific function by right-clicking on it in the editor
2. **As a developer**, I want to generate tests for all functions in a file with a single command
3. **As a developer**, I want to configure LLM providers and API keys within VS Code
4. **As a developer**, I want to see generation progress and results in a dedicated panel
5. **As a developer**, I want to customize test generation templates and patterns

### Core Features:

#### 1. Context Menu Integration
- **Right-click on function**: Generate test for specific function
- **Right-click on file**: Generate tests for all functions in file
- **Right-click on folder**: Generate tests for entire project/module

#### 2. Configuration Management
- **LLM Provider Settings**: GUI for configuring API keys and models
- **Project Configuration**: Visual editor for test generation settings
- **Template Customization**: UI for modifying test templates

#### 3. Real-time Feedback
- **Progress Panel**: Show generation progress and status
- **Results Viewer**: Display generated tests with syntax highlighting
- **Error Reporting**: Clear error messages and troubleshooting guidance

#### 4. Integration with VS Code Features
- **Problems Panel**: Show generation errors and warnings
- **Output Channel**: Dedicated output for test generation logs
- **Quick Pick**: Function selection interface

### Technical Architecture:

#### Extension Structure:
```
extension/
├── src/
│   ├── extension.ts          # Main extension entry point
│   ├── testGenerator.ts      # Core test generation logic
│   ├── configManager.ts      # Configuration management
│   ├── ui/
│   │   ├── progressPanel.ts  # Progress display
│   │   ├── resultsViewer.ts  # Test results display
│   │   └── configPanel.ts    # Configuration UI
│   └── utils/
│       ├── pythonRunner.ts   # Python process management
│       └── fileUtils.ts      # File system operations
├── package.json              # Extension manifest
├── tsconfig.json            # TypeScript configuration
└── resources/
    └── templates/           # Default test templates
```

#### Integration Approach:
1. **Python Backend**: Reuse existing AI-DT Python codebase
2. **Node.js Frontend**: VS Code extension written in TypeScript
3. **Inter-process Communication**: Use child processes or REST API
4. **Configuration Sync**: Share configuration between Python and TypeScript

### API Design:

#### Python Service API (REST):
```typescript
interface TestGenerationAPI {
  // Project analysis
  analyzeProject(projectPath: string, config?: ProjectConfig): Promise<ProjectAnalysis>;
  analyzeFile(filePath: string, projectConfig?: ProjectConfig): Promise<FileAnalysis>;
  
  // Test generation
  generateFunctionTest(functionName: string, context: GenerationContext): Promise<TestResult>;
  generateFileTests(filePath: string, config?: GenerationConfig): Promise<TestResults>;
  
  // Configuration
  getConfiguration(): Promise<ExtensionConfig>;
  updateConfiguration(config: Partial<ExtensionConfig>): Promise<void>;
}
```

#### Extension Commands:
```json
{
  "commands": [
    {
      "command": "ai-dt.generateFunctionTest",
      "title": "Generate Unit Test for Function",
      "category": "AI-DT"
    },
    {
      "command": "ai-dt.generateFileTests", 
      "title": "Generate Tests for Current File",
      "category": "AI-DT"
    },
    {
      "command": "ai-dt.configureExtension",
      "title": "Configure AI-DT Extension",
      "category": "AI-DT"
    }
  ]
}
```

### Configuration Management:

#### Extension Settings:
```json
{
  "ai-dt.llmProvider": "deepseek",
  "ai-dt.apiKey": "",
  "ai-dt.model": "deepseek-coder",
  "ai-dt.maxWorkers": 3,
  "ai-dt.outputDirectory": "./generated_tests",
  "ai-dt.autoSaveTests": true,
  "ai-dt.testTemplate": "google_test_mockcpp"
}
```

### User Interface Components:

#### 1. Progress Panel:
- Real-time generation status
- Function-by-function progress
- Error and warning indicators
- Generation statistics

#### 2. Results Viewer:
- Syntax-highlighted test code
- Side-by-side comparison with original function
- Quick navigation to generated files
- One-click test execution

#### 3. Configuration Panel:
- LLM provider selection
- API key management  
- Project-specific settings
- Template customization

### Security Considerations:
- **API Key Storage**: Use VS Code's secret storage
- **Network Security**: Secure communication with LLM providers
- **Code Safety**: Validate generated tests before execution
- **Privacy**: Local processing where possible

### Performance Considerations:
- **Caching**: Cache project analysis results
- **Incremental Generation**: Only regenerate changed functions
- **Background Processing**: Non-blocking UI during generation
- **Resource Management**: Configurable worker limits

### Testing Strategy:
- **Unit Tests**: Test individual components
- **Integration Tests**: Test Python-Node.js communication
- **UI Tests**: Test extension user interface
- **End-to-End Tests**: Complete workflow testing

### Deployment Considerations:
- **Python Dependency**: Bundle Python runtime or require installation
- **Cross-platform**: Support Windows, macOS, and Linux
- **Version Compatibility**: Support multiple VS Code versions
- **Update Strategy**: Seamless updates through VS Code marketplace

## Next Steps:
1. Create detailed technical specification
2. Set up extension development environment
3. Implement core Python service API
4. Develop VS Code extension skeleton
5. Implement configuration management
6. Add context menu integration
7. Develop UI components
8. Test and refine the extension

## Dependencies:
- VS Code Extension API
- TypeScript 4.0+
- Node.js 16+
- Python 3.8+ with AI-DT dependencies
- Various VS Code UI libraries

This design provides a comprehensive foundation for developing a VS Code extension that brings the power of AI-driven test generation directly into the development environment.