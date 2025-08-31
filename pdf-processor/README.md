# pdf-processor

## Overview
The pdf-processor project is designed to process PDF files, extracting text and relevant information, and converting it into structured data formats. This project provides a set of utilities for ingesting PDF content, extracting specific data points, and compiling rules for further processing.

## Project Structure
```
pdf-processor
├── src
│   └── pdf_processor
│       ├── __init__.py
│       ├── ingest.py
│       ├── extract.py
│       ├── ir.py
│       ├── rules.py
│       └── audit.py
├── scripts
│   └── run_rule.py
├── tests
│   └── unit
│       └── test_pdf_processor_ir.py
└── README.md
```

## Installation
To install the necessary dependencies, please run:
```
pip install -r requirements.txt
```

## Usage
1. **Ingest PDF Files**: Use the `pdf_to_text_with_offsets` function from `ingest.py` to convert PDF files into text with offsets.
2. **Extract Amounts**: Utilize the `extract_amounts` function from `extract.py` to find and return amounts from the ingested text.
3. **Compile Rules**: The `compile_rules` function in `rules.py` allows you to create rules based on the extracted information.
4. **Audit Logs**: The `append_jsonl` function in `audit.py` can be used to log records in a JSON Lines format for auditing purposes.
5. **Run Rules**: The `run_rule.py` script serves as a harness to invoke the compiled rules.

## Testing
Unit tests for the project are located in the `tests/unit` directory. You can run the tests using:
```
pytest tests/unit
```

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.