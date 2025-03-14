# tests/test_asc_generation_with_rag.py
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
from electroninja.llm.prompts.circuit_prompts import (
    GENERAL_INSTRUCTION,
    SAFETY_FOR_AGENT,
    RAG_ASC_GENERATION_PROMPT
)

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_clean_asc_code(asc_code):
    """
    Extract only the pure ASC code starting from 'Version 4'
    This ensures we don't include descriptions in the ASC code examples
    """
    if "Version 4" in asc_code:
        idx = asc_code.find("Version 4")
        return asc_code[idx:].strip()
    return asc_code.strip()

def test_asc_generation_with_rag(prompt):
    """
    Test ASC code generation using RAG (Retrieval Augmented Generation)
    
    Args:
        prompt (str): User prompt for circuit design
        
    Returns:
        dict: Dictionary with generation results
    """
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
    
    print("\n====== TEST: ASC GENERATION WITH RAG ======\n")
    
    # Load vector store
    print("Loading vector store...")
    vector_store.load()
    print("Vector store loaded successfully")
    
    # Fetch examples from vector database
    print("Fetching similar examples from vector DB...")
    examples = vector_store.search(prompt)
    
    result["num_examples"] = len(examples)
    print(f"Found {len(examples)} similar examples")
    
    # Process examples for the prompt
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
        
        # Ensure we only have the clean ASC code without descriptions
        asc_code = extract_clean_asc_code(asc_code)
        
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
    
    # Construct o3-mini prompt
    system_prompt = f"{GENERAL_INSTRUCTION}\n\n{SAFETY_FOR_AGENT}"
    
    user_prompt = (
        "Below are examples of circuits similar to the user's request:\n\n"
        f"{examples_text}"
        f"User's request: {prompt}\n\n"
        f"{RAG_ASC_GENERATION_PROMPT}"
    )
    
    print("=== SYSTEM PROMPT SENT TO o3-mini ===")
    print(system_prompt)
    print("\n===========================\n")
    
    print("=== USER PROMPT SENT TO o3-mini ===")
    print(user_prompt)
    print("\n===========================\n")
    
    # Generate ASC code from o3-mini
    try:
        response = openai.ChatCompletion.create(
            model=llm_provider.asc_gen_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract and process response
        asc_response = response.choices[0].message.content.strip()
        
        # Clean the ASC code if needed
        if asc_response.upper() != "N":
            asc_response = extract_clean_asc_code(asc_response)
        
        result["asc_code"] = asc_response
        
        print("=== RESPONSE FROM o3-mini ===")
        print(asc_response)
        print("\n===========================\n")
        
        # Check if the ASC code looks valid
        if "Version 4" in asc_response:
            print("✅ Valid ASC code detected")
        elif asc_response.upper() == "N":
            print("⚠️ Model responded with 'N' - indicating not a circuit request")
        else:
            print("⚠️ Response may not be valid ASC code")
        
    except Exception as e:
        print(f"Error generating ASC code: {str(e)}")
        result["error"] = str(e)
    
    return result

if __name__ == "__main__":
    # Sample circuit prompts to test
    prompts = [
        "Create a circuit with two resistors in parallel",
        "Design a simple RC low-pass filter"
    ]
    
    # Test each prompt
    for prompt in prompts:
        print(f"\n\n*** TESTING PROMPT: '{prompt}' ***\n")
        result = test_asc_generation_with_rag(prompt)