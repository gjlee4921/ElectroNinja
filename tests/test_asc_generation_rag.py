import os
import sys
import logging
import openai
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.llm.vector_store import VectorStore
from electroninja.backend.circuit_generator import CircuitGenerator

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_asc_generation_with_rag(prompt):
    """Test ASC code generation using RAG with raw LLM I/O from circuit model only"""
    print("\n====== TEST: ASC GENERATION WITH RAG ======")
    print(f"Processing prompt: '{prompt}'")
    
    # Initialize components
    config = Config()
    llm_provider = OpenAIProvider(config)
    
    # Override the evaluation method to bypass judgement
    llm_provider.evaluate_circuit_request = lambda prompt: True
    
    vector_store = VectorStore(config)
    vector_store.load()
    circuit_generator = CircuitGenerator(llm_provider, vector_store)
    
    # Intercept OpenAI API calls to print LLM input/output
    original_create = openai.ChatCompletion.create

    def create_wrapper(**kwargs):
        print("\n=== RAW INPUT TO LLM ===")
        for message in kwargs["messages"]:
            print(f"Role: {message['role']}")
            print(f"Content:\n{message['content']}")
            print("-" * 50)
        response = original_create(**kwargs)
        print("\n=== RAW OUTPUT FROM LLM ===")
        print(response.choices[0].message.content)
        print("=" * 25)
        return response

    openai.ChatCompletion.create = create_wrapper

    try:
        examples = vector_store.search(prompt)
        print(f"Found {len(examples)} similar examples")
        
        asc_code = circuit_generator.generate_asc_code(prompt)
        print("\n=== FINAL ASC CODE ===")
        print(asc_code)
    finally:
        openai.ChatCompletion.create = original_create
    
    return asc_code

if __name__ == "__main__":
    prompts = ["Create a circuit with a battery and two resistances in parallel"]
    for prompt in prompts:
        print(f"\n*** TESTING PROMPT: '{prompt}' ***")
        test_asc_generation_with_rag(prompt)
