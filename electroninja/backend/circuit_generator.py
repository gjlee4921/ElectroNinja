import logging
from typing import List, Dict, Any, Optional, Tuple
from electroninja.llm.providers.base import LLMProvider
from electroninja.llm.vector_store import VectorStore
from electroninja.utils.error_handler import ModelError

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

    def validate_asc_code(self, asc_code: str) -> bool:
        """
        Validate ASC code to ensure it's properly formed.
        
        Args:
            asc_code (str): ASC code to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check for basic structure
        if not asc_code.startswith("Version 4"):
            self.logger.warning("Invalid ASC code: Does not start with 'Version 4'")
            return False
            
        # Check for duplicate FLAG entries
        flag_lines = [line for line in asc_code.splitlines() if line.startswith("FLAG")]
        flag_targets = [line.split()[1:3] for line in flag_lines if len(line.split()) >= 3]
        if len(flag_targets) != len(set(tuple(target) for target in flag_targets)):
            self.logger.warning("Invalid ASC code: Contains duplicate FLAGS")
            return False
            
        # Check for duplicate SYMBOL entries at same coordinates
        symbol_lines = [line for line in asc_code.splitlines() if line.startswith("SYMBOL")]
        symbol_positions = []
        for line in symbol_lines:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    pos = (parts[-2], parts[-1])
                    symbol_type = parts[1]
                    key = (symbol_type, pos)
                    if key in symbol_positions:
                        self.logger.warning(f"Invalid ASC code: Duplicate SYMBOL {symbol_type} at position {pos}")
                        return False
                    symbol_positions.append(key)
                except:
                    pass
                    
        # Ensure there's at least one voltage source
        if not any(line.startswith("SYMBOL voltage") for line in symbol_lines):
            self.logger.warning("Invalid ASC code: No voltage source found")
            return False
            
        return True

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
                
            # Clean and validate the ASC code
            clean_asc = self.extract_clean_asc_code(asc_code)
            
            if not self.validate_asc_code(clean_asc):
                self.logger.warning("Generated ASC code failed validation")
                return "Error: Generated circuit is invalid"
                
            self.logger.info("ASC code generated and validated successfully")
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
            
            # Clean and validate the refined ASC code
            clean_asc = self.extract_clean_asc_code(refined_asc)
            
            if not self.validate_asc_code(clean_asc):
                self.logger.warning("Refined ASC code failed validation")
                return "Error: Refined circuit is invalid"
                
            self.logger.info("ASC code refined and validated successfully")
            return clean_asc
            
        except Exception as e:
            error_msg = f"Error refining ASC code: {str(e)}"
            self.logger.error(error_msg)
            return f"Error: {error_msg}"