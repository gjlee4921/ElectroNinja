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
    DESCRIPTION_PROMPT
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
        self.description_model = self.config.DESCRIPTION_MODEL
        self.logger = logger        
        
    def evaluate_circuit_request(self, prompt: str) -> str:
        try:
            # Format the evaluation prompt with the new instructions
            evaluation_prompt = CIRCUIT_RELEVANCE_EVALUATION_PROMPT.format(prompt=prompt)
            logger.info(f"Evaluating if request is circuit-related: {prompt}")
            response = openai.ChatCompletion.create(
                model=self.evaluation_model,
                messages=[{"role": "user", "content": evaluation_prompt}]
            )
            # Return the raw result string: either 'N' or the component letters (e.g., "V, R, C")
            result = response.choices[0].message.content.strip()
            logger.info(f"Evaluation result for '{prompt}': {result}")
            return result
        except Exception as e:
            logger.error(f"Error evaluating request: {str(e)}")
            # In case of error, return "N" as a safe fallback.
            return "N"

        
    def create_description(self, previous_description: str, new_request: str) -> str:
        """
        Merge a current circuit description with a new modification request to a new description.
        
        Args:
            previous_description: The previous circuit description
            new_request: The new modification request from the user
            
        Returns:
            A merged, comprehensive circuit description
        """
        previous_description = previous_description if previous_description is not None else "None"

        description_prompt = DESCRIPTION_PROMPT.format(
            previous_description=previous_description,
            new_request=new_request
        )
        self.logger.info("Generating description using prompt:\n" + description_prompt)
        
        try:
            response = openai.ChatCompletion.create(
                model=self.description_model,
                messages=[{"role": "user", "content": description_prompt}]
            )
            new_description = response.choices[0].message.content.strip()
            
            self.logger.info("Merged result:\n" + new_description)
            
            return new_description
        except Exception as e:
            self.logger.error("Error generating description: " + str(e))
            return new_request
    
    def extract_clean_asc_code(self, asc_code: str) -> str:
        if "Version 4" in asc_code:
            idx = asc_code.find("Version 4")
            return asc_code[idx:].strip()
        return asc_code.strip()

    def generate_asc_code(self, description: str, examples=None) -> str:
        self.logger.info(f"Generating ASC code for circuit description: {description}")
        system_prompt = f"{ASC_SYSTEM_PROMPT}"
        user_prompt = self._build_prompt(description, examples)
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

    def _build_prompt(self, description: str, examples=None) -> str:
        if not examples or len(examples) == 0:
            return f"Circuit description: {description}\n\n{RAG_ASC_GENERATION_PROMPT}"
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
            "Below are examples of circuits similar to the given description:\n\n"
            f"{examples_text}"
            f"Circuit description: {description}\n\n"
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
    
    def refine_asc_code(self, description: str, history: list) -> str:
        try:
            prompt = "Below are previous attempts and feedback:\n\n"
            for item in history:
                if "asc_code" in item:
                    prompt += f"Attempt {item.get('attempt', item.get('iteration', '?'))} ASC code:\n{item['asc_code']}\n\n"
                if "vision_feedback" in item:
                    prompt += f"Vision feedback (Iteration {item.get('iteration','?')}): {item['vision_feedback']}\n\n"
            prompt += f"Original circuit description: {description}\n\n"
            prompt += REFINEMENT_PROMPT_TEMPLATE
            logger.info("Refining ASC code based on feedback")
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
        
