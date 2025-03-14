from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def generate_asc_code(self, prompt, examples=None):
        """
        Generate ASC code based on prompt and examples
        
        Args:
            prompt (str): User prompt
            examples (list): Optional examples for RAG
            
        Returns:
            str: ASC code
        """
        pass
        
    @abstractmethod
    def generate_chat_response(self, prompt):
        """
        Generate a chat response
        
        Args:
            prompt (str): User prompt
            
        Returns:
            str: Chat response
        """
        pass
        
    @abstractmethod
    def refine_asc_code(self, request, history):
        """
        Refine ASC code based on request and history
        
        Args:
            request (str): Original user request
            history (list): Conversation history
            
        Returns:
            str: Refined ASC code
        """
        pass
        
    @abstractmethod
    def analyze_vision_feedback(self, history, feedback, iteration):
        """
        Generate a status update based on vision feedback
        
        Args:
            history (list): Conversation history
            feedback (str): Vision feedback
            iteration (int): Current iteration
            
        Returns:
            str: Status update
        """
        pass