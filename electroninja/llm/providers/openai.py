import os
import openai
import logging
from electroninja.config.settings import Config
from electroninja.llm.providers.base import LLMProvider
from electroninja.llm.prompts.circuit_prompts import (
    ASC_SYSTEM_PROMPT,
    REFINEMENT_PROMPT_TEMPLATE,
    CIRCUIT_RELEVANCE_EVALUATION_PROMPT,
    RAG_ASC_GENERATION_PROMPT,
    MERGING_PROMPT
)
from electroninja.llm.prompts.chat_prompts import (
    CIRCUIT_CHAT_PROMPT,
    VISION_FEEDBACK_PROMPT
)

logger = logging.getLogger('electroninja')

class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLM provider containing all LLM functionalities."""
    
    def __init__(self, config=None):
        self.config = config or Config()
        openai.api_key = self.config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.asc_gen_model = self.config.ASC_MODEL
        self.chat_model = self.config.CHAT_MODEL
        self.evaluation_model = self.config.EVALUATION_MODEL  
        self.merger_model = self.config.MERGER_MODEL
        self.logger = logger        
    
    def evaluate_circuit_request(self, prompt: str) -> bool:
        try:
            evaluation_prompt = f"{CIRCUIT_RELEVANCE_EVALUATION_PROMPT.format(prompt=prompt)}"
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
            return False
    
    def extract_clean_asc_code(self, asc_code: str) -> str:
        if "Version 4" in asc_code:
            idx = asc_code.find("Version 4")
            return asc_code[idx:].strip()
        return asc_code.strip()
    
    def generate_asc_code(self, prompt: str, examples=None) -> str:
        self.logger.info(f"Generating ASC code for request: {prompt}")
        system_prompt = f"{ASC_SYSTEM_PROMPT}"
        user_prompt = self._build_prompt(prompt, examples)
        try:
            response = openai.ChatCompletion.create(
                model=self.asc_gen_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
            )
            asc_code = response.choices[0].message.content.strip()
            if asc_code.upper() == "N":
                return "N"
            else:
                return self.extract_clean_asc_code(asc_code)
        except Exception as e:
            self.logger.error(f"Error generating ASC code: {str(e)}")
            return "Error: Failed to generate circuit"
    
    def _build_prompt(self, request: str, examples=None) -> str:
        if not examples or len(examples) == 0:
            return f"User's request: {request}\n\n{RAG_ASC_GENERATION_PROMPT}"
        examples_text = ""
        for i, example in enumerate(examples, start=1):
            desc = example.get("metadata", {}).get("description", "No description")
            if "metadata" in example and "pure_asc_code" in example["metadata"]:
                asc_code = example["metadata"]["pure_asc_code"]
            else:
                asc_code = example.get("asc_code", "")
            asc_code = self.extract_clean_asc_code(asc_code)
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
    
    def generate_chat_response(self, prompt: str) -> str:
        try:
            chat_prompt = f"{CIRCUIT_CHAT_PROMPT.format(prompt=prompt)}"
            logger.info(f"Generating chat response for prompt: {prompt}")
            response = openai.ChatCompletion.create(
                model=self.chat_model,
                messages=[{"role": "user", "content": chat_prompt}]
            )
            chat_response = response.choices[0].message.content.strip()
            return chat_response
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return "Error generating chat response"
    
    def generate_vision_feedback_response(self, vision_feedback: str) -> str:
        try:
            is_success = vision_feedback.strip() == 'Y'
            prompt = VISION_FEEDBACK_PROMPT.format(
                vision_feedback=vision_feedback
            )
            logger.info(f"Generating vision feedback response (success={is_success})")
            response = openai.ChatCompletion.create(
                model=self.chat_model,
                messages=[{"role": "user", "content": prompt}]
            )
            feedback_response = response.choices[0].message.content.strip()
            return feedback_response
        except Exception as e:
            logger.error(f"Error generating vision feedback response: {str(e)}")
            return "Error generating vision feedback response"
    
    def refine_asc_code(self, request: str, history: list) -> str:
        try:
            prompt = "Below are previous attempts and feedback:\n\n"
            for item in history:
                if "asc_code" in item:
                    prompt += f"Attempt {item.get('attempt', item.get('iteration', '?'))} ASC code:\n{item['asc_code']}\n\n"
                if "vision_feedback" in item:
                    prompt += f"Vision feedback (Iteration {item.get('iteration','?')}): {item['vision_feedback']}\n\n"
            prompt += f"Original user's request: {request}\n\n"
            prompt += REFINEMENT_PROMPT_TEMPLATE
            logger.info(f"Refining ASC code based on feedback")
            response = openai.ChatCompletion.create(
                model=self.asc_gen_model,
                messages=[{"role": "system", "content": ASC_SYSTEM_PROMPT},
                          {"role": "user", "content": prompt}]
            )
            refined_asc = response.choices[0].message.content.strip()
            return refined_asc
        except Exception as e:
            logger.error(f"Error refining ASC code: {str(e)}")
            return "Error refining ASC code"
    
    def merge_requests(self, request_dict: dict) -> str:
        """
        Merge multiple circuit requests into one final request using the MERGING_PROMPT.
        The request_dict should be of the form:
        {"request1": "initial prompt", "request2": "follow-up", ...}
        """
        initial = request_dict['request1']
        # Gather follow-ups in order
        follow_ups = "\n".join(
            request_dict[key] for key in sorted(request_dict.keys()) if key != "request1"
        )
        merging_prompt = MERGING_PROMPT.format(request1=initial, follow_ups=follow_ups)
        self.logger.info("Merging requests using prompt: " + merging_prompt)
        try:
            response = openai.ChatCompletion.create(
                model=self.merger_model,
                messages=[{"role": "user", "content": merging_prompt}]
            )
            merged_response = response.choices[0].message.content.strip()
            return merged_response
        except Exception as e:
            self.logger.error("Error merging requests: " + str(e))
            return initial