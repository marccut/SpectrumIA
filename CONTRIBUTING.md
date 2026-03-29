# 🤝 Contributing to SpectrumIA

Thank you for your interest in contributing to SpectrumIA! This document provides guidelines for contributing code, tests, and documentation.

---

## 📋 Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and adhere to our Code of Conduct:

- Be respectful and inclusive
- Welcome diverse perspectives
- Focus on constructive feedback
- Report issues through appropriate channels

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Git
- pip

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/[owner]/spectrumia.git
cd spectrumia

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install-dev

# Setup pre-commit hooks
make setup-pre-commit

# Run tests to verify setup
make test-fast
```

---

## 📝 Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b fix/bug-description
```

Use descriptive branch names:
- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation updates
- `test/` for test additions
- `refactor/` for code refactoring

### 2. Make Your Changes

```bash
# Edit files, add new code, etc.

# Run pre-commit hooks to check code quality
make pre-commit-check

# Or let git hooks run automatically on commit
git add .
git commit -m "feat: add new feature"  # Conventional commit format
```

### 3. Run Tests Locally

```bash
# Run all tests
make test

# Or specific tests
make test-specific TEST=tests/test_schemas.py

# With coverage
make test-coverage
```

### 4. Fix Issues

```bash
# Auto-fix formatting and lint issues
make quality-fix

# Type check
make type-check

# Security check
make security-check

# Run full quality checks
make quality-check
```

### 5. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# GitHub will suggest creating a PR
# Fill in the PR template with:
# - Description of changes
# - Related issue (if applicable)
# - Testing approach
# - Checklist verification
```

### 6. Review Process

- Maintainers will review your PR
- GitHub Actions runs automated tests
- Address review comments
- Once approved, maintainer will merge

---

## 🧪 Testing Guidelines

### Test Structure

```python
# tests/test_module.py
import pytest
from module import function

class TestFunction:
    """Test function behavior."""

    def test_success_case(self):
        """Test successful execution."""
        assert function(args) == expected

    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(Exception):
            function(invalid_args)
```

### Test Naming

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Descriptive names: `test_function_returns_correct_value`

### Coverage Requirements

- New code must have test coverage
- Minimum 70% overall coverage
- Core modules (core/, models/) aim for 85%+

### Running Tests

```bash
# All tests
make test

# Specific file
make test-specific TEST=tests/test_schemas.py

# With markers
make test-markers MARKER=unit

# With coverage
make test-coverage

# Fast mode (no verbose)
make test-fast
```

---

## 💻 Code Style

### Format: Black

```bash
# Format code
make format

# Check formatting
make format-check
```

**Rules**:
- Line length: 100 characters
- Use single quotes for strings
- 4 spaces for indentation

### Lint: Ruff

```bash
# Check linting
make lint

# Auto-fix lint issues
make lint-fix
```

**Rules**:
- Follow PEP 8
- No unused imports
- Meaningful variable names
- Docstrings for public functions

### Type Hints: Mypy

```bash
# Type check
make type-check
```

**Rules**:
- Add type hints to function parameters and returns
- Use `Optional[Type]` for nullable values
- Import from `typing` module

### Example: Properly Formatted Function

```python
"""Module docstring."""

from typing import Optional
from pydantic import BaseModel

def calculate_score(
    values: list[float],
    weights: Optional[list[float]] = None,
) -> float:
    """Calculate weighted score from values.

    Args:
        values: List of numeric values
        weights: Optional weights for values

    Returns:
        Weighted score as float

    Raises:
        ValueError: If values is empty
    """
    if not values:
        raise ValueError("Values list cannot be empty")

    if weights is None:
        weights = [1.0] * len(values)

    return sum(v * w for v, w in zip(values, weights)) / sum(weights)
```

---

## 📚 Documentation

### Docstrings

```python
def function(param1: str, param2: int) -> bool:
    """Brief description.

    Longer description explaining what the function does,
    including any important details about behavior.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When inputs are invalid

    Examples:
        >>> function("test", 42)
        True
    """
    pass
```

### README Updates

If your changes affect usage:
1. Update relevant section in `README.md`
2. Add examples if applicable
3. Keep documentation consistent with code

### Code Comments

```python
# Use comments sparingly - code should be self-documenting

# GOOD: Explain WHY, not WHAT
# Use a list for O(1) lookup time instead of iterating
items_set = set(items)

# BAD: Explains WHAT (obvious from code)
# Add item to set
items_set.add(item)
```

---

## 🔀 Git Conventions

### Commit Messages

Follow Conventional Commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation update
- `style`: Formatting, no code changes
- `refactor`: Code refactoring
- `test`: Test addition/modification
- `chore`: Build, dependencies, etc.

**Examples**:
```
feat(schemas): add UserResponse model

fix(database): handle null values in queries

docs: update installation instructions

test: add coverage for edge cases
```

### Branching

```bash
# Always create a feature branch
git checkout -b feature/description

# Never commit directly to main
# Never rewrite public history
# Keep commits atomic and logical
```

---

## 🔍 Code Review Checklist

Before submitting a PR, ensure:

- ✅ Code follows style guide (run `make quality-check`)
- ✅ Tests pass locally (`make test`)
- ✅ New tests added for new functionality
- ✅ Coverage maintained or improved
- ✅ Documentation updated if needed
- ✅ Commit messages follow conventions
- ✅ No secrets or credentials in code
- ✅ No breaking changes without discussion

---

## 📊 PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Code refactoring

## Related Issue
Closes #123

## Changes
- Change 1
- Change 2
- Change 3

## Testing
Describe testing approach:
- [ ] Unit tests added
- [ ] Manual testing done
- [ ] Coverage verified

## Checklist
- [ ] Code follows style guide
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No breaking changes
```

---

## 🐛 Bug Reports

When reporting bugs:

1. **Title**: Clear, concise description
2. **Steps to Reproduce**: Exact steps to trigger bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: Python version, OS, etc.
6. **Logs**: Error messages, stack traces
7. **Minimal Example**: Smallest code to reproduce

---

## 💡 Feature Requests

When proposing features:

1. **Title**: Clear, one-sentence summary
2. **Motivation**: Why this feature is needed
3. **Proposed Solution**: How you envision it working
4. **Alternatives**: Other approaches considered
5. **Impact**: How it affects existing code
6. **Examples**: Usage examples if applicable

---

## 🚫 What NOT to Do

- Don't commit directly to `main`
- Don't disable tests or checks
- Don't add dependencies without discussion
- Don't include credentials or secrets
- Don't make unrelated changes in one PR
- Don't force push to shared branches
- Don't ignore review feedback

---

## 🎓 Development Tips

### Useful Make Commands

```bash
# Quick development cycle
make workflow  # clean, format, lint, test

# Debug specific test
make test-specific TEST=tests/test_file.py

# Check everything before pushing
make quality-check && make test

# Profile your code
python -m cProfile -s cumulative script.py
```

### IDE Setup

**VS Code**:
```json
{
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "[python]": {
        "editor.formatOnSave": true
    }
}
```

**PyCharm**:
- Enable Black integration
- Set code style to match project
- Enable type hint inspection

---

## 📞 Questions?

- **Issues**: Create GitHub issue with detailed info
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check README.md and guides first

---

## 🙏 Thank You!

Your contributions help make SpectrumIA better. We appreciate your effort!

---

**Last Updated**: 2026-03-27
