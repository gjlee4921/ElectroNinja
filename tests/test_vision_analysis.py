# tests/test_vision_analysis.py
import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.vision_analyser import VisionAnalyzer

# Load environment variables
load_dotenv()

# Set up minimal logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='vision_test.log',
    filemode='w'
)

def test_vision_analysis(image_path, original_request):
    """
    Test vision analysis of circuit images and return raw output
    
    Args:
        image_path (str): Path to the circuit image
        original_request (str): Original user request
    """
    # Validate image path
    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found: {image_path}")
        return
    
    try:
        # Initialize components
        config = Config()
        vision_analyzer = VisionAnalyzer(config)
        
        # Analyze the image
        analysis = vision_analyzer.analyze_circuit_image(image_path, original_request)
        
        # Print only the raw LLM output with no formatting
        print(analysis)
        
    except Exception as e:
        print(f"ERROR: {str(e)}")

def main():
    """Main function to run the test"""
    parser = argparse.ArgumentParser(description='Test vision analysis of circuit images')
    parser.add_argument('--image', '-i', type=str, help='Path to circuit image')
    parser.add_argument('--request', '-r', type=str, help='User request to test')
    args = parser.parse_args()
    
    # Use default image path if not provided
    if not args.image:
        default_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                 "data", "output", "prompt1", "output0", "image.png")
        args.image = default_path
    
    # Use default request if not provided
    if not args.request:
        default_requests = [
            "Design a voltage divider circuit",
            "Create a circuit with two resistors in parallel",
            "Make an RC low-pass filter"
        ]
        
        for i, request in enumerate(default_requests, 1):
            if i > 1:
                print("\n----------------------------------------\n")
            test_vision_analysis(args.image, request)
    else:
        # Run single test with provided request
        test_vision_analysis(args.image, args.request)

if __name__ == "__main__":
    main()