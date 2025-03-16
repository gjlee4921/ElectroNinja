import logging
from electroninja.llm.providers.openai import OpenAIProvider

logger = logging.getLogger('electroninja')

class RequestMerger:
    """
    Merges multiple circuit requests into one final request using the OpenAI provider.
    """
    def __init__(self, openai_provider: OpenAIProvider):
        self.provider = openai_provider
        self.logger = logger

    def merge_requests(self, request_dict: dict) -> str:
        """
        Creates the final merged prompt intended for the circuit model.
        This function merges the user requests into one comprehensive prompt.
        """
        # Print the input requests
        print(f"\n{'='*80}\nMERGER PROMPT INPUT:\n{'='*80}")
        for key, value in request_dict.items():
            print(f"{key}: {value}")
        print('='*80)
        
        # Merge the requests
        merged_request = self.provider.merge_requests(request_dict)
        
        # Print the merged result
        print(f"\n{'='*80}\nMERGER RESULT OUTPUT:\n{'='*80}\n{merged_request}\n{'='*80}")
        
        return merged_request