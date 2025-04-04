import os
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def process_file(file_path):
    result = ""
    # Specify the encoding if needed to avoid UnicodeDecodeError.
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Remove any trailing newline characters and add a new newline.
            result += line.rstrip("\n") + "\n"
    return result

# Prompt fragments
general = (
    process_file(r"backend\\llm\\prompts\\general.txt") + "\n" +
    process_file(r"backend\\llm\\prompts\\resistor.txt") + "\n" +
    # process_file(r"backend\\llm\\prompts\\capacitor.txt") + "\n" +
    process_file(r"backend\\llm\\prompts\\voltage_source.txt") #+ "\n" +
    # process_file(r"backend\\llm\\prompts\\diode.txt") + "\n" +
    # process_file(r"backend\\llm\\prompts\\inductor.txt")
)

safety_for_agent = (
    "If the client's message is irrelevant to electrical engineering or circuits, "
    "respond solely with the letter 'N'. There should be no additional commentary."
)
asc_generation_prompt = (
    "Generate the complete .asc code for the circuit the user requested. "
    "It is CRUCIAL that your response contains only the valid .asc code with no extra explanation. DO NOT add any comments or descriptions to the asc code, it MUST start with 'Version 4', don't include any headings like 'ASC code:'."
    "Your statements must be forceful, clear, and unequivocal, ensuring that the code can be directly imported into LTSpice."
)
user_prompt = "Customer's request:"

class ChatManager:
    """
    Provides methods for obtaining LLM responses:
      - get_asc_code() returns the .asc code for the circuit (from o3-mini).
      - get_chat_response() returns a friendly chat response (from gpt-4o-mini).
      - refine_asc_code() generates a revised ASC code based on conversation history and vision feedback.
      - get_status_update() produces a brief status update based on conversation history and latest vision feedback.
    """
    def get_asc_code(self, prompt: str) -> str:
        try:
            asc_resp = openai.ChatCompletion.create(
                model="o3-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return asc_resp.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating .asc code: {str(e)}"

    def get_chat_response(self, user_input: str) -> str:
        chat_prompt = (
            "If the client's message is directly related to circuit design, reply with a concise, confident greeting, "
            "and inform the client that the circuit is being generated. DO NOT include any .asc code in your response. "
            f"{user_prompt} {user_input}\n"
            "Provide a brief, assertive message that assures the client that the circuit is in process."
        )
        try:
            chat_resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": chat_prompt}]
            )
            return chat_resp.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating chat response: {str(e)}"

    def refine_asc_code(self, conversation_history: list, user_request: str) -> str:
        prompt = f"{general}\n Below are previous attempts and feedback:\n\n"
        for item in conversation_history:
            if "asc_code" in item:
                prompt += f"Attempt {item.get('attempt', item.get('iteration', '?'))} ASC code:\n{item['asc_code']}\n\n"
            if "vision_feedback" in item:
                prompt += f"Vision feedback (Iteration {item.get('iteration','?')}): {item['vision_feedback']}\n\n"
        prompt += f"Original user's request: {user_request}\n\n"
        prompt += (
            "Based on the above attempts and feedback, please provide a revised complete .asc code "
            "for a circuit that meets the user's request. Your answer must contain only valid .asc code with no additional explanation."
        )
        try:
            response = openai.ChatCompletion.create(
                model="o3-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error refining .asc code: {str(e)}"

    def get_status_update(self, conversation_history: list, vision_feedback: str, iteration: int) -> str:
        prompt = (
            "Based on the following conversation history and the latest vision feedback, "
            "provide a concise status update for the user. The update should explain why the current circuit attempt might be insufficient or what remains to be fixed, "
            "or indicate that the circuit is verified if it meets the request. Do not include any ASC code in your response.\n\n"
        )
        prompt += "Conversation History:\n"
        for item in conversation_history:
            prompt += f"{item}\n"
        prompt += f"\nLatest Vision Feedback (Iteration {iteration}): {vision_feedback}\n"
        prompt += "Status update:"
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating status update: {str(e)}"
