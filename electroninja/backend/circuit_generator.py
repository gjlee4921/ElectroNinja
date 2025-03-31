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

    def generate_asc_code(self, description: str, prompt_id: int) -> str:
        """
        Generates ASC code by retrieving examples, building a comprehensive prompt (with instructions),
        and then asking the provider to generate the code.
        """
        self.logger.info(f"Generating ASC code for circuit description: '{description}'")
        
        # Retrieve similar examples from the vector store using the description
        examples = self.vector_store.search(description, top_k=3)
        
        # Print input details (for debugging)
        print(f"\n{'='*80}\nCIRCUIT GENERATOR PROMPT INPUT:\n{'='*80}")
        print(f"Circuit description: {description}")
        print(f"Examples retrieved: {len(examples)}")
        for i, example in enumerate(examples):
            print(f"Example {i+1} metadata: {example.get('metadata', {})}")
            asc_code = example.get('asc_code', '')
            if asc_code:
                print(f"Example {i+1} ASC code (first 50 chars): {asc_code[:50]}...")
        print('='*80)

        # Generate ASC code using the provider, passing prompt_id to load components/instructions.
        asc_code = self.provider.generate_asc_code(description, examples, prompt_id)
        clean_asc = self.provider.extract_clean_asc_code(asc_code)
        final_asc = self._ensure_header(clean_asc)
        
        # Print output details (for debugging)
        print(f"\n{'='*80}\nCIRCUIT GENERATOR OUTPUT:\n{'='*80}")
        print(f"Original output length: {len(asc_code)} chars")
        print(f"Clean ASC code length: {len(clean_asc)} chars")
        print(f"Final ASC code (first 100 chars):\n{final_asc[:100]}...")
        print('='*80)
        
        self.logger.info("ASC code generated successfully")
        return final_asc

    # The refine_asc_code method remains unchanged.


    def refine_asc_code(self, description: str, history: List[Dict[str, Any]]) -> str:
        self.logger.info(f"Refining ASC code for circuit description: '{description}'")
        
        print(f"\n{'='*80}\nCIRCUIT REFINER PROMPT INPUT:\n{'='*80}")
        print(f"Circuit description: {description}")
        print(f"History entries: {len(history)}")
        for i, entry in enumerate(history):
            print(f"Entry {i}: iteration={entry.get('iteration')}")
            feedback = entry.get('vision_feedback', '')
            if feedback:
                if len(feedback) > 50:
                    print(f"  Feedback (first 50 chars): {feedback[:50]}...")
                else:
                    print(f"  Feedback: {feedback}")
            asc_code = entry.get('asc_code', '')
            if asc_code:
                print(f"  ASC code length: {len(asc_code)} chars")
        print('='*80)
        
        refined_asc = self.provider.refine_asc_code(description, history)
        clean_asc = self.provider.extract_clean_asc_code(refined_asc)
        final_asc = self._ensure_header(clean_asc)
        
        print(f"\n{'='*80}\nCIRCUIT REFINER OUTPUT:\n{'='*80}")
        print(f"Original output length: {len(refined_asc)} chars")
        print(f"Clean ASC code length: {len(clean_asc)} chars")
        print(f"Final ASC code (first 100 chars):\n{final_asc[:100]}...")
        print('='*80)
        
        self.logger.info("ASC code refined successfully")
        return final_asc
