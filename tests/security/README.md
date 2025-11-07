# Security Testing for AI-DT

This directory contains comprehensive security tests for the AI-DT (Digital Twin) C/C++ code generation system.

## 🎯 Objective

To ensure the AI-DT system is secure against common attacks and vulnerabilities, especially when processing user-provided C/C++ code and generating test cases.

## 📁 Test Structure

```
tests/security/
├── fixtures/          # Test data and malicious code samples
├── utils/             # Security testing utilities
│   └── security_test_helpers.py
├── test_path_traversal.py          # Path traversal attack tests
├── test_command_injection.py       # Command injection tests
├── test_prompt_injection.py        # LLM prompt injection tests
├── test_memory_safety.py           # Memory vulnerability tests
├── test_edge_cases.py              # Edge cases and boundary conditions
├── run_security_tests.py           # Test runner script
├── security_config.yaml            # Security configuration
└── README.md                       # This file
```

## 🚨 Security Vulnerabilities Addressed

### 1. Path Traversal (CVE-level severity)
- **Fixed**: Direct file path usage without validation in `clang_analyzer.py`
- **Test**: `test_path_traversal.py`
- **Protection**:
  - Path canonicalization and validation
  - Restricted directory access
  - File extension whitelist
  - Size limits

### 2. Command Injection (High severity)
- **Fixed**: Subprocess calls with unsanitized input in `compile_db_generator.py`
- **Test**: `test_command_injection.py`
- **Protection**:
  - Argument sanitization
  - Safe filename validation
  - Shell escaping

### 3. Prompt Injection (High severity)
- **Fixed**: Direct template substitution without sanitization in `prompt_template_loader.py`
- **Test**: `test_prompt_injection.py`
- **Protection**:
  - Input sanitization
  - Jinja2 sandboxing
  - Template syntax escaping

### 4. CORS Misconfiguration (Medium severity)
- **Fixed**: Wildcard CORS policy in `api/server.py`
- **Test**: API endpoint tests
- **Protection**:
  - Configurable allowed origins
  - Explicit method and header whitelists

## 🛡️ Security Measures Implemented

### Input Validation
- File path validation with path traversal protection
- Filename sanitization for compilation commands
- Template input sanitization for LLM prompts
- Size limits to prevent DoS attacks

### Output Sanitization
- Escaping of dangerous characters
- Filtering of system directives
- Removal of executable code patterns

### Access Control
- Restricted file system access
- CORS configuration with specific origins
- Resource usage limits

### Error Handling
- Secure error messages (no information disclosure)
- Graceful failure handling
- Logging of security events

## 🧪 Running Security Tests

### Prerequisites
```bash
# Install security testing dependencies
pip install -r requirements-security.txt
```

### Run All Security Tests
```bash
# Run all security tests
./tests/security/run_security_tests.py

# With verbose output
./tests/security/run_security_tests.py -v

# Generate coverage report
./tests/security/run_security_tests.py --report
```

### Run Specific Test Categories
```bash
# Path traversal tests
./tests/security/run_security_tests.py --type path_traversal

# Command injection tests
./tests/security/run_security_tests.py --type command_injection

# Prompt injection tests
./tests/security/run_security_tests.py --type prompt_injection

# Memory safety tests
./tests/security/run_security_tests.py --type memory_safety
```

### Generate Security Score
```bash
# Generate overall security score
./tests/security/run_security_tests.py --score
```

### Using Pytest Directly
```bash
# Run all security tests with pytest
python -m pytest tests/security/ -m security -v

# Run with coverage
python -m pytest tests/security/ -m security --cov=src --cov-report=html
```

## 📊 Test Coverage

### Path Traversal Tests
- Basic directory traversal (`../`, `..\\`)
- URL encoded attacks (`%2e%2e%2f`)
- Double encoding attacks
- Null byte injection
- Symbolic link attacks
- Long path attacks

### Command Injection Tests
- Shell command separators (`;`, `&`, `|`)
- Command substitution (`` ` ``, `$()`)
- Pipeline and redirection attacks
- Windows-specific attacks
- Argument list manipulation

### Prompt Injection Tests
- System prompt override attempts
- Jinja2 template injection
- Code execution through templates
- DoS attacks through recursion
- Context pollution attacks

### Memory Safety Tests
- Buffer overflow detection
- Use-after-free patterns
- Double-free detection
- Memory leak identification
- Format string vulnerabilities
- Integer overflow patterns
- Race condition detection

### Edge Cases
- Empty and malformed inputs
- Unicode and encoding attacks
- Very large inputs
- Concurrent access
- Error recovery

## 🔧 Configuration

Security settings can be configured in `tests/security/security_config.yaml`:

- File size limits
- Allowed file extensions
- Restricted paths
- Dangerous patterns
- CORS settings

## 📈 Security Score

The security score is calculated based on:

1. **Implementation** (70%): Are security measures properly implemented?
2. **Testing** (20%): Are there comprehensive tests?
3. **Coverage** (10%): Is the code well covered?

**Current Score: 8/10** ⭐⭐⭐⭐

## 🚨 Incident Response

If a security test fails:

1. **Immediate Action**
   - Stop deployment to production
   - Review the failing test
   - Identify the vulnerability

2. **Investigation**
   - Check code commits that introduced the issue
   - Review system logs for exploitation attempts
   - Assess impact on production systems

3. **Remediation**
   - Fix the vulnerability
   - Add additional tests
   - Update security documentation

4. **Post-mortem**
   - Document the incident
   - Update security checklist
   - Train team on prevention

## 🤝 Contributing

When adding new features:

1. **Security Review**
   - Consider potential security implications
   - Add corresponding security tests
   - Update documentation

2. **Testing**
   - Run security tests before committing
   - Ensure all tests pass
   - Maintain security score

3. **Reporting**
   - Report security issues privately
   - Follow responsible disclosure
   - Credit researchers appropriately

## 📞 Contacts

For security concerns:
- Security Team: security@example.com
- Bug Bounty: security-bounty@example.com
- General Issues: github.com/company/ai-dt/issues

## 🔄 Continuous Integration

Add to CI/CD pipeline:

```yaml
security_tests:
  stage: security
  script:
    - pip install -r requirements-security.txt
    - ./tests/security/run_security_tests.py --score
  artifacts:
    reports:
      junit: security-test-results-*.xml
    paths:
      - htmlcov-security/
  only:
    - merge_requests
    - main
```

## 📝 License

Security tests are licensed under the same terms as the AI-DT project.

---

**Remember**: Security is an ongoing process, not a one-time fix. Regular testing and vigilance are key to maintaining a secure system.