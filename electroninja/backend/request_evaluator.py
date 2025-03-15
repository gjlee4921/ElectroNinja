import logging
from electroninja.llm.providers.base import LLMProvider

logger = logging.getLogger('electroninja')

class RequestEvaluator:
    """
    Evaluates if a user request is related to electrical circuits.
    Acts as the first step in the workflow to determine if we should
    process the request as a circuit design task.
    """

    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize the request evaluator.
        
        Args:
            llm_provider (LLMProvider): The LLM provider to use for evaluation
        """
        self.llm_provider = llm_provider
        self.logger = logger

    def is_circuit_related(self, prompt: str) -> bool:
        """
        Evaluate if a request is related to electrical circuits.
        
        Args:
            prompt (str): User request to evaluate
            
        Returns:
            bool: True if circuit-related, False otherwise
        """
        try:
            self.logger.info(f"Evaluating if request is circuit-related: '{prompt}'")
            
            # Use the LLM provider to evaluate if the request is circuit-related
            is_circuit = self.llm_provider.evaluate_circuit_request(prompt)
            
            self.logger.info(f"Evaluation result for '{prompt}': {is_circuit}")
            return is_circuit
            
        except Exception as e:
            self.logger.error(f"Error evaluating request: {str(e)}")
            return False  # Default to not circuit-related in case of error