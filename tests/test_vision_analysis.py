# tests/new_test_vision_analysis.py
import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.vision_analyser import VisionAnalyzer
from electroninja.backend.vision_processor import VisionProcessor

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_separator(title=None):
    """Print a formatted separator line with an optional title."""
    width = 80
    if title:
        print("\n" + "=" * 20 + f" {title} " + "=" * (width - len(title) - 22) + "\n")
    else:
        print("\n" + "=" * width + "\n")

def test_vision_analysis(image_path, original_request):
    """
    Test vision analysis of circuit images using the VisionProcessor
    
    Args:
        image_path (str): Path to the circuit image
        original_request (str): Original user request
    """
    print_separator("TEST: VISION ANALYSIS")
    print(f"Image path: {image_path}")
    print(f"Original request: '{original_request}'")
    
    # Validate image path
    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found: {image_path}")
        return
    
    try:
        # Initialize components
        config = Config()
        vision_processor = VisionProcessor(config)
        
        # Get the vision image analysis prompt
        from electroninja.llm.prompts.circuit_prompts import VISION_IMAGE_ANALYSIS_PROMPT
        
        # Intercept the OpenAI API call to capture the exact prompt and response
        import openai
        original_create = openai.ChatCompletion.create
        
        def create_wrapper(**kwargs):
            # Print the exact prompt going to the model
            print("\n=== EXACT PROMPT SENT TO VISION MODEL ===")
            for message in kwargs["messages"]:
                print(f"Role: {message['role']}")
                # For vision content, just note that there's an image rather than dumping binary data
                if isinstance(message['content'], list):
                    print("Content: [Contains image data and the following text]")
                    for item in message['content']:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            print(f"Text content: {item['text']}")
                else:
                    print(f"Content: {message['content']}")
            print("===========================\n")
            
            # Call the original API
            response = original_create(**kwargs)
            
            # Print the exact raw response from the model
            print("\n=== EXACT RAW RESPONSE FROM VISION MODEL ===")
            raw_response = response.choices[0].message.content.strip()
            print(raw_response)
            print("===========================\n")
            
            return response
        
        # Print the vision prompt template that would be used
        print("\n=== VISION ANALYSIS PROMPT TEMPLATE ===")
        print(VISION_IMAGE_ANALYSIS_PROMPT.format(original_request=original_request))
        print("===========================\n")
        
        # Replace the API method temporarily if available
        try:
            openai.ChatCompletion.create = create_wrapper
        except:
            print("Warning: Could not intercept OpenAI API call - will not show exact prompt and response")
        
        # Analyze the image
        analysis = vision_processor.analyze_circuit_image(image_path, original_request)
        
        print("\n=== FINAL VISION ANALYSIS RESULT ===")
        print(analysis)
        
        # Check if the circuit is verified
        is_verified = vision_processor.is_circuit_verified(analysis)
        print(f"\nCircuit verification result: {'✅ Verified' if is_verified else '❌ Not verified'}")
        
        print_separator("TEST COMPLETED")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original method if it was replaced
        try:
            if 'original_create' in locals():
                openai.ChatCompletion.create = original_create
        except:
            pass

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