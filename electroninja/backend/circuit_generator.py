import logging
from typing import List, Dict, Any
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.llm.vector_store import VectorStore

logger = logging.getLogger('electroninja')

class CircuitGenerator:
    """
    Generates and refines ASC code for circuit designs using the OpenAI provider.
    """
    def __init__(self, openai_provider: OpenAIProvider, vector_store: VectorStore):
        self.provider = openai_provider
        self.vector_store = vector_store
        self.logger = logger

    def _ensure_header(self, asc_code: str) -> str:
        """Ensure the ASC code contains the required header."""
        if not asc_code.startswith("Version 4"):
            asc_code = "Version 4\nSHEET 1 880 680\n" + asc_code
        return asc_code

    def generate_asc_code(self, prompt: str) -> str:
        self.logger.info(f"Generating ASC code for request: '{prompt}'")
        # Retrieve similar examples from the vector store.
        examples = self.vector_store.search(prompt)
        # Use the provided is_circuit_related flag instead of evaluating the prompt here.
        asc_code = self.provider.generate_asc_code(prompt, examples)
        asc_code = self.provider.extract_clean_asc_code(asc_code)
        asc_code = self._ensure_header(asc_code)
        self.logger.info("ASC code generated successfully")
        return asc_code

    def refine_asc_code(self, original_request: str, history: List[Dict[str, Any]]) -> str:
        self.logger.info(f"Refining ASC code for request: '{original_request}'")
        refined_asc = self.provider.refine_asc_code(original_request, history)
        refined_asc = self.provider.extract_clean_asc_code(refined_asc)
        refined_asc = self._ensure_header(refined_asc)
        self.logger.info("ASC code refined successfully")
        return refined_asc
