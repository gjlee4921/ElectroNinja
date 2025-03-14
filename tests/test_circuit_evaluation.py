# tests/new_test_circuit_evaluation.py
import os
import sys
import logging
import openai
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.backend.request_evaluator import RequestEvaluator

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
    print("\n====== TEST: CIRCUIT RELEVANCE EVALUATION ======\n")
    print(f"Evaluating if request is circuit-related: '{prompt}'")
    
    # Initialize components
    config = Config()
    llm_provider = OpenAIProvider(config)
    request_evaluator = RequestEvaluator(llm_provider)
    
    # Initialize result dictionary
    result = {
        "prompt": prompt,
        "is_circuit_related": False,
        "raw_evaluation": ""
    }
    
    # Get the circuit relevance evaluation prompt template
    from electroninja.llm.prompts.circuit_prompts import GENERAL_INSTRUCTION, CIRCUIT_RELEVANCE_EVALUATION_PROMPT
    
    # Intercept the OpenAI API call to capture the exact prompt and response
    original_create = openai.ChatCompletion.create
    
    def create_wrapper(**kwargs):
        # Print the exact prompt going to the model
        print("\n=== EXACT PROMPT SENT TO LLM ===")
        for message in kwargs["messages"]:
            print(f"Role: {message['role']}")
            print(f"Content: {message['content']}")
        print("===========================\n")
        
        # Call the original API
        response = original_create(**kwargs)
        
        # Print the exact raw response from the model
        print("\n=== EXACT RAW RESPONSE FROM LLM ===")
        raw_response = response.choices[0].message.content.strip()
        print(raw_response)
        print("===========================\n")
        
        # Store the raw response
        result["raw_evaluation"] = raw_response
        
        return response
    
    # Replace the API method temporarily
    openai.ChatCompletion.create = create_wrapper
    
    try:
        # Show the exact evaluation prompt that will be used
        exact_prompt = f"{GENERAL_INSTRUCTION}\n\n{CIRCUIT_RELEVANCE_EVALUATION_PROMPT.format(prompt=prompt)}"
        print("\n=== EVALUATION PROMPT TEMPLATE ===")
        print(exact_prompt)
        print("===========================\n")
        
        # Evaluate if the request is circuit related
        is_circuit_related = request_evaluator.is_circuit_related(prompt)
        
        # Store results
        result["is_circuit_related"] = is_circuit_related
        
        print(f"\nFinal evaluation result: {is_circuit_related}")
        print(f"Circuit-related: {'Yes' if is_circuit_related else 'No'}")
        
    except Exception as e:
        print(f"Error during evaluation: {str(e)}")
        result["error"] = str(e)
    finally:
        # Restore original method
        openai.ChatCompletion.create = original_create
    
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