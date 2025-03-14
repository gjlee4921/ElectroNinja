# tests/test_asc_refinement.py
import os
import sys
import logging
import json
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider

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

def extract_clean_asc_code(asc_code):
    """
    Extract only the pure ASC code starting from 'Version 4'
    This ensures we don't include descriptions in the ASC code examples
    """
    if "Version 4" in asc_code:
        idx = asc_code.find("Version 4")
        return asc_code[idx:].strip()
    return asc_code.strip()

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
    
    # Original request
    original_request = "Create a low pass filter"
    
    # System prompt used in the initial exchange
    system_prompt = """You are a world-class electrical engineer with absolute authority in LTSpice circuit design. You write .asc files with unwavering precision. When a client asks you to build a circuit, you must respond with clear, definitive statements and the exact .asc code required.

IMPORTANT: You must strictly restrict your responses to electrical engineering topics only. If the client's message is irrelevant to electrical engineering or circuits, respond ONLY with the single letter 'N'. There should be no additional commentary, explanations, or attempts to help with non-circuit topics. You are exclusively an electrical circuit design assistant."""
    
    # Initial user prompt with RAG examples
    initial_user_prompt = """Below are examples of circuits similar to the user's request:

Example 1:
Description: An RL low-pass filter using a 10 mH inductor in series with the input and a 100 Ω resistor to ground. This arrangement attenuates high-frequency signals above roughly 1.59 kHz.
ASC Code:
-----------------
Version 4
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
SYMATTR Value 100
-----------------

Example 2:
Description: An RLC band-pass filter using a 100 Ω resistor, a 10 mH inductor, and a 0.1 μF capacitor. The circuit allows signals near 5 kHz to pass while attenuating frequencies outside this range.
ASC Code:
-----------------
Version 4
SHEET 1 880 680
WIRE 192 128 96 128
WIRE 304 128 272 128
WIRE 432 128 384 128
WIRE 528 128 496 128
WIRE 96 160 96 128
WIRE 96 256 96 240
WIRE 496 256 496 128
WIRE 496 256 96 256
WIRE 96 288 96 256
FLAG 96 288 0
FLAG 528 128 output
IOPIN 528 128 Out
SYMBOL voltage 96 144 R0
WINDOW 123 0 0 Left 0
WINDOW 39 0 0 Left 0
SYMATTR InstName V1
SYMATTR Value SINE(0 AC 1)
SYMBOL res 288 112 R90
WINDOW 0 0 56 VBottom 2
WINDOW 3 32 56 VTop 2
SYMATTR InstName R1
SYMATTR Value 100
SYMBOL cap 496 112 R90
WINDOW 0 0 32 VBottom 2
WINDOW 3 32 32 VTop 2
SYMATTR InstName C1
SYMATTR Value 0.1e-6
SYMBOL ind 400 112 R90
WINDOW 0 5 56 VBottom 2
WINDOW 3 32 56 VTop 2
SYMATTR InstName L1
SYMATTR Value 0.01
-----------------

Example 3:
Description: An RL high-pass filter circuit using a 100 Ω resistor in series with the input and a 10 mH inductor to ground. It passes high-frequency signals while attenuating those below approximately 1.59 kHz (cutoff frequency f_c = R/(2πL)).
ASC Code:
-----------------
Version 4
SHEET 1 880 680
WIRE 176 128 96 128
WIRE 320 128 256 128
WIRE 96 160 96 128
WIRE 320 160 320 128
WIRE 96 256 96 240
WIRE 320 256 320 240
WIRE 320 256 96 256
WIRE 96 272 96 256
FLAG 96 272 0
FLAG 320 128 output
IOPIN 320 128 Out
SYMBOL ind 304 144 R0
SYMATTR InstName L1
SYMATTR Value 0.01
SYMBOL res 160 144 R270
WINDOW 0 32 56 VTop 2
WINDOW 3 0 56 VBottom 2
SYMATTR InstName R1
SYMATTR Value 100
SYMBOL voltage 96 144 R0
SYMATTR InstName V1
-----------------

User's request: Create a low pass filter

Now, based on the examples above, generate the complete .asc code for a circuit that meets the user's request.

CRITICAL INSTRUCTIONS:
1. Your output MUST begin with 'Version 4' and contain ONLY valid LTSpice ASC code
2. Do NOT include ANY descriptions, explanations, or comments before the ASC code
3. Do NOT include ANY text that is not part of the ASC file format
4. If the request is not related to circuits, respond only with 'N'

OUTPUT FORMAT (exact):
Version 4
SHEET 1 ...
... [remaining ASC code] ..."""
    
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
    
    # Create conversation history with complete context
    history = [
        {
            "iteration": 0,
            "system_prompt": system_prompt,
            "user_prompt": initial_user_prompt,
            "asc_code": initial_asc_code,
            "vision_feedback": vision_feedback
        }
    ]
    
    print(f"Original request: {original_request}")
    
    # Display initial system prompt
    print("\nInitial system prompt:")
    print("-" * 60)
    print(system_prompt)
    print("-" * 60)
    
    # Display initial user prompt with RAG
    print("\nInitial user prompt with RAG examples:")
    print("-" * 60)
    print(initial_user_prompt)
    print("-" * 60)
    
    # Display initial ASC code
    print("\nInitial ASC code (iteration 0) - o3-mini's response:")
    print("-" * 60)
    print(initial_asc_code)
    print("-" * 60)
    
    # Display vision feedback
    print("\nVision feedback for iteration 0:")
    print("-" * 60)
    print(vision_feedback)
    print("-" * 60)
    
    # Refine ASC code
    print_separator("REFINING ASC CODE")
    
    try:
        # Build raw refinement prompt (for debugging)
        prompt = "Below are previous attempts and feedback:\n\n"
        
        for item in history:
            prompt += f"Attempt {item.get('iteration', '?')} ASC code:\n{item['asc_code']}\n\n"
            prompt += f"Vision feedback (Iteration {item.get('iteration','?')}): {item['vision_feedback']}\n\n"
            
        prompt += f"Original user's request: {original_request}\n\n"
        
        from electroninja.llm.prompts.circuit_prompts import REFINEMENT_PROMPT_TEMPLATE
        prompt += REFINEMENT_PROMPT_TEMPLATE
        
        print("\nRAW REFINEMENT PROMPT:")
        print("-" * 60)
        print(prompt)
        print("-" * 60)
        
        # Get refined ASC code
        refined_asc = llm_provider.refine_asc_code(original_request, history)
        
        # Clean the ASC code if needed
        refined_asc = extract_clean_asc_code(refined_asc)
        
        print("\nREFINED ASC CODE:")
        print("-" * 60)
        print(refined_asc)
        print("-" * 60)
        
        # Add to history for potential further iterations
        history.append({
            "iteration": 1,
            "asc_code": refined_asc,
            "vision_feedback": "Not analyzed yet" # Would be filled by vision model in real scenario
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

if __name__ == "__main__":
    test_asc_code_refinement()