# tests/test_vision_feedback_response.py
import os
import sys
import logging
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

def test_vision_feedback_response(vision_feedback):
    """
    Test generating user-friendly responses from vision model feedback
    
    Args:
        vision_feedback (str): Feedback from vision model
        
    Returns:
        str: User-friendly response
    """
    # Initialize components
    config = Config()
    llm_provider = OpenAIProvider(config)
    
    print("\n====== TEST: VISION FEEDBACK RESPONSE ======\n")
    print("Vision feedback:")
    print("-" * 40)
    print(vision_feedback)
    print("-" * 40)
    
    # Generate response
    try:
        response = llm_provider.generate_vision_feedback_response(vision_feedback)
        
        print("\nGenerated response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        return response
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

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

5. **Why It Doesn’t Meet the Requirements**:
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