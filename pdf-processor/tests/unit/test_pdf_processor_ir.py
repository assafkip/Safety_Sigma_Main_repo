import unittest
from src.pdf_processor.ir import to_ir_objects

class TestIRFunctions(unittest.TestCase):

    def test_to_ir_objects(self):
        # Example input: list of Span objects
        spans = [
            # Add mock Span objects here for testing
        ]
        
        # Expected output: list of IR objects
        expected_ir_objects = [
            # Add expected IR objects here
        ]
        
        # Call the function to test
        result = to_ir_objects(spans)
        
        # Assert that the result matches the expected output
        self.assertEqual(result, expected_ir_objects)

if __name__ == '__main__':
    unittest.main()