# tests/test_circuit_evaluation.py
import os
import sys
import logging
import openai
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.llm.prompts.circuit_prompts import (
    GENERAL_INSTRUCTION,
    CIRCUIT_RELEVANCE_EVALUATION_PROMPT
)

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_circuit_evaluation(prompt):
    """
    Test whether the evaluation model correctly identifies if a request is circuit-related
    
    Args:
        prompt (str): User prompt to evaluate
        
    Returns:
        dict: Dictionary with evaluation results
    """
    # Initialize components
    config = Config()
    llm_provider = OpenAIProvider(config)
    
    # Initialize result dictionary
    result = {
        "prompt": prompt,
        "is_circuit_related": False,
        "raw_evaluation": ""
    }
    
    print("\n====== TEST: CIRCUIT RELEVANCE EVALUATION ======\n")
    
    # Build evaluation prompt
    evaluation_prompt = (
        f"{GENERAL_INSTRUCTION}\n\n"
        f"{CIRCUIT_RELEVANCE_EVALUATION_PROMPT.format(prompt=prompt)}"
    )
    
    print("=== PROMPT SENT TO EVALUATION MODEL (gpt-4o-mini) ===")
    print(evaluation_prompt)
    print("\n===========================\n")
    
    # Call the model
    try:
        response = openai.ChatCompletion.create(
            model=llm_provider.evaluation_model,
            messages=[{"role": "user", "content": evaluation_prompt}]
        )
        
        # Extract and process response
        raw_result = response.choices[0].message.content.strip()
        is_circuit_related = raw_result.upper().startswith('Y')
        
        # Store results
        result["raw_evaluation"] = raw_result
        result["is_circuit_related"] = is_circuit_related
        
        print("=== RAW RESPONSE FROM EVALUATION MODEL ===")
        print(raw_result)
        print("\n===========================\n")
        
        print(f"Final evaluation result: {is_circuit_related} (Circuit-related: {'Yes' if is_circuit_related else 'No'})")
        
    except Exception as e:
        print(f"Error during evaluation: {str(e)}")
        result["error"] = str(e)
    
    return result

if __name__ == "__main__":
    # Sample prompts to test
    prompts = [
        "Create a circuit with two resistors in parallel",
        "Design a simple RC low-pass filter",
        "Tell me about World War 2",
    ]
    
    # Test each prompt
    results = {}
    for prompt in prompts:
        print(f"\n\n*** TESTING PROMPT: '{prompt}' ***\n")
        result = test_circuit_evaluation(prompt)
        results[prompt] = result
    
    # Print summary
    print("\n\n====== TEST SUMMARY ======\n")
    for prompt, result in results.items():
        circuit_result = "Circuit-related" if result["is_circuit_related"] else "Not circuit-related"
        print(f"Prompt: '{prompt}' => {circuit_result}")