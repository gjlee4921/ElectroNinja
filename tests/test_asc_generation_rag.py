import os
import sys
import logging
import openai
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.llm.vector_store import VectorStore
from electroninja.backend.circuit_generator import CircuitGenerator

# Load environment variables and set up logging
load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_asc_generation_rag():
    prompt = "Create a circuit with a battery and two resistances in parallel"
    print("\n====== TEST: ASC GENERATION WITH RAG ======")
    print(f"Processing prompt: '{prompt}'")
    
    # Initialize configuration and providers
    config = Config()
    provider = OpenAIProvider(config)

    # Initialize vector store and load examples
    vector_store = VectorStore(config)
    vector_store.load()
    
    # Create the CircuitGenerator from the backend
    circuit_generator = CircuitGenerator(provider, vector_store)
    
    # Intercept OpenAI API calls to print raw input and output
    original_create = openai.ChatCompletion.create

    def create_wrapper(**kwargs):
        print("\n=== RAW INPUT TO LLM ===")
        for message in kwargs.get("messages", []):
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
        # Generate ASC code using the provided prompt and relevance flag
        asc_code = circuit_generator.generate_asc_code(prompt)
        print("\n=== FINAL ASC CODE ===")
        print(asc_code)
    finally:
        # Restore the original ChatCompletion.create method
        openai.ChatCompletion.create = original_create

if __name__ == "__main__":
    test_asc_generation_rag()
