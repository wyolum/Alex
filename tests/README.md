# Alex CAD Tests

This directory contains unit tests for the Alex CAD project, with a focus on JSON functionality.

## Test Files

### `test_json_parts_library.py`
Tests the existing JSON parts library file (`part_libraries/parts_library.json`).

**Coverage:**
- JSON structure validation
- Part data integrity
- Piecewise pricing data
- Interface definitions
- Database consistency

**Tests:** 29

### `test_json_export_import.py`
Tests the JSON export/import functionality module (`scripts/packages/json_export.py`).

**Coverage:**
- Library export to JSON
- JSON validation
- Part retrieval by name
- Piecewise price calculations
- Library import from JSON

**Tests:** 28 (23 passed, 5 skipped)

## Running Tests

### Quick Start

```bash
# Activate the conda environment
conda activate alex_test

# Run all tests
python -m pytest tests/ -v

# Or use the test runner script
python tests/run_json_tests.py -v
```

### Using pytest directly

```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_json_parts_library.py -v

# Run specific test class
python -m pytest tests/test_json_parts_library.py::TestPricingData -v

# Run specific test method
python -m pytest tests/test_json_parts_library.py::TestPricingData::test_piecewise_price_parts -v

# Run with coverage
python -m pytest tests/ --cov=scripts/packages --cov-report=html
```

### Using the test runner script

```bash
# Run all tests
python tests/run_json_tests.py

# Run with verbose output
python tests/run_json_tests.py -v

# Run with coverage report
python tests/run_json_tests.py -c

# Run specific test file
python tests/run_json_tests.py -f test_json_parts_library.py

# Run specific test class
python tests/run_json_tests.py -f test_json_parts_library.py -t TestPricingData

# Run specific test method
python tests/run_json_tests.py -f test_json_parts_library.py -t "TestPricingData::test_piecewise_price_parts"
```

## Test Results

Latest test run:
```
======================== 52 passed, 5 skipped in 0.74s =========================
```

- ✅ **52 tests passed**
- ⏭️ **5 tests skipped** (import tests requiring library initialization)
- ❌ **0 tests failed**

## Requirements

The tests require the following packages (already in `alex_test` environment):
- pytest
- numpy
- All packages from `scripts/requirements.txt`

To install pytest in the environment:
```bash
conda activate alex_test
pip install pytest
```

## Test Documentation

See `JSON_TEST_SUMMARY.md` for detailed information about:
- Test coverage
- Issues found and fixed
- Usage examples
- Recommendations

## Directory Structure

```
tests/
├── README.md                      # This file
├── JSON_TEST_SUMMARY.md          # Detailed test summary
├── run_json_tests.py             # Test runner script
├── test_json_parts_library.py    # JSON file structure tests
└── test_json_export_import.py    # Export/import functionality tests
```

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Use descriptive test names
3. Add docstrings to test methods
4. Group related tests in test classes
5. Update this README with new test information

## Continuous Integration

To integrate these tests into a CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    conda activate alex_test
    python -m pytest tests/ -v --cov=scripts/packages
```

## Troubleshooting

### Import Errors
If you get import errors, make sure:
1. You're in the project root directory
2. The `alex_test` conda environment is activated
3. All dependencies are installed

### Database Errors
Some tests interact with the SQLite database. If you encounter database errors:
1. Ensure the database file exists in `part_libraries/Main/Parts.db`
2. Check file permissions
3. Try running from the project root directory

### Skipped Tests
Some import tests are skipped because they require:
- Wireframe files (`.npy` files)
- Proper library initialization
- STL files

These tests can be enabled by setting up proper test fixtures.
