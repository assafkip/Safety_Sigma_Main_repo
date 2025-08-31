# Safety Sigma Main Repository

## Overview
The Safety Sigma Main Repository is designed to provide a comprehensive suite of tests for validating specific behaviors related to payment processing, memo preservation, link matching, and category checks. This project aims to ensure the reliability and correctness of the functionalities it tests.

## Directory Structure
```
Safety_Sigma_Main_repo
├── tests
│   └── golden_cases
│       └── test_indicators.py
└── README.md
```

## Tests
The `tests/` directory contains all the test files for the project. Within this directory, the `golden_cases/` subdirectory is specifically for golden case tests. The `test_indicators.py` file includes Python test functions that validate the following behaviors:

- **Payment Amount Exactness**: Ensures that the payment amount appears verbatim.
- **Memo Preservation**: Validates that the memo is preserved as a token sequence.
- **Link Matching**: Checks that the wa.me link matches the specified regex and preserves the scheme and path.
- **Category Checks**: Confirms that the generated categories match the source categories with no differences.

## Usage
To run the tests, navigate to the project directory and execute the test suite using your preferred testing framework (e.g., pytest). Ensure that all dependencies are installed and configured correctly before running the tests.