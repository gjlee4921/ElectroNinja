import logging
from typing import List, Dict, Any, Optional, Tuple
from electroninja.llm.providers.base import LLMProvider
from electroninja.llm.vector_store import VectorStore

logger = logging.getLogger('electroninja')

class CircuitGenerator:
    """
    Generates and refines ASC code for circuit designs.
    Uses RAG for initial generation and can refine based on feedback.
    """

    def __init__(self, llm_provider: LLMProvider, vector_store: VectorStore):
        """
        Initialize the circuit generator.
        
        Args:
            llm_provider (LLMProvider): The LLM provider to use for generating circuits
            vector_store (VectorStore): The vector store for retrieving similar examples
        """
        self.llm_provider = llm_provider
        self.vector_store = vector_store
        self.logger = logger

    def extract_clean_asc_code(self, asc_code: str) -> str:
        """
        Extract only the pure ASC code starting from 'Version 4'.
        This ensures we don't include descriptions in the ASC code.
        
        Args:
            asc_code (str): Raw ASC code which may include descriptions
            
        Returns:
            str: Clean ASC code
        """
        if "Version 4" in asc_code:
            idx = asc_code.find("Version 4")
            return asc_code[idx:].strip()
        return asc_code.strip()

    def generate_asc_code(self, prompt: str) -> str:
        """
        Generate ASC code based on user prompt using RAG.
        
        Args:
            prompt (str): User prompt for a circuit design
            
        Returns:
            str: Generated ASC code, or "N" if not circuit-related
        """
        try:
            self.logger.info(f"Generating ASC code for request: '{prompt}'")
            
            # Fetch similar examples from vector database
            examples = self.vector_store.search(prompt)
            self.logger.info(f"Found {len(examples)} similar examples for RAG")
            
            # Generate ASC code using the LLM provider with examples
            asc_code = self.llm_provider.generate_asc_code(prompt, examples)
            
            # If the model returns "N", it means the request is not circuit-related
            if asc_code == "N":
                self.logger.info(f"Model determined request is not circuit-related: '{prompt}'")
                return "N"
                
            # Clean the ASC code
            clean_asc = self.extract_clean_asc_code(asc_code)
            
            # Simple check to ensure it starts with Version 4
            if not clean_asc.startswith("Version 4"):
                self.logger.warning("ASC code does not start with 'Version 4', adding it")
                clean_asc = "Version 4\nSHEET 1 880 680\n" + clean_asc
                
            self.logger.info("ASC code generated successfully")
            return clean_asc
            
        except Exception as e:
            error_msg = f"Error generating ASC code: {str(e)}"
            self.logger.error(error_msg)
            return f"Error: {error_msg}"

    def refine_asc_code(self, original_request: str, history: List[Dict[str, Any]]) -> str:
        """
        Refine ASC code based on vision feedback and conversation history.
        
        Args:
            original_request (str): Original user request
            history (List[Dict]): Conversation history including previous ASC code and feedback
            
        Returns:
            str: Refined ASC code
        """
        try:
            self.logger.info(f"Refining ASC code for request: '{original_request}'")
            
            # Refine the ASC code using the LLM provider
            refined_asc = self.llm_provider.refine_asc_code(original_request, history)
            
            # Clean the refined ASC code
            clean_asc = self.extract_clean_asc_code(refined_asc)
            
            # Simple check to ensure it starts with Version 4
            if not clean_asc.startswith("Version 4"):
                self.logger.warning("Refined ASC code does not start with 'Version 4', adding it")
                clean_asc = "Version 4\nSHEET 1 880 680\n" + clean_asc
                
            self.logger.info("ASC code refined successfully")
            return clean_asc
            
        except Exception as e:
            error_msg = f"Error refining ASC code: {str(e)}"
            self.logger.error(error_msg)
            return f"Error: {error_msg}"