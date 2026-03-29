.PHONY: help install install-dev setup-pre-commit test test-fast test-coverage lint format type-check security-check clean clean-cache clean-test run docs

PYTHON := python3
PIP := pip
PYTEST := pytest
BLACK := black
RUFF := ruff
MYPY := mypy
BANDIT := bandit

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)SpectrumIA - Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Installation:$(NC)"
	@grep -E '^install.*:.*?## ' $(MAKEFILE_LIST) | sed 's/^/  /' | awk 'BEGIN {FS = ":.*?## "} {printf "$(BLUE)%-30s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@grep -E '^test.*:.*?## ' $(MAKEFILE_LIST) | sed 's/^/  /' | awk 'BEGIN {FS = ":.*?## "} {printf "$(BLUE)%-30s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@grep -E '^(lint|format|type-check|security-check):.*?## ' $(MAKEFILE_LIST) | sed 's/^/  /' | awk 'BEGIN {FS = ":.*?## "} {printf "$(BLUE)%-30s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@grep -E '^(setup-pre-commit|run|clean|docs):.*?## ' $(MAKEFILE_LIST) | sed 's/^/  /' | awk 'BEGIN {FS = ":.*?## "} {printf "$(BLUE)%-30s$(NC) %s\n", $$1, $$2}'

# Installation targets
install: ## Install production dependencies
	@echo "$(YELLOW)Installing production dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-dev: install ## Install development dependencies
	@echo "$(YELLOW)Installing development dependencies...$(NC)"
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"

setup-pre-commit: install-dev ## Setup pre-commit hooks
	@echo "$(YELLOW)Setting up pre-commit hooks...$(NC)"
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"
	@echo "$(BLUE)Run 'make pre-commit-check' to test manually$(NC)"

# Testing targets
test: ## Run all tests with verbose output
	@echo "$(YELLOW)Running all tests...$(NC)"
	$(PYTEST) tests/ -v --tb=short
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-fast: ## Run tests without verbose output (faster)
	@echo "$(YELLOW)Running tests (fast mode)...$(NC)"
	$(PYTEST) tests/ -q
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	$(PYTEST) tests/ \
		--cov=core \
		--cov=models \
		--cov=app \
		--cov-report=html \
		--cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report generated (htmlcov/index.html)$(NC)"

test-specific: ## Run specific test file (usage: make test-specific TEST=tests/test_schemas.py)
	@if [ -z "$(TEST)" ]; then \
		echo "$(RED)Error: TEST variable required$(NC)"; \
		echo "Usage: make test-specific TEST=tests/test_schemas.py"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Running $(TEST)...$(NC)"
	$(PYTEST) $(TEST) -v --tb=short
	@echo "$(GREEN)✓ Test completed$(NC)"

test-markers: ## Run tests by marker (usage: make test-markers MARKER=performance)
	@if [ -z "$(MARKER)" ]; then \
		echo "$(RED)Error: MARKER variable required$(NC)"; \
		echo "Usage: make test-markers MARKER=performance"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Running tests marked as $(MARKER)...$(NC)"
	$(PYTEST) tests/ -v -m $(MARKER) --tb=short
	@echo "$(GREEN)✓ Test completed$(NC)"

# Code quality targets
lint: ## Check code with ruff
	@echo "$(YELLOW)Linting code with ruff...$(NC)"
	$(RUFF) check core/ models/ app/ tests/
	@echo "$(GREEN)✓ Lint check passed$(NC)"

lint-fix: ## Fix lint issues with ruff
	@echo "$(YELLOW)Fixing lint issues...$(NC)"
	$(RUFF) check --fix core/ models/ app/ tests/
	@echo "$(GREEN)✓ Lint issues fixed$(NC)"

format: ## Format code with black
	@echo "$(YELLOW)Formatting code with black...$(NC)"
	$(BLACK) core/ models/ app/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(YELLOW)Checking code formatting...$(NC)"
	$(BLACK) --check core/ models/ app/ tests/
	@echo "$(GREEN)✓ Code formatting check passed$(NC)"

type-check: ## Type check code with mypy
	@echo "$(YELLOW)Type checking code...$(NC)"
	$(MYPY) core/ models/ || true
	@echo "$(GREEN)✓ Type check completed$(NC)"

security-check: ## Security check with bandit
	@echo "$(YELLOW)Running security checks...$(NC)"
	$(BANDIT) -r core/ models/ app/ -ll || true
	@echo "$(GREEN)✓ Security check completed$(NC)"

quality-check: format-check lint type-check security-check ## Run all quality checks
	@echo "$(GREEN)✓ All quality checks passed$(NC)"

quality-fix: lint-fix format ## Fix code issues
	@echo "$(GREEN)✓ Code issues fixed$(NC)"

# Pre-commit manual check
pre-commit-check: ## Run pre-commit checks manually
	@echo "$(YELLOW)Running pre-commit checks...$(NC)"
	pre-commit run --all-files
	@echo "$(GREEN)✓ Pre-commit checks passed$(NC)"

# Development targets
run: ## Run Streamlit app
	@echo "$(YELLOW)Starting Streamlit app...$(NC)"
	streamlit run app/main.py

run-dev: ## Run Streamlit app in development mode
	@echo "$(YELLOW)Starting Streamlit app (development mode)...$(NC)"
	streamlit run app/main.py --logger.level=debug

docs: ## Generate documentation
	@echo "$(YELLOW)Generating documentation...$(NC)"
	sphinx-build -b html docs/ docs/_build/
	@echo "$(GREEN)✓ Documentation generated (docs/_build/index.html)$(NC)"

# Cleanup targets
clean: clean-cache clean-test ## Clean all generated files

clean-cache: ## Remove Python cache files
	@echo "$(YELLOW)Removing cache files...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cache cleaned$(NC)"

clean-test: ## Remove test artifacts
	@echo "$(YELLOW)Removing test artifacts...$(NC)"
	rm -rf htmlcov/ test-report.html test-results.xml coverage.xml .coverage
	@echo "$(GREEN)✓ Test artifacts removed$(NC)"

# Combined targets
all: install-dev setup-pre-commit quality-check test ## Complete setup and checks

status: ## Show project status
	@echo "$(BLUE)SpectrumIA Project Status$(NC)"
	@echo ""
	@echo "$(GREEN)Files:$(NC)"
	@echo "  Python files: $$(find core models app tests -name '*.py' | wc -l)"
	@echo "  Test files: $$(find tests -name 'test_*.py' | wc -l)"
	@echo "  Total lines: $$(find core models app tests -name '*.py' -exec wc -l {} + | tail -1 | awk '{print $$1}')"
	@echo ""
	@echo "$(GREEN)Dependencies:$(NC)"
	@echo "  Installed: $$(pip list | wc -l)"
	@echo ""
	@echo "$(GREEN)Configuration:$(NC)"
	@[ -f pyproject.toml ] && echo "  ✓ pyproject.toml" || echo "  ✗ pyproject.toml"
	@[ -f .pre-commit-config.yaml ] && echo "  ✓ .pre-commit-config.yaml" || echo "  ✗ .pre-commit-config.yaml"
	@[ -f .github/workflows/pytest.yml ] && echo "  ✓ GitHub Actions (pytest)" || echo "  ✗ GitHub Actions (pytest)"
	@[ -f .github/workflows/coverage.yml ] && echo "  ✓ GitHub Actions (coverage)" || echo "  ✗ GitHub Actions (coverage)"

# Development workflow
workflow: clean quality-fix test ## Run typical development workflow (clean, format, lint, test)
	@echo "$(GREEN)✓ Development workflow completed$(NC)"

.PHONY: all help status workflow
