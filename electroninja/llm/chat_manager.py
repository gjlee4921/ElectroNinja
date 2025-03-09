import os
from dotenv import load_dotenv

# Load environment variables from a .env file in the project root directory
load_dotenv()

# Import the OpenAI client
from openai import OpenAI

# Initialize the OpenAI client with your API key from the .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Prompt fragments
general = (
    "You are an expert electrical engineer that can use LTSpice to build circuits by writing .asc files. "
    "A client asks you to build a circuit, and in order to do that you have to write the .asc code."
)
safety_for_chat = (
    "If the message of the client is irrelevant to electrical engineering and circuits, "
    "simply say that you are here to help with electrical circuit designing, and nothing else."
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
response_generation_prompt = (
    "Here generate a brief message to send to your client as they wait for the circuit to be generated."
)
user_prompt = "Your customer's request is:"

class ChatManager:
    """
    Provides separate methods for obtaining LLM responses.
      - get_asc_code() returns the .asc code for the circuit (from o3-mini).
      - get_chat_response() returns a friendly chat response for the client (from gpt-4o-mini).
    """

    def get_asc_code(self, user_input: str) -> str:
        """
        Generate the .asc code for the circuit based on the user's request.
        :param user_input: The client's request.
        :return: The .asc code as a string, or "N" if the query is deemed irrelevant.
        """
        asc_prompt = (
            f"{general}\n"
            f"{safety_for_agent}\n"
            f"{user_prompt} {user_input}\n"
            f"{asc_generation_prompt}"
        )
        try:
            asc_resp = client.chat.completions.create(
                model="o3-mini",
                messages=[{"role": "user", "content": asc_prompt}]
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
            f"{safety_for_chat}\n"
            f"{user_prompt} {user_input}\n"
            f"{response_generation_prompt}"
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
