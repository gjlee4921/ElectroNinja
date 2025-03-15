import logging
from electroninja.llm.providers.openai import OpenAIProvider

logger = logging.getLogger('electroninja')

class ChatResponseGenerator:
    """
    Generates chat responses for the user using the OpenAI provider.
    """
    def __init__(self, openai_provider: OpenAIProvider):
        self.provider = openai_provider
        self.logger = logger

    def generate_response(self, prompt: str, is_circuit_related: bool) -> str:
        self.logger.info(f"Generating chat response for prompt: '{prompt}', circuit-related: {is_circuit_related}")
        # Delegates to the provider's method.
        return self.provider.generate_chat_response(prompt)

    def generate_feedback_response(self, vision_feedback: str) -> str:
        self.logger.info("Generating vision feedback response")
        # Delegates to the provider's method.
        return self.provider.generate_vision_feedback_response(vision_feedback)
