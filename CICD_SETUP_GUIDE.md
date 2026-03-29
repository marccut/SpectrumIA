# 🚀 Phase 7: CI/CD & Automation Setup Guide

**Status**: ✅ COMPLETE
**Date**: 2026-03-27

---

## 📋 Overview

This guide covers the complete CI/CD and automation setup for SpectrumIA, including:

1. **GitHub Actions Workflows** - Automated testing and code quality checks
2. **Pre-commit Hooks** - Local code quality enforcement
3. **Project Configuration** - pytest, black, ruff, mypy setup
4. **Development Makefile** - Convenient command shortcuts

---

## 🔧 Files Created

### CI/CD Configuration
- ✅ `.github/workflows/pytest.yml` - Test execution workflow
- ✅ `.github/workflows/coverage.yml` - Coverage reporting workflow
- ✅ `.pre-commit-config.yaml` - Pre-commit hooks configuration
- ✅ `pyproject.toml` - Tool configuration (pytest, black, ruff, mypy)
- ✅ `Makefile` - Development command shortcuts

---

## 🎯 GitHub Actions Workflows

### 1. pytest.yml - Test Execution Workflow

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs**:

#### Tests Job
- **Matrix**: Python 3.10, 3.11, 3.12
- **Actions**:
  - Checkout code
  - Set up Python environment
  - Install dependencies
  - Run pytest with HTML report
  - Upload test results artifacts
  - Publish test results

#### Code Quality Job
- **Checks**:
  - Black code formatting
  - Ruff linting
  - Mypy type checking
  - Bandit security checks

#### Summary Job
- Aggregates results from all jobs
- Reports overall status

### 2. coverage.yml - Coverage Reporting Workflow

**Triggers**:
- Push to `main` or `develop`
- Pull requests

**Jobs**:

#### Coverage Job
- Generates pytest coverage report
- Uploads to Codecov
- Enforces minimum coverage threshold (70%)
- Comments on PRs with coverage details

#### Coverage Badge Job
- Generates coverage badge
- Updates on successful push to `main`

**Configuration**:
- Threshold: 70% minimum
- Modules: core, models, app
- Report formats: XML, HTML, Terminal

---

## 🔒 Pre-commit Hooks

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
make setup-pre-commit

# Or manually:
pre-commit install
pre-commit install --hook-type commit-msg
```

### Hooks Included

1. **Black** - Code formatting
   - Line length: 100 characters
   - Target Python: 3.10+

2. **Ruff** - Fast Python linter
   - Check mode: E, W, F, I, C, B, D, UP
   - Auto-fix enabled

3. **Mypy** - Static type checking
   - Strict mode enabled for selected modules
   - Ignores third-party imports

4. **Bandit** - Security checks
   - Runs on core/, models/, app/
   - Confidence level: LOW

5. **Standard Hooks**
   - Trailing whitespace cleanup
   - End of file fixer
   - YAML validation
   - JSON validation
   - Large file detection (1MB limit)
   - Merge conflict detection
   - Private key detection

6. **Commit Message Linting**
   - Enforces conventional commits
   - Validates message format

### Running Pre-commit Manually

```bash
# Check all files
make pre-commit-check

# Or directly:
pre-commit run --all-files

# Auto-fix issues
pre-commit run --all-files --fix
```

---

## ⚙️ Project Configuration (pyproject.toml)

### Tool Configurations

#### Black
```toml
[tool.black]
line-length = 100
target-version = ["py310"]
```

#### Ruff
```toml
[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "W", "F", "I", "C", "B", "D", "UP"]
```

#### Mypy
```toml
[tool.mypy]
python_version = "3.10"
strict_optional = true
check_untyped_defs = true
```

#### Pytest
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-v", "--tb=short"]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "performance: Performance tests",
]
```

#### Coverage
```toml
[tool.coverage.run]
source = ["core", "models", "app"]

[tool.coverage.report]
exclude_lines = [...]
precision = 2
```

---

## 📊 Makefile Commands

### Installation

```bash
# Install production dependencies
make install

# Install development dependencies
make install-dev

# Setup pre-commit hooks
make setup-pre-commit
```

### Testing

```bash
# Run all tests
make test

# Run tests (fast mode)
make test-fast

# Run with coverage report
make test-coverage

# Run specific test file
make test-specific TEST=tests/test_schemas.py

# Run tests by marker
make test-markers MARKER=performance
```

### Code Quality

```bash
# Check code formatting
make format-check

# Format code
make format

# Lint code
make lint

# Fix lint issues
make lint-fix

# Type check
make type-check

# Security check
make security-check

# Run all quality checks
make quality-check

# Fix all code issues
make quality-fix

# Run pre-commit manually
make pre-commit-check
```

### Development

```bash
# Run Streamlit app
make run

# Run app in debug mode
make run-dev

# Generate documentation
make docs

# Show project status
make status

# Complete development workflow
make workflow
```

