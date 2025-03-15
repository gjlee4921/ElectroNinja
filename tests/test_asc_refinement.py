import os
import sys
import logging
import openai
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.llm.vector_store import VectorStore
from electroninja.backend.circuit_generator import CircuitGenerator

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_asc_code_refinement():
    """Test ASC code refinement based on vision feedback with LLM I/O printed"""
    print("\n====== TEST: ASC CODE REFINEMENT ======")
    
    config = Config()
    llm_provider = OpenAIProvider(config)
    vector_store = VectorStore(config)
    circuit_generator = CircuitGenerator(llm_provider, vector_store)
    
    original_request = "Create a low pass filter"
    print(f"Original request: {original_request}")
    
    initial_asc_code = """Version 4
SHEET 1 880 680
WIRE 224 112 128 112
WIRE 400 112 304 112
WIRE 128 144 128 112
WIRE 400 144 400 112
WIRE 128 256 128 224
WIRE 400 256 400 224
WIRE 400 256 128 256
WIRE 128 272 128 256
FLAG 128 272 0
FLAG 400 112 output
IOPIN 400 112 Out
SYMBOL voltage 128 128 R0
WINDOW 123 0 0 Left 0
WINDOW 39 0 0 Left 0
SYMATTR InstName V1
SYMATTR Value SINE(0 AC 1)
SYMBOL ind 320 96 R90
WINDOW 0 5 56 VBottom 2
WINDOW 3 32 56 VTop 2
SYMATTR InstName L1
SYMATTR Value 0.01
SYMBOL res 384 128 R0
SYMATTR InstName R1
SYMATTR Value 100"""
    
    print("\nInitial ASC code:")
    print(initial_asc_code)
    
    vision_feedback = """1. **What's wrong with the current implementation:**
The circuit uses an inductor (L1) and resistor (R1) in series which does not form a typical low-pass filter.
2. **Recommendation:**
Replace the inductor with a capacitor and form an RC low-pass filter.
3. **Expected:**
An RC low-pass filter with the appropriate cutoff frequency."""
    
    print("\nVision feedback:")
    print(vision_feedback)
    
    history = [{
        "iteration": 0,
        "asc_code": initial_asc_code,
        "vision_feedback": vision_feedback
    }]
    
    original_create = openai.ChatCompletion.create

    def create_wrapper(**kwargs):
        print("\n=== RAW INPUT TO LLM ===")
        for message in kwargs["messages"]:
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
        refined_asc = circuit_generator.refine_asc_code(original_request, history)
        print("\n=== REFINED ASC CODE ===")
        print(refined_asc)
    finally:
        openai.ChatCompletion.create = original_create
    
    return refined_asc

if __name__ == "__main__":
    test_asc_code_refinement()
