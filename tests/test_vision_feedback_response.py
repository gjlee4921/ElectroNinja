# tests/new_test_vision_feedback_response.py
import os
import sys
import logging
import openai
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.backend.chat_response_generator import ChatResponseGenerator

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

def test_vision_feedback_response(vision_feedback):
    """
    Test generating user-friendly responses from vision model feedback
    using the ChatResponseGenerator
    
    Args:
        vision_feedback (str): Feedback from vision model
        
    Returns:
        str: User-friendly response
    """
    print_separator("TEST: VISION FEEDBACK RESPONSE")
    
    # Initialize components
    config = Config()
    llm_provider = OpenAIProvider(config)
    chat_generator = ChatResponseGenerator(llm_provider)
    
    print("Vision feedback:")
    print("-" * 60)
    print(vision_feedback)
    print("-" * 60)
    
    # Get the vision feedback prompt template
    from electroninja.llm.prompts.chat_prompts import VISION_FEEDBACK_PROMPT
    
    # Intercept the OpenAI API call to capture the exact prompt and response
    original_create = openai.ChatCompletion.create
    
    def create_wrapper(**kwargs):
        # Print the exact prompt going to the model
        print("\n=== EXACT PROMPT SENT TO LLM ===")
        for message in kwargs["messages"]:
            print(f"Role: {message['role']}")
            print(f"Content:\n{message['content']}")
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
    
    try:
        # Show the prompt template that would be used
        print("\n=== VISION FEEDBACK PROMPT TEMPLATE ===")
        exact_prompt = VISION_FEEDBACK_PROMPT.format(vision_feedback=vision_feedback)
        print(exact_prompt)
        print("===========================\n")
        
        # Generate response
        response = chat_generator.generate_feedback_response(vision_feedback)
        
        print("\n=== FINAL FEEDBACK RESPONSE ===")
        print(response)
        
        # Check if the response indicates success
        is_success = vision_feedback.strip() == 'Y'
        print(f"\nCircuit success status: {'✅ Success' if is_success else '❌ Needs improvement'}")
        
        print_separator("TEST COMPLETED")
        return response
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Restore original method
        openai.ChatCompletion.create = original_create

if __name__ == "__main__":
    # Test case 1: Successful circuit (Y)
    success_feedback = "Y"
    
    # Test case 2: Circuit with issues (detailed feedback)
    failure_feedback = """1. **Components Present**:
   - Voltage source (V1 = 50V)
   - Resistor R1 = 200 ohms
   - Resistor R2 = 100 ohms

2. **Connections**:
   - Resistors R1 and R2 are in parallel.
   - The parallel combination is connected across the voltage source.

3. **Comparison to Standard Voltage Divider**:
   - A standard voltage divider circuit consists of two resistors in series. The output voltage is taken across one of the resistors.

4. **Issues**:
   - The current configuration has R1 and R2 in parallel, not in series.

5. **Why It Doesn't Meet the Requirements**:
   - A voltage divider relies on the series arrangement of resistors to divide the input voltage proportionally based on their resistance values (principle: \( V_out = V_in \times \frac{R2}{R1 + R2} \)).

6. **Recommendations for Fixing**:
   - Connect R1 and R2 in series.
   - Connect one terminal of R1 to the positive end of V1.
   - Connect the other terminal of R2 to the negative end (or ground) of V1.
   - Take the output voltage across R2 (or R1, depending on the desired division ratio).

7. **Expected Behavior After Modifications**:
   - The circuit will correctly divide the 50V input according to the ratio of the resistances.
   - With R1 = 200 ohms and R2 = 100 ohms, the expected output voltage across R2 will be:
     \[
     V_{out} = 50 \times \frac{100}{200 + 100} = \frac{50}{3} \approx 16.67V
     \]

By reconfiguring R1 and R2 in series, the circuit will function as a proper voltage divider."""
    
    # Run tests
    print("\n\n=== TEST 1: SUCCESSFUL CIRCUIT ===\n")
    test_vision_feedback_response(success_feedback)
    
    print("\n\n=== TEST 2: CIRCUIT WITH ISSUES ===\n")
    test_vision_feedback_response(failure_feedback)