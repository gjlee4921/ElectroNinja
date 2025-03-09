import os
from dotenv import load_dotenv
import openai

# Load environment variables and set the API key on the module-level client.
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Prompt fragments with emphasis on assertive statements
general = (
    "You are a world-class electrical engineer with absolute authority in LTSpice circuit design. "
    "You write .asc files with unwavering precision. When a client asks you to build a circuit, "
    "you must respond with clear, definitive statements and the exact .asc code required."
)
safety_for_agent = (
    "If the client's message is irrelevant to electrical engineering or circuits, "
    "respond solely with the letter 'N'. There should be no additional commentary."
)
asc_generation_prompt = (
    "Generate the complete .asc code for the circuit the user requested. "
    "It is CRUCIAL that your response contains only the valid .asc code with no extra explanation. "
    "Your statements must be forceful, clear, and unequivocal, ensuring that the code can be directly imported into LTSpice."
)
user_prompt = "Customer's request:"

class ChatManager:
    """
    Provides methods for obtaining LLM responses:
      - get_asc_code() returns the .asc code for the circuit (from o3-mini).
      - get_chat_response() returns a friendly, assertive chat response for the client (from gpt-4o-mini).
    """

    def get_asc_code(self, prompt: str) -> str:
        """
        Generates the .asc code based on the provided prompt.
        
        :param prompt: The complete prompt including examples and the user's request.
        :return: The generated ASC code as a string, or "N" if the query is deemed irrelevant.
        """
        try:
            asc_resp = openai.ChatCompletion.create(
                model="o3-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            asc_output = asc_resp.choices[0].message.content.strip()
            return asc_output
        except Exception as e:
            return f"Error generating .asc code: {str(e)}"

    def get_chat_response(self, user_input: str) -> str:
        """
        Generates a friendly and assertive chat response for the client.
        
        :param user_input: The client's request.
        :return: The generated chat response as a string.
        """
        chat_prompt = (
            f"{general}\n"
            "If the client's message is not directly related to circuit design, reply with a concise, confident greeting. "
            f"{user_prompt} {user_input}\n"
            "Provide a brief, assertive message that informs the client that the circuit is being generated without any ambiguity."
        )
        try:
            chat_resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": chat_prompt}]
            )
            chat_output = chat_resp.choices[0].message.content.strip()
            return chat_output
        except Exception as e:
            return f"Error generating chat response: {str(e)}"
