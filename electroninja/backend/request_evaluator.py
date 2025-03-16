import logging
from electroninja.llm.providers.openai import OpenAIProvider

logger = logging.getLogger('electroninja')

class RequestEvaluator:
    """
    Evaluates if a user request is related to electrical circuits using the OpenAI provider.
    """
    def __init__(self, openai_provider: OpenAIProvider):
        self.provider = openai_provider
        self.logger = logger

    def is_circuit_related(self, prompt: str) -> bool:
        self.logger.info(f"Evaluating if request is circuit-related: '{prompt}'")
        
        # Print the input prompt
        print(f"\n{'='*80}\nEVALUATOR PROMPT INPUT:\n{'='*80}\n{prompt}\n{'='*80}")
        
        # Get the evaluation result
        result = self.provider.evaluate_circuit_request(prompt)
        
        # Print the evaluation result
        print(f"\n{'='*80}\nEVALUATOR RESULT OUTPUT:\n{'='*80}\n{result}\n{'='*80}")
        
        self.logger.info(f"Evaluation result for '{prompt}': {result}")
        return result