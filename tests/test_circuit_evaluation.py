import os
import sys
import logging
import openai
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.backend.request_evaluator import RequestEvaluator

load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_circuit_evaluation(prompt):
    """Test circuit relevance evaluation with LLM I/O printed"""
    print("\n====== TEST: CIRCUIT RELEVANCE EVALUATION ======")
    print(f"Evaluating prompt: '{prompt}'")
    
    config = Config()
    llm_provider = OpenAIProvider(config)
    request_evaluator = RequestEvaluator(llm_provider)
    
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
        is_circuit_related = request_evaluator.is_circuit_related(prompt)
        print("\n=== EVALUATION RESULT ===")
        print(f"Circuit-related: {'Yes' if is_circuit_related else 'No'}")
    finally:
        openai.ChatCompletion.create = original_create

    return is_circuit_related

if __name__ == "__main__":
    prompts = [
        "Create a circuit with two resistors in parallel",
        "Design a simple RC low-pass filter",
        "Tell me about World War 2",
    ]
    for prompt in prompts:
        print(f"\n*** TESTING PROMPT: '{prompt}' ***")
        test_circuit_evaluation(prompt)
