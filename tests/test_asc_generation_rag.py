# tests/new_test_asc_generation_rag.py
import os
import sys
import logging
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

def test_asc_generation_with_rag(prompt):
    """
    Test ASC code generation using RAG (Retrieval Augmented Generation)
    
    Args:
        prompt (str): User prompt for circuit design
        
    Returns:
        dict: Dictionary with generation results
    """
    print("\n====== TEST: ASC GENERATION WITH RAG ======\n")
    print(f"Processing prompt: '{prompt}'")
    
    # Initialize components
    config = Config()
    llm_provider = OpenAIProvider(config)
    vector_store = VectorStore(config)
    
    # Initialize result dictionary
    result = {
        "prompt": prompt,
        "asc_code": "",
        "num_examples": 0,
        "examples": []
    }
    
    # Load vector store
    print("Loading vector store...")
    vector_store.load()
    print("Vector store loaded successfully")
    
    # Create circuit generator
    circuit_generator = CircuitGenerator(llm_provider, vector_store)
    
    # Get prompt templates
    from electroninja.llm.prompts.circuit_prompts import GENERAL_INSTRUCTION, SAFETY_FOR_AGENT, RAG_ASC_GENERATION_PROMPT
    
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
    
    try:
        # Fetch examples from vector database
        examples = vector_store.search(prompt)
        result["num_examples"] = len(examples)
        print(f"Found {len(examples)} similar examples")
        
        # Process examples for display
        examples_text = ""
        for i, example in enumerate(examples, start=1):
            # Get description from metadata
            desc = example.get("metadata", {}).get("description", "No description")
            
            # Get ASC code, preferring pure_asc_code if available
            if "metadata" in example and "pure_asc_code" in example["metadata"]:
                asc_code = example["metadata"]["pure_asc_code"]
            else:
                # Fall back to asc_code field
                asc_code = example.get("asc_code", "")
            
            # Clean the ASC code
            asc_code = circuit_generator.extract_clean_asc_code(asc_code)
            
            # Store for result
            result["examples"].append({
                "description": desc,
                "asc_code": asc_code
            })
            
            # Format with clear separation for the prompt
            examples_text += (
                f"Example {i}:\n"
                f"Description: {desc}\n"
                f"ASC Code:\n"
                f"-----------------\n"
                f"{asc_code}\n"
                f"-----------------\n\n"
            )
        
        # Show the prompt template that would be used
        print("\n=== RAG PROMPT TEMPLATE THAT WILL BE USED ===")
        system_prompt = f"{GENERAL_INSTRUCTION}\n\n{SAFETY_FOR_AGENT}"
        print(f"System prompt: {system_prompt}")
        
        user_prompt = (
            "Below are examples of circuits similar to the user's request:\n\n"
            f"{examples_text}"
            f"User's request: {prompt}\n\n"
            f"{RAG_ASC_GENERATION_PROMPT}"
        )
        print(f"User prompt: {user_prompt}")
        print("===========================\n")
        
        # Generate ASC code using circuit generator
        asc_code = circuit_generator.generate_asc_code(prompt)
        result["asc_code"] = asc_code
        
        print("\n=== FINAL ASC CODE ===")
        print(asc_code)
        
        # Check if the ASC code looks valid
        if asc_code.startswith("Version 4"):
            print("✅ Valid ASC code detected")
            valid = circuit_generator.validate_asc_code(asc_code)
            print(f"Validation result: {'✅ Valid' if valid else '❌ Invalid'}")
        elif asc_code == "N":
            print("⚠️ Model responded with 'N' - indicating not a circuit request")
        else:
            print("⚠️ Response may not be valid ASC code")
        
    except Exception as e:
        print(f"Error generating ASC code: {str(e)}")
        result["error"] = str(e)
    finally:
        # Restore original method
        openai.ChatCompletion.create = original_create
    
    return result

if __name__ == "__main__":
    # Sample circuit prompts to test
    prompts = [
        "Create a circuit with a battery and two resistances in parallel"
    ]
    
    # Test each prompt
    for prompt in prompts:
        print(f"\n\n*** TESTING PROMPT: '{prompt}' ***\n")
        result = test_asc_generation_with_rag(prompt)