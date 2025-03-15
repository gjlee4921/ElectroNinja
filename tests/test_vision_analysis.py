import os
import sys
import logging
import openai
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.backend.vision_processor import VisionProcessor

load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_vision_analysis(image_path, original_request):
    """Test vision analysis of circuit images with printed LLM I/O"""
    print("\n====== TEST: VISION ANALYSIS ======")
    print(f"Image path: {image_path}")
    print(f"Original request: '{original_request}'")
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return
    
    config = Config()
    vision_processor = VisionProcessor(config)
    
    original_create = openai.ChatCompletion.create

    def create_wrapper(**kwargs):
        print("\n=== RAW INPUT TO VISION MODEL ===")
        for message in kwargs["messages"]:
            print(f"Role: {message['role']}")
            if isinstance(message['content'], list):
                print("Content: [Contains image data and text]")
                for item in message['content']:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        print(f"Text: {item['text']}")
            else:
                print(f"Content:\n{message['content']}")
            print("-" * 50)
        response = original_create(**kwargs)
        print("\n=== RAW OUTPUT FROM VISION MODEL ===")
        print(response.choices[0].message.content)
        print("=" * 25)
        return response

    try:
        openai.ChatCompletion.create = create_wrapper
    except Exception as e:
        print("Warning: Could not intercept OpenAI API calls")
    
    try:
        analysis = vision_processor.analyze_circuit_image(image_path, original_request)
        print("\n=== VISION ANALYSIS RESULT ===")
        print(analysis)
        is_verified = vision_processor.is_circuit_verified(analysis)
        print(f"\nCircuit verified: {'Yes' if is_verified else 'No'}")
    finally:
        try:
            openai.ChatCompletion.create = original_create
        except:
            pass
    
    return analysis

if __name__ == "__main__":
    default_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "output", "prompt1", "output0", "image.png"
    )
    default_requests = [
        "Create a circuit with 6 resistances in parallel and a battery 6V"
    ]
    for request in default_requests:
        test_vision_analysis(default_path, request)
        print("\n" + "-" * 60 + "\n")