### Cleanup

```bash
# Clean all generated files
make clean

# Clean cache only
make clean-cache

# Clean test artifacts only
make clean-test
```

---

## 📈 Workflow Scenarios

### Scenario 1: Local Development with Pre-commit

```bash
# 1. Setup environment
make install-dev
make setup-pre-commit

# 2. Make code changes

# 3. Pre-commit hooks run automatically on git commit
# If issues found, fix them automatically or manually

# 4. If hooks pass, commit is created

# 5. Run tests before pushing
make test
```

### Scenario 2: Pull Request Workflow

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes and commit
# Pre-commit hooks run automatically

# 3. Push branch
git push origin feature/new-feature

# 4. GitHub Actions automatically:
#    - Run tests on Python 3.10, 3.11, 3.12
#    - Check code formatting
#    - Run linters and type checks
#    - Generate coverage report
#    - Comment on PR with results

# 5. If all checks pass, approve and merge
```

### Scenario 3: Continuous Integration

```bash
# On push to main/develop:
# 1. Tests run on multiple Python versions
# 2. Coverage report generated
# 3. Coverage threshold checked (70% minimum)
# 4. Results uploaded to Codecov
# 5. Badge updated
# 6. Artifacts saved for 30 days
```

---

## 🔍 Monitoring & Reporting

### GitHub Actions Dashboard
- View at: `https://github.com/[owner]/spectrumia/actions`
- Shows all workflow runs
- Displays success/failure status
- Links to artifacts and logs

### Coverage Reports
- **Codecov**: `https://codecov.io/gh/[owner]/spectrumia`
- **Local**: `htmlcov/index.html` (after running `make test-coverage`)
- **GitHub**: Coverage artifacts stored for 30 days

### Test Reports
- HTML reports uploaded to GitHub Actions
- JUnit XML format for CI integration
- Test results published on PR

---

## 🚨 Troubleshooting

### Pre-commit Hook Failures

**Black formatting issues:**
```bash
# Auto-fix with make
make format

# Or manually
black core/ models/ app/ tests/
```

**Ruff linting issues:**
```bash
# Auto-fix
make lint-fix

# Or manually
ruff check --fix core/ models/ app/ tests/
```

**Mypy type errors:**
```bash
# Run type check
make type-check

# Review errors and add type hints
```

**Commit message issues:**
```bash
# Use conventional commit format
# feat: add new feature
# fix: bug fix
# docs: documentation update
# test: test addition/modification
```

### GitHub Actions Failures

**Tests failing:**
1. Check test logs in GitHub Actions
2. Run `make test-coverage` locally to reproduce
3. Fix issues and push

**Coverage below threshold:**
1. Review coverage report
2. Add tests for uncovered code
3. Run `make test-coverage` locally

**Code quality checks failing:**
1. Run `make quality-fix` locally
2. Commit fixes
3. Push again

---

## 📚 Additional Resources

### Documentation Files
- `TESTING_PHASE6_SUMMARY.md` - Test suite overview
- `PHASE6_COMPLETION.md` - Phase 6 completion report
- `README.md` - Project overview

### Configuration Files
- `requirements.txt` - Dependencies
- `.gitignore` - Git ignore patterns
- `.env.example` - Environment variables template

### GitHub
- Actions: `.github/workflows/`
- Pre-commit: `.pre-commit-config.yaml`
- Project config: `pyproject.toml`

---

## ✅ Implementation Checklist

- ✅ GitHub Actions workflows created (pytest.yml, coverage.yml)
- ✅ Pre-commit hooks configured (.pre-commit-config.yaml)
- ✅ Project configuration (pyproject.toml)
- ✅ Makefile with 30+ commands
- ✅ Documentation (this guide)
- ✅ All files syntax validated

---

## 🎯 Next Steps

1. **Push to GitHub**:
   ```bash
   git add .github/ pyproject.toml .pre-commit-config.yaml Makefile
   git commit -m "feat: add CI/CD automation setup"
   git push origin develop
   ```

2. **Setup locally**:
   ```bash
   make install-dev
   make setup-pre-commit
   make quality-check  # Verify everything works
   ```

3. **Create PR**: Push to feature branch and create PR to see workflows in action

4. **Monitor**: Check GitHub Actions dashboard for workflow runs

---

## 📞 Support

For issues with CI/CD setup:
1. Check GitHub Actions logs: Actions → Workflow → Job → Step
2. Run `make status` to see local configuration
3. Run `make pre-commit-check` to test hooks locally
4. Review error messages and fix issues
5. Commit and push changes

---

**Phase 7: CI/CD & Automation - COMPLETE** ✅

All workflows configured and ready for continuous integration!

**Project Progress**: 6 of 8 phases complete (75%)
**Next**: Phase 8 - Production Deployment

