import os
import openai
import logging
from electroninja.config.settings import Config
from electroninja.llm.providers.base import LLMProvider
from electroninja.llm.prompts.circuit_prompts import (
    GENERAL_INSTRUCTION,
    SAFETY_FOR_AGENT,
    REFINEMENT_PROMPT_TEMPLATE,
    VISION_ANALYSIS_PROMPT_TEMPLATE,
    CIRCUIT_RELEVANCE_EVALUATION_PROMPT,
    RAG_ASC_GENERATION_PROMPT
)
from electroninja.llm.prompts.chat_prompts import (
    CIRCUIT_CHAT_PROMPT,
    NON_CIRCUIT_CHAT_PROMPT,
    VISION_FEEDBACK_PROMPT
)


logger = logging.getLogger('electroninja')

class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLM provider"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        openai.api_key = self.config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.asc_gen_model = self.config.ASC_MODEL
        self.chat_model = self.config.CHAT_MODEL
        self.evaluation_model = self.config.CHAT_MODEL  # Using same model for evaluation
        self.logger = logger        
    
    def evaluate_circuit_request(self, prompt):
        """
        Evaluate if a request is related to electrical circuits
        
        Args:
            prompt (str): User request to evaluate
            
        Returns:
            bool: True if circuit-related, False otherwise
        """
        try:
            evaluation_prompt = f"{GENERAL_INSTRUCTION}\n\n{CIRCUIT_RELEVANCE_EVALUATION_PROMPT.format(prompt=prompt)}"
            
            logger.info(f"Evaluating if request is circuit-related: {prompt}")
            
            response = openai.ChatCompletion.create(
                model=self.evaluation_model,
                messages=[{"role": "user", "content": evaluation_prompt}]
            )
            
            result = response.choices[0].message.content.strip()
            is_circuit_related = result.upper().startswith('Y')
            
            logger.info(f"Evaluation result for '{prompt}': {is_circuit_related}")
            return is_circuit_related
            
        except Exception as e:
            logger.error(f"Error evaluating request: {str(e)}")
            return False  # Default to not circuit-related in case of error
    
    def extract_clean_asc_code(self, asc_code):
        """
        Extract only the pure ASC code starting from 'Version 4'
        This ensures we don't include descriptions in the ASC code examples
        """
        if "Version 4" in asc_code:
            idx = asc_code.find("Version 4")
            return asc_code[idx:].strip()
        return asc_code.strip()
    
    def generate_asc_code(self, prompt, examples=None):
        """
        Generate ASC code for a circuit based on the user's prompt and optional examples
        
        Args:
            prompt (str): User's circuit request
            examples (list, optional): Similar circuit examples from vector DB
        
        Returns:
            str: Generated ASC code or 'N' if not related to circuits
        """
        # Check if the request is related to circuits using the model
        if not self.evaluate_circuit_request(prompt):
            self.logger.info(f"Request not circuit-related (model evaluation): {prompt}")
            return "N"
        
        self.logger.info(f"Generating ASC code for request: {prompt}")
        
        # Build prompt with examples if provided
        system_prompt = f"{GENERAL_INSTRUCTION}\n\n{SAFETY_FOR_AGENT}"
        user_prompt = self._build_prompt(prompt, examples)
        
        try:
            response = openai.ChatCompletion.create(
                model=self.asc_gen_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
            )
            
            # Extract content
            asc_code = response.choices[0].message.content.strip()
            
            # Post-process to ensure only ASC code is returned
            if asc_code.upper() == "N":
                return "N"
            else:
                # Extract only the ASC code part
                return self.extract_clean_asc_code(asc_code)
                
        except Exception as e:
            self.logger.error(f"Error generating ASC code: {str(e)}")
            return "Error: Failed to generate circuit"
    
    def _build_prompt(self, request, examples=None):
        """Build a prompt with or without examples"""
        if not examples or len(examples) == 0:
            return f"User's request: {request}\n\n{RAG_ASC_GENERATION_PROMPT}"
        
        examples_text = ""
        for i, example in enumerate(examples, start=1):
            # Get description from metadata
            desc = example.get("metadata", {}).get("description", "No description")
            
            # Get ASC code, preferring pure_asc_code if available
            if "metadata" in example and "pure_asc_code" in example["metadata"]:
                asc_code = example["metadata"]["pure_asc_code"]
            else:
                # Fall back to asc_code field
                asc_code = example.get("asc_code", "")
            
            # Clean the ASC code
            asc_code = self.extract_clean_asc_code(asc_code)
            
            # Format with clear separation
            examples_text += (
                f"Example {i}:\n"
                f"Description: {desc}\n"
                f"ASC Code:\n"
                f"-----------------\n"
                f"{asc_code}\n"
                f"-----------------\n\n"
            )
        
        return (
            "Below are examples of circuits similar to the user's request:\n\n"
            f"{examples_text}"
            f"User's request: {request}\n\n"
            f"{RAG_ASC_GENERATION_PROMPT}"
        )
    
    def generate_chat_response(self, prompt):
        """Generate a chat response"""
        try:
            # Use the dedicated model evaluation
            is_circuit_related = self.evaluate_circuit_request(prompt)
            
            if is_circuit_related:
                chat_prompt = f"{GENERAL_INSTRUCTION}\n{CIRCUIT_CHAT_PROMPT.format(prompt=prompt)}"
            else:
                chat_prompt = f"{GENERAL_INSTRUCTION}\n{NON_CIRCUIT_CHAT_PROMPT.format(prompt=prompt)}"
            
            logger.info(f"Generating chat response for prompt: {prompt}")
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.chat_model,
                messages=[{"role": "user", "content": chat_prompt}]
            )
            
            # Extract and return response
            chat_response = response.choices[0].message.content.strip()
            return chat_response
            
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
    
    def generate_vision_feedback_response(self, vision_feedback):
        """
        Generate a user-friendly response based on vision model feedback
        
        Args:
            vision_feedback (str): Feedback from vision model about the circuit
            
        Returns:
            str: User-friendly response about circuit status
        """
        try:
            # Check if vision feedback is exactly 'Y' (success)
            is_success = vision_feedback.strip() == 'Y'
            
            # Build prompt based on feedback
            prompt = VISION_FEEDBACK_PROMPT.format(
                vision_feedback=vision_feedback
            )
            
            logger.info(f"Generating vision feedback response (success={is_success})")
            
            # Call OpenAI API with gpt-4o-mini
            response = openai.ChatCompletion.create(
                model=self.chat_model,  # Should be configured as gpt-4o-mini
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract and return the response
            feedback_response = response.choices[0].message.content.strip()
            return feedback_response
            
        except Exception as e:
            logger.error(f"Error generating vision feedback response: {str(e)}")
            # Provide a default response in case of error
            if vision_feedback.strip() == 'Y':
                return "Your circuit is complete and meets the requirements. Feel free to ask if you'd like any modifications."
            else:
                return "I identified some issues with the circuit and I'm working to fix them. I'll have an improved version shortly."
    
    def refine_asc_code(self, request, history):
        """Refine ASC code based on request and history"""
        try:
            # Build refinement prompt
            prompt = "Below are previous attempts and feedback:\n\n"
            
            for item in history:
                if "asc_code" in item:
                    prompt += f"Attempt {item.get('attempt', item.get('iteration', '?'))} ASC code:\n{item['asc_code']}\n\n"
                    
                if "vision_feedback" in item:
                    prompt += f"Vision feedback (Iteration {item.get('iteration','?')}): {item['vision_feedback']}\n\n"
                    
            prompt += f"Original user's request: {request}\n\n"
            prompt += REFINEMENT_PROMPT_TEMPLATE
            
            logger.info(f"Refining ASC code based on feedback")
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.asc_gen_model,
                messages=[{"role": "system", "content": GENERAL_INSTRUCTION},
                          {"role": "user", "content": prompt}]
            )
            
            # Extract and return refined ASC code
            refined_asc = response.choices[0].message.content.strip()
            return refined_asc
            
        except Exception as e:
            logger.error(f"Error refining ASC code: {str(e)}")
            
    def analyze_vision_feedback(self, history, feedback, iteration):
        """Generate a status update based on vision feedback"""
        try:
            prompt = (
                VISION_ANALYSIS_PROMPT_TEMPLATE +
                "\n\nConversation History:\n"
            )
            
            for item in history:
                prompt += f"{item}\n"
                
            prompt += f"\nLatest Vision Feedback (Iteration {iteration}): {feedback}\n"
            prompt += "Status update:"
            
            logger.info(f"Generating status update for iteration {iteration}")
            
            response = openai.ChatCompletion.create(
                model=self.chat_model,
                messages=[{"role": "user", "content": prompt}],
            )
            
            # Extract and return status update
            status_update = response.choices[0].message.content.strip()
            return status_update
            
        except Exception as e:
            logger.error(f"Error generating status update: {str(e)}")
