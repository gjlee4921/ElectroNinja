import logging
from electroninja.llm.providers.base import LLMProvider

logger = logging.getLogger('electroninja')

class ChatResponseGenerator:
    """
    Generates chat responses for the user based on their requests.
    This handles both circuit-related and non-circuit-related responses.
    """

    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize the chat response generator.
        
        Args:
            llm_provider (LLMProvider): The LLM provider to use for generating responses
        """
        self.llm_provider = llm_provider
        self.logger = logger

    def generate_response(self, prompt: str, is_circuit_related: bool) -> str:
        """
        Generate an appropriate chat response based on the prompt and whether
        it's related to circuits or not.
        
        Args:
            prompt (str): User prompt
            is_circuit_related (bool): Whether the prompt is related to circuits
            
        Returns:
            str: Generated chat response
        """
        try:
            self.logger.info(f"Generating chat response for prompt: '{prompt}', circuit-related: {is_circuit_related}")
            
            # Generate the chat response using the LLM provider
            chat_response = self.llm_provider.generate_chat_response(prompt)
            
            self.logger.info("Chat response generated successfully")
            return chat_response
            
        except Exception as e:
            error_msg = f"Error generating chat response: {str(e)}"
            self.logger.error(error_msg)
            
            # Provide a fallback response
            if is_circuit_related:
                return "I'll design a circuit for you. Please give me a moment to process your request."
            else:
                return "I'm sorry, but I'm an electrical engineering assistant and can only help with circuit design requests."
                
    def generate_feedback_response(self, vision_feedback: str) -> str:
        """
        Generate a user-friendly response based on vision model feedback.
        
        Args:
            vision_feedback (str): Feedback from vision model about the circuit
            
        Returns:
            str: User-friendly response about circuit status
        """
        try:
            self.logger.info("Generating vision feedback response")
            
            # Generate the response using the LLM provider
            feedback_response = self.llm_provider.generate_vision_feedback_response(vision_feedback)
            
            self.logger.info("Vision feedback response generated successfully")
            return feedback_response
            
        except Exception as e:
            error_msg = f"Error generating vision feedback response: {str(e)}"
            self.logger.error(error_msg)
            
            # Provide a fallback response
            if vision_feedback.strip() == 'Y':
                return "Your circuit is complete and meets the requirements. Feel free to ask if you'd like any modifications."
            else:
                return "I identified some issues with the circuit and I'm working to fix them. I'll have an improved version shortly."