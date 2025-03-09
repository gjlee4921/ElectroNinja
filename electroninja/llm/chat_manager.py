import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Prompt fragments
general = (
    "You are an expert electrical engineer that can use LTSpice to build circuits by writing .asc files. "
    "A client asks you to build a circuit, and in order to do that you have to write the .asc code."
)
safety_for_agent = (
    "If the message of the client is irrelevant to electrical engineering and circuits, "
    "just produce the letter 'N'. The answer should contain nothing else, just the letter."
)
asc_generation_prompt = (
    "Now generate the .asc code for the circuit the user asked. In your answer it is EXTREMELY IMPORTANT, "
    "that only .asc code is contained, with no additional explanation. This code will be imported into LTSpice "
    "so that the circuit is visible to the user."
)
user_prompt = "Your customer's request is:"

class ChatManager:
    """
    Provides separate methods for obtaining LLM responses.
      - get_asc_code() returns the .asc code for the circuit (from o3-mini).
      - get_chat_response() returns a friendly chat response for the client (from gpt-4o-mini).
    """

    def get_asc_code(self, prompt: str) -> str:
        """
        Generate the .asc code based on the provided prompt.
        :param prompt: The complete prompt (which includes examples and the user request).
        :return: The .asc code as a string, or "N" if the query is deemed irrelevant.
        """
        try:
            asc_resp = client.chat.completions.create(
                model="o3-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            asc_output = asc_resp.choices[0].message.content.strip()
            return asc_output
        except Exception as e:
            return f"Error generating .asc code: {str(e)}"

    def get_chat_response(self, user_input: str) -> str:
        """
        Generate a friendly chat response for the client.
        :param user_input: The client's request.
        :return: The chat response as a string.
        """
        chat_prompt = (
            f"{general}\n"
            "If the user's message is not circuit-related, simply reply with a short, friendly response. "
            f"{user_prompt} {user_input}\n"
            "Here generate a brief message to send to your client as they wait for the circuit to be generated."
        )
        try:
            chat_resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": chat_prompt}]
            )
            chat_output = chat_resp.choices[0].message.content.strip()
            return chat_output
        except Exception as e:
            return f"Error generating chat response: {str(e)}"
