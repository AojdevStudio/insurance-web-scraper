# Testing Documentation

## Overview

This directory contains the test suite for the dental insurance guidelines web scraper project. The testing framework is based on pytest with additional plugins for asyncio testing, mocking, and code coverage.

## Test Structure

- `tests/conftest.py`: Contains common pytest fixtures and compatibility patches
- `tests/spiders/`: Tests for individual carrier spider implementations
- `tests/__init__.py`: Package initialization
- `tests/test_data_cleaner.py`: Tests for data cleaning and validation modules

## Running Tests

To run the full test suite with coverage reporting:

```bash
pytest
```

This will automatically use the settings in `pytest.ini` to run all tests and generate coverage reports.

## Coverage Requirements

The project requires 80% code coverage as specified in the acceptance criteria. Coverage reports are generated in both terminal output and HTML format.

To view the HTML coverage report:

```bash
# Run tests and generate report
pytest

# Open the HTML report
open htmlcov/index.html
```

## Mock Data

Test fixtures provide mock responses and sample data to simulate:

- HTML responses from insurance carriers
- PDF downloads
- Spider behavior
- Error conditions

## Adding New Tests

When adding new tests:

1. Follow the existing patterns in similar test files
2. Use pytest fixtures for shared setup
3. Make sure to test both success and error paths
4. Mock external dependencies to ensure tests run reliably
5. Update mocks when the underlying code changes

## Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

All test fixtures and functions have docstrings explaining their purpose. 