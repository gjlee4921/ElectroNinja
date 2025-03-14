# tests/test_circuit_chat_response.py
import os
import sys
import logging
import openai
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.llm.prompts.circuit_prompts import GENERAL_INSTRUCTION
from electroninja.llm.prompts.chat_prompts import (
    CIRCUIT_CHAT_PROMPT,
    NON_CIRCUIT_CHAT_PROMPT
)

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_circuit_chat_response(prompt, is_circuit_related):
    """
    Test generating chat responses for user requests based on whether the request 
    is circuit-related or not (without performing evaluation).
    
    Args:
        prompt (str): User prompt
        is_circuit_related (bool): Whether the prompt is related to circuits
    
    Returns:
        dict: Dictionary with chat response results
    """
    # Initialize components
    config = Config()
    llm_provider = OpenAIProvider(config)
    
    # Initialize result dictionary
    result = {
        "prompt": prompt,
        "is_circuit_related": is_circuit_related,
        "chat_response": ""
    }
    
    print("\n====== TEST: CIRCUIT CHAT RESPONSE ======\n")
    print(f"Processing prompt: '{prompt}'")
    print(f"Circuit-related: {'Yes' if is_circuit_related else 'No'}")
    
    # Generate appropriate chat prompt based on circuit relevance
    if is_circuit_related:
        chat_prompt = f"{GENERAL_INSTRUCTION}\n{CIRCUIT_CHAT_PROMPT.format(prompt=prompt)}"
        print("\nUsing CIRCUIT_CHAT_PROMPT for circuit-related request")
    else:
        chat_prompt = f"{GENERAL_INSTRUCTION}\n{NON_CIRCUIT_CHAT_PROMPT.format(prompt=prompt)}"
        print("\nUsing NON_CIRCUIT_CHAT_PROMPT for non-circuit-related request")
    
    print("\n=== PROMPT SENT TO gpt-4o-mini ===")
    print(chat_prompt)
    print("\n===========================\n")
    
    # Generate chat response
    try:
        response = openai.ChatCompletion.create(
            model=llm_provider.chat_model,
            messages=[{"role": "user", "content": chat_prompt}]
        )
        
        # Extract and store response
        chat_response = response.choices[0].message.content.strip()
        result["chat_response"] = chat_response
        
        print("=== RESPONSE FROM gpt-4o-mini ===")
        print(chat_response)
        print("\n===========================\n")

        
    except Exception as e:
        print(f"Error generating chat response: {str(e)}")
        result["error"] = str(e)
    
    return result

if __name__ == "__main__":
    # Sample prompts to test
    circuit_prompts = [
        "Create a circuit with two resistors in parallel"
    ]
    
    non_circuit_prompts = [
        "Tell me about World War 2"
    ]
    
    # Test circuit-related prompts
    print("\n\n=== TESTING CIRCUIT-RELATED PROMPTS ===\n")
    for prompt in circuit_prompts:
        print(f"\n*** TESTING PROMPT: '{prompt}' ***\n")
        result = test_circuit_chat_response(prompt, is_circuit_related=True)
    
    # Test non-circuit-related prompts
    print("\n\n=== TESTING NON-CIRCUIT-RELATED PROMPTS ===\n")
    for prompt in non_circuit_prompts:
        print(f"\n*** TESTING PROMPT: '{prompt}' ***\n")
        result = test_circuit_chat_response(prompt, is_circuit_related=False)