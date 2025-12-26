# Contributing to Data Quality Framework

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 🤝 Ways to Contribute

- Report bugs
- Suggest enhancements
- Write documentation
- Submit code improvements
- Create new validators
- Improve test coverage
- Share examples
- Help with infrastructure

## 🐛 Reporting Bugs

Before reporting a bug, please:

1. Check existing issues
2. Ensure you have the latest version
3. Test with minimal reproduction code

When reporting, include:

```markdown
**Environment**
- Python version: 3.9 / 3.10 / 3.11
- OS: Linux / macOS / Windows
- Framework version: 0.2.0

**Description**
Clear description of the issue

**Steps to Reproduce**
1. ...
2. ...

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Minimal Code Example**
```python
# Your code here
```
```

## 💡 Suggesting Enhancements

Create an issue with:

```markdown
**Current Behavior**
What currently happens

**Desired Behavior**
What you'd like to happen

**Reasoning**
Why this would be useful

**Possible Implementation**
Your idea for how to implement it
```

## 📋 Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/data-quality-framework.git
cd data-quality-framework
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Development Dependencies

```bash
pip install -e ".[dev,api,cli,database]"
```

### 4. Set Up Pre-commit Hooks

```bash
pre-commit install
```

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test

```bash
pytest tests/test_validators.py::TestNullCheckValidator -v
```

### Generate Coverage Report

```bash
pytest tests/ --cov=src/data_quality_framework --cov-report=html
open htmlcov/index.html
```

### Coverage Targets

- Minimum: 80%
- Target: 95%+
- Exclude: examples, __main__

## 📝 Code Style

### Format Code with Black

```bash
black src/ tests/
```

### Sort Imports with isort

```bash
isort src/ tests/
```

### Check Types with mypy

```bash
mypy src/
```

### Lint with flake8

```bash
flake8 src/ tests/
```

### Run All Quality Checks

```bash
make lint
```

## 📦 Making Changes

### Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### Branch Naming

- Feature: `feature/short-description`
- Bugfix: `fix/short-description`
- Docs: `docs/short-description`
- Tests: `test/short-description`

### Writing Code

**Follow these principles:**

1. **Single Responsibility** - One class/function = one purpose
2. **DRY** - Don't repeat yourself
3. **KISS** - Keep it simple
4. **Readability** - Clear naming and comments
5. **Type Hints** - Add type annotations
6. **Docstrings** - Document public functions

**Example:**

```python
def validate_column_range(
    data: pd.DataFrame,
    column: str,
    min_value: float,
    max_value: float
) -> Dict[str, List[str]]:
    """
    Validate that column values are within a range.
    
    Args:
        data: Input DataFrame
        column: Column name to validate
        min_value: Minimum acceptable value
        max_value: Maximum acceptable value
    
    Returns:
        Dictionary with validation errors, empty if valid
    
    Raises:
        ValueError: If column doesn't exist
    """
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found")
    
    errors = {}
    invalid_rows = data[
        (data[column] < min_value) | (data[column] > max_value)
    ].index.tolist()
    
    if invalid_rows:
        errors[column] = [
            f"Values outside range [{min_value}, {max_value}]"
        ]
    
    return errors
```

### Writing Tests

**Test Structure:**

```python
import pytest
import pandas as pd
from data_quality_framework.validators import YourValidator

class TestYourValidator:
    """Tests for YourValidator"""
    
    def test_valid_case(self):
        """Test with valid data"""
        data = pd.DataFrame({...})
        validator = YourValidator(...)
        result = validator.validate(data)
        assert result.passed
    
    def test_invalid_case(self):
        """Test with invalid data"""
        data = pd.DataFrame({...})
        validator = YourValidator(...)
        result = validator.validate(data)
        assert not result.passed
        assert "error message" in result.errors
    
    def test_edge_case(self):
        """Test edge cases"""
        ...
```

**Test Coverage:**

- Aim for 95%+ coverage
- Test both success and failure cases
- Include edge cases
- Test error messages
- Parameterize similar tests

### Writing Documentation

**Docstring Format (Google style):**

```python
def my_function(arg1: str, arg2: int) -> bool:
    """
    Short description of function.
    
    Longer description if needed. Explain what it does,
    why it exists, and when to use it.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When something is wrong
        TypeError: When type is incorrect
    
    Example:
        >>> result = my_function("test", 123)
        >>> print(result)
        True
    """
```

### Commit Messages

Follow conventional commits:

```
type(scope): short description

Longer explanation if needed.

Fixes #123
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `perf:` Performance improvement
- `ci:` CI/CD changes

**Example:**

```
feat(validators): add custom validator base class

Implement a flexible base class that allows users to create
custom validators by extending CustomValidator and implementing
the validate() method.

This enables non-technical users to add domain-specific validation
rules without modifying the core framework.

Fixes #42
```

## 🔄 Pull Request Process

### Before Submitting

1. Update your branch: `git pull origin main`
2. Run all tests: `pytest tests/ -v`
3. Check coverage: `pytest tests/ --cov`
4. Format code: `black src/ tests/`
5. Sort imports: `isort src/ tests/`
6. Lint code: `flake8 src/ tests/`
7. Type check: `mypy src/`

### Create Pull Request

**Title:** Follow conventional commits

**Description:**

```markdown
## Description
What does this PR do?

## Related Issues
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Coverage maintained (95%+)
- [ ] Documentation updated
- [ ] Code formatted with black
- [ ] No new warnings
```

### PR Review

We'll review your PR and may request changes. Don't worry—all feedback is constructive!

## 📚 Adding a New Validator

### 1. Create Validator Class

```python
# src/data_quality_framework/validators.py

class CustomRuleValidator(BaseValidator):
    """Validator for custom business rules"""
    
    def __init__(self, columns: List[str], rule_function: Callable):
        super().__init__()
        self.columns = columns
        self.rule_function = rule_function
    
    def validate(self, data: pd.DataFrame) -> ValidationResult:
        """Apply custom rule to data"""
        errors = {}
        
        try:
            for column in self.columns:
                if column not in data.columns:
                    errors[column] = [f"Column not found"]
                    continue
                
                invalid_rows = ~data[column].apply(self.rule_function)
                
                if invalid_rows.any():
                    errors[column] = [
                        f"Rule failed for {invalid_rows.sum()} rows"
                    ]
        
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            errors["error"] = [str(e)]
        
        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            validator_name=self.name
        )
```

### 2. Write Tests

```python
# tests/test_validators.py

class TestCustomRuleValidator:
    def test_valid_rule(self):
        data = pd.DataFrame({'age': [20, 30, 40]})
        validator = CustomRuleValidator(
            columns=['age'],
            rule_function=lambda x: x >= 18
        )
        result = validator.validate(data)
        assert result.passed
    
    def test_invalid_rule(self):
        data = pd.DataFrame({'age': [10, 20, 30]})
        validator = CustomRuleValidator(
            columns=['age'],
            rule_function=lambda x: x >= 18
        )
        result = validator.validate(data)
        assert not result.passed
```

### 3. Update __init__.py

```python
# src/data_quality_framework/__init__.py

from .validators import CustomRuleValidator

__all__ = [
    "CustomRuleValidator",
    # ... other validators
]
```

### 4. Document in README

Add example in [README.md](README.md) showing how to use your validator.

## 🐳 Docker & Terraform Changes

### Update Dockerfile

```dockerfile
# Add new dependencies here
RUN pip install new-package>=1.0.0
```

### Update docker-compose.yml

```yaml
services:
  new-service:
    image: new-service:latest
    # ...
```

### Update Terraform

```hcl
# terraform/variables.tf
variable "new_setting" {
  description = "..."
  type        = string
}

# terraform/main.tf
resource "aws_resource" "new" {
  # Configuration
}
```

## 📊 Performance Guidelines

- API response time < 500ms
- Validation < 100ms per 1000 rows
- Database queries < 50ms
- Memory usage < 500MB for typical datasets

Profile with:

```bash
pytest tests/ --profile
```

## 🔐 Security Guidelines

- No hardcoded credentials
- Use environment variables
- Validate all inputs
- Sanitize database queries
- Regular dependency updates

Check with:

```bash
pip audit
```

## 📞 Getting Help

- **Questions:** Open a Discussion
- **Issues:** Search existing issues first
- **Documentation:** Check [docs/](docs/) folder
- **Examples:** See [examples/](examples/) folder

## ✅ Checklist Before Final PR

- [ ] Tests pass: `pytest tests/ -v`
- [ ] Coverage >= 95%: `pytest tests/ --cov`
- [ ] Code formatted: `black src/ tests/`
- [ ] Imports sorted: `isort src/ tests/`
- [ ] Linted: `flake8 src/ tests/`
- [ ] Type checked: `mypy src/`
- [ ] Docstrings added
- [ ] Examples provided
- [ ] Documentation updated
- [ ] No security issues: `pip audit`
- [ ] Commit messages follow conventional style
- [ ] PR description is clear and complete

---

**Thank you for contributing!** 🎉

Your help makes Data Quality Framework better for everyone.

---

Questions? Open an issue or start a discussion!
