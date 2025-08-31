# This file serves as a small harness that invokes the compiled rule.

from src.pdf_processor.rules import compile_rules
from src.pdf_processor.ir import to_ir_objects
from src.pdf_processor.extract import extract_amounts
from src.pdf_processor.ingest import pdf_to_text_with_offsets

def main():
    # Example usage of the functions
    path = "path/to/pdf/document.pdf"  # Replace with the actual PDF path
    spans = pdf_to_text_with_offsets(path)
    amounts = extract_amounts(" ".join(span.text for span in spans))
    ir_objects = to_ir_objects(spans)
    rules = compile_rules(ir_objects)

    # Here you would typically apply the rules to the data
    print("Extracted amounts:", amounts)
    print("IR Objects:", ir_objects)
    print("Compiled Rules:", rules)

if __name__ == "__main__":
    main()