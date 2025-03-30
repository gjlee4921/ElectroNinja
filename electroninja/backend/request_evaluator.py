import logging
import os
from electroninja.llm.providers.openai import OpenAIProvider

logger = logging.getLogger('electroninja')

class RequestEvaluator:
    """
    Evaluates if a user request is related to electrical circuits using the OpenAI provider.
    Also handles saving and loading of the evaluation components for each prompt.
    """
    def __init__(self, openai_provider: OpenAIProvider):
        self.provider = openai_provider
        self.logger = logger

    def evaluate_request(self, prompt: str, prompt_id: int) -> str:
        """
        Evaluates the request and saves the evaluation result (component letters) to a file if relevant.
        If the evaluation result is 'N', nothing is saved.
        
        Args:
            prompt (str): The user request.
            prompt_id (int): The current prompt/session identifier.
        
        Returns:
            str: The raw evaluation result (either 'N' or the component letters).
        """
        self.logger.info(f"Evaluating if request is circuit-related: '{prompt}'")
        print(f"\n{'='*80}\nEVALUATOR PROMPT INPUT:\n{'='*80}\n{prompt}\n{'='*80}")
        
        # Get the evaluation result from the provider.
        result = self.provider.evaluate_circuit_request(prompt)
        
        print(f"\n{'='*80}\nEVALUATOR RESULT OUTPUT:\n{'='*80}\n{result}\n{'='*80}")
        self.logger.info(f"Evaluation result for '{prompt}': {result}")

        # If the result is not 'N', save the component letters.
        if result.strip().upper() != 'N':
            self.save_components(result, prompt_id)
            
        return result

    def save_components(self, components: str, prompt_id: int) -> str:
        """
        Saves the evaluation result (components) to a file in the output/prompt{prompt_id} directory.
        Only saves if the evaluation result is not 'N'.
        
        Args:
            components (str): The evaluation output (e.g., "R, C").
            prompt_id (int): The current prompt/session identifier.
        
        Returns:
            str: The file path to the saved components file.
        """
        if components.strip().upper() == 'N':
            self.logger.info("Evaluation result is 'N'; no components to save.")
            return None
        
        output_dir = os.path.join("data", "output", f"prompt{prompt_id}")
        os.makedirs(output_dir, exist_ok=True)
        
        comp_path = os.path.join(output_dir, "components.txt")
        with open(comp_path, "w", encoding="utf-8") as f:
            f.write(components)
            
        self.logger.info(f"Saved components to: {comp_path}")
        return comp_path

    def load_components(self, prompt_id: int) -> str:
        """
        Loads the evaluation result (components) from the file in output/prompt{prompt_id}/components.txt.
        
        Args:
            prompt_id (int): The prompt/session identifier.
        
        Returns:
            str: The loaded component letters, or None if the file doesn't exist.
        """
        comp_path = os.path.join("data", "output", f"prompt{prompt_id}", "components.txt")
        if not os.path.exists(comp_path):
            self.logger.info(f"No components file found at: {comp_path}")
            return None
        try:
            with open(comp_path, "r", encoding="utf-8") as f:
                components = f.read()
            self.logger.info(f"Loaded components from: {comp_path}")
            return components
        except Exception as e:
            self.logger.error(f"Error loading components: {str(e)}")
            return None
