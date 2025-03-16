import os
import sys
import logging
import openai
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.backend.merging import RequestMerger

# Load environment variables and set up logging
load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_request_merger():
    """Test merging multiple circuit requests with LLM I/O printed"""
    print("\n====== TEST: REQUEST MERGER ======")
    
    # Initialize configuration and providers
    config = Config()
    llm_provider = OpenAIProvider(config)
    
    # Create the RequestMerger from the backend
    request_merger = RequestMerger(llm_provider)
    
    # Example request dictionary - fill this with your test data
    request_dict = {
        "request1": "Create a circuit with a battery 5V and two resistances in parallel 5 ohms and 3 ohms",
        "request2": "Add another resistor 4 ohms in parallel with the existing resistors",
        "request3": "Change the battery to 10V",
        "request4": "Add a capacitor 10uF in series with the resistors",
        "request5": "Remove the 5 ohms resistor"
    }
    
    print("\n=== REQUEST DICTIONARY ===")
    print(request_dict)
    
    # Intercept OpenAI API calls to print raw input and output
    original_create = openai.ChatCompletion.create

    def create_wrapper(**kwargs):
        print("\n=== RAW INPUT TO LLM ===")
        for message in kwargs.get("messages", []):
            print(f"Role: {message['role']}")
            print(f"Content:\n{message['content']}")
            print("-" * 50)
        response = original_create(**kwargs)
        print("\n=== RAW OUTPUT FROM LLM ===")
        print(response.choices[0].message.content)
        print("=" * 25)
        return response

    openai.ChatCompletion.create = create_wrapper

    try:
        # Generate the merged prompt
        merged_prompt = request_merger.merge_requests(request_dict)
        print("\n=== FINAL MERGED PROMPT ===")
        print(merged_prompt)
        return merged_prompt
    finally:
        # Restore the original ChatCompletion.create method
        openai.ChatCompletion.create = original_create

if __name__ == "__main__":
    test_request_merger()