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
    """OpenAI implementation of LLM provider containing all LLM functionalities."""
    
    def __init__(self, config=None):
        self.config = config or Config()
        openai.api_key = self.config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.asc_gen_model = self.config.ASC_MODEL
        self.chat_model = self.config.CHAT_MODEL
        self.evaluation_model = self.config.CHAT_MODEL  # Using same model for evaluation
        self.logger = logger        
    
    def evaluate_circuit_request(self, prompt):
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
            return False
    
    def extract_clean_asc_code(self, asc_code):
        if "Version 4" in asc_code:
            idx = asc_code.find("Version 4")
            return asc_code[idx:].strip()
        return asc_code.strip()
    
    def generate_asc_code(self, prompt, examples=None):
        if not self.evaluate_circuit_request(prompt):
            self.logger.info(f"Request not circuit-related (model evaluation): {prompt}")
            return "N"
        self.logger.info(f"Generating ASC code for request: {prompt}")
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
            asc_code = response.choices[0].message.content.strip()
            if asc_code.upper() == "N":
                return "N"
            else:
                return self.extract_clean_asc_code(asc_code)
        except Exception as e:
            self.logger.error(f"Error generating ASC code: {str(e)}")
            return "Error: Failed to generate circuit"
    
    def _build_prompt(self, request, examples=None):
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
    
    def generate_chat_response(self, prompt):
        try:
            is_circuit_related = self.evaluate_circuit_request(prompt)
            if is_circuit_related:
                chat_prompt = f"{GENERAL_INSTRUCTION}\n{CIRCUIT_CHAT_PROMPT.format(prompt=prompt)}"
            else:
                chat_prompt = f"{GENERAL_INSTRUCTION}\n{NON_CIRCUIT_CHAT_PROMPT.format(prompt=prompt)}"
            logger.info(f"Generating chat response for prompt: {prompt}")
            response = openai.ChatCompletion.create(
                model=self.chat_model,
                messages=[{"role": "user", "content": chat_prompt}]
            )
            chat_response = response.choices[0].message.content.strip()
            return chat_response
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
    
    def generate_vision_feedback_response(self, vision_feedback):
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
            if vision_feedback.strip() == 'Y':
                return "Your circuit is complete and meets the requirements. Feel free to ask if you'd like any modifications."
            else:
                return "I identified some issues with the circuit and I'm working to fix them. I'll have an improved version shortly."
    
    def refine_asc_code(self, request, history):
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
                messages=[{"role": "system", "content": GENERAL_INSTRUCTION},
                          {"role": "user", "content": prompt}]
            )
            refined_asc = response.choices[0].message.content.strip()
            return refined_asc
        except Exception as e:
            logger.error(f"Error refining ASC code: {str(e)}")
    
    def analyze_vision_feedback(self, history, feedback, iteration):
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
            status_update = response.choices[0].message.content.strip()
            return status_update
        except Exception as e:
            logger.error(f"Error generating status update: {str(e)}")
