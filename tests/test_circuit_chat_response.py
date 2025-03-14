# tests/new_test_circuit_chat_response.py
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

def test_circuit_chat_response(prompt, is_circuit_related):
    """
    Test generating chat responses for user requests based on whether the request 
    is circuit-related or not.
    
    Args:
        prompt (str): User prompt
        is_circuit_related (bool): Whether the prompt is related to circuits
    
    Returns:
        dict: Dictionary with chat response results
    """
    print("\n====== TEST: CIRCUIT CHAT RESPONSE ======\n")
    print(f"Processing prompt: '{prompt}'")
    print(f"Circuit-related: {'Yes' if is_circuit_related else 'No'}")
    
    # Initialize components
    config = Config()
    llm_provider = OpenAIProvider(config)
    chat_generator = ChatResponseGenerator(llm_provider)
    
    # Initialize result dictionary
    result = {
        "prompt": prompt,
        "is_circuit_related": is_circuit_related,
        "chat_response": ""
    }
    
    # Get prompt templates
    from electroninja.llm.prompts.circuit_prompts import GENERAL_INSTRUCTION
    from electroninja.llm.prompts.chat_prompts import CIRCUIT_CHAT_PROMPT, NON_CIRCUIT_CHAT_PROMPT
    
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
        
        return response
    
    # Replace the API method temporarily
    openai.ChatCompletion.create = create_wrapper
    
    try:
        # Show the prompt template that would be used
        print("\n=== CHAT PROMPT TEMPLATE ===")
        if is_circuit_related:
            exact_prompt = f"{GENERAL_INSTRUCTION}\n{CIRCUIT_CHAT_PROMPT.format(prompt=prompt)}"
            print("Using CIRCUIT_CHAT_PROMPT template:")
        else:
            exact_prompt = f"{GENERAL_INSTRUCTION}\n{NON_CIRCUIT_CHAT_PROMPT.format(prompt=prompt)}"
            print("Using NON_CIRCUIT_CHAT_PROMPT template:")
        print(exact_prompt)
        print("===========================\n")
        
        # Generate chat response
        chat_response = chat_generator.generate_response(prompt, is_circuit_related)
        result["chat_response"] = chat_response
        
        print("\n=== FINAL CHAT RESPONSE ===")
        print(chat_response)
        print("===========================\n")
        
    except Exception as e:
        print(f"Error generating chat response: {str(e)}")
        result["error"] = str(e)
    finally:
        # Restore original method
        openai.ChatCompletion.create = original_create
    
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