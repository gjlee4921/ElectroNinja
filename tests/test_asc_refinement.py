# tests/new_test_asc_refinement.py
import os
import sys
import logging
import json
import openai
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.llm.vector_store import VectorStore
from electroninja.backend.circuit_generator import CircuitGenerator

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_separator(title=None):
    """Print a formatted separator line with an optional title."""
    width = 80
    if title:
        print("\n" + "=" * 20 + f" {title} " + "=" * (width - len(title) - 22) + "\n")
    else:
        print("\n" + "=" * width + "\n")

def test_asc_code_refinement():
    """
    Test the ASC code refinement process by:
    1. Starting with an initial ASC code
    2. Using vision feedback to refine it
    3. Outputting the refined code
    """
    print_separator("TEST: ASC CODE REFINEMENT")
    
    # Initialize components
    config = Config()
    llm_provider = OpenAIProvider(config)
    vector_store = VectorStore(config)
    circuit_generator = CircuitGenerator(llm_provider, vector_store)
    
    # Original request
    original_request = "Create a low pass filter"
    print(f"Original request: {original_request}")
    
    # Initial ASC code (iteration 0) - o3-mini's response
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
    
    # Print initial ASC code
    print("\nInitial ASC code (iteration 0):")
    print("-" * 60)
    print(initial_asc_code)
    print("-" * 60)
    
    # Vision feedback for iteration 0
    vision_feedback = """1. **What's wrong with the current implementation:**

   The circuit consists of an inductor (L1) and a resistor (R1) in series with an AC source. While inductors can be used to create filters, this particular arrangement does not constitute a low-pass filter configuration on its own.

2. **Why it doesn't meet the requirements:**

   - A low-pass filter typically allows low-frequency signals to pass while attenuating high-frequency signals. In the classic low-pass filter, the simplest form would be an RC (resistor-capacitor) low-pass filter, which uses a resistor (R) and a capacitor (C) in series, with the output taken across the capacitor.
   - Here, we have an RL series circuit, which behaves differently. It does not serve the purpose of a low-pass filter in the standard sense. Instead, an RL series circuit with output across the inductor is more commonly used for high-pass filtering due to the inductor's tendency to block high-frequency signals.

3. **Detailed recommendations for fixing the circuit:**

   - Replace the inductor (L1) with a capacitor (C1). Connect the capacitor in parallel with the resistor (R1) to form a classic RC low-pass filter.
   - If an RL filter is specifically required, ensure the correct configuration and note that it will typically result in a high-pass filter.

4. **Expected behavior after the modifications:**

   - After replacing the inductor with a capacitor and forming a proper RC low-pass filter, the circuit will allow signals with frequencies lower than a certain cutoff frequency to pass with little attenuation.
   - The cutoff frequency (\\( f_c \\)) of an RC low-pass filter is determined by the formula:

     \\[
     f_c = \\frac{1}{2\\pi RC}
     \\]

   - Adjust the resistor and capacitor values to achieve the desired cutoff frequency."""
    
    # Print vision feedback
    print("\nVision feedback for iteration 0:")
    print("-" * 60)
    print(vision_feedback)
    print("-" * 60)
    
    # Create conversation history with complete context
    history = [
        {
            "iteration": 0,
            "asc_code": initial_asc_code,
            "vision_feedback": vision_feedback
        }
    ]
    
    # Get the refinement prompt template
    from electroninja.llm.prompts.circuit_prompts import GENERAL_INSTRUCTION, REFINEMENT_PROMPT_TEMPLATE
    
    # Intercept the OpenAI API call to capture the exact prompt and response
    original_create = openai.ChatCompletion.create
    
    def create_wrapper(**kwargs):
        # Print the exact prompts going to the model
        print("\n=== EXACT PROMPTS SENT TO LLM ===")
        for message in kwargs["messages"]:
            print(f"Role: {message['role']}")
            print(f"Content:\n{message['content']}")
            print("-" * 50)
        print("===========================\n")
        
        # Call the original API
        response = original_create(**kwargs)
        
        # Print the exact raw response from the model
        print("\n=== EXACT RAW RESPONSE FROM LLM ===")
        raw_response = response.choices[0].message.content.strip()
        print(raw_response)
        print("===========================\n")
        
        return response
    
    # Replace the API method temporarily
    openai.ChatCompletion.create = create_wrapper
    
    # Refine ASC code
    print_separator("REFINING ASC CODE")
    
    try:
        # Build the exact refinement prompt that would be used
        print("\n=== REFINEMENT PROMPT THAT WILL BE USED ===")
        refinement_prompt_parts = ["Below are previous attempts and feedback:\n\n"]
        
        for item in history:
            refinement_prompt_parts.append(f"Attempt {item.get('iteration', '?')} ASC code:\n{item['asc_code']}\n\n")
            refinement_prompt_parts.append(f"Vision feedback (Iteration {item.get('iteration','?')}): {item['vision_feedback']}\n\n")
            
        refinement_prompt_parts.append(f"Original user's request: {original_request}\n\n")
        refinement_prompt_parts.append(REFINEMENT_PROMPT_TEMPLATE)
        
        # Join the parts to create the final prompt
        refinement_prompt = "".join(refinement_prompt_parts)
        
        print(refinement_prompt)
        print("===========================\n")
        
        # Get refined ASC code using the circuit generator
        refined_asc = circuit_generator.refine_asc_code(original_request, history)
        
        print("\nFINAL REFINED ASC CODE:")
        print("-" * 60)
        print(refined_asc)
        print("-" * 60)
        
        # Validate the refined ASC code
        is_valid = circuit_generator.validate_asc_code(refined_asc)
        print(f"\nValidation result: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        # Add to history for potential further iterations
        history.append({
            "iteration": 1,
            "asc_code": refined_asc,
            "vision_feedback": "Not analyzed yet"  # Would be filled by vision model in real scenario
        })
        
        # Save history to JSON for reference
        with open("refinement_history.json", "w") as f:
            json.dump(history, f, indent=2)
        print("\nSaved refinement history to refinement_history.json")
        
        print_separator("TEST COMPLETED")
        return True
        
    except Exception as e:
        print(f"Error during refinement test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original method
        openai.ChatCompletion.create = original_create

if __name__ == "__main__":
    test_asc_code_refinement()