import os, base64
from dotenv import load_dotenv
import openai

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

class VisionManager:
    """
    Manages vision-based interactions with an OpenAI model that supports image inputs.
    Used to check if a generated circuit image (PNG) matches the user's request.
    """
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    def analyze_circuit_image(self, image_path: str, user_request: str, detail: str = "high") -> str:
        with open(image_path, "rb") as img_file:
            encoded_image = base64.b64encode(img_file.read()).decode("utf-8")
        prompt_text = (
            f"User's circuit request: {user_request}\n\n"
            "Below is an image of a circuit schematic. Please perform the following steps:\n"
            "1. List the circuit components you see in the image along with their values.\n"
            "2. Determine if the circuit exactly meets the user's request (i.e. it should have exactly the specified components with correct values and no extras).\n"
            "3. If it matches perfectly, reply with a single letter 'Y'. Otherwise, explain clearly which components are missing or incorrect. Or if wires are missing point them out\n"
            "For example, if the request is '1 resistor 10 ohms and 1 battery 5V', then the circuit must have exactly one resistor labeled 10 ohms and one battery labeled 5V.\n"
        )
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}", "detail": detail}}
                ]
            }
        ]
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                store=True
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error analyzing circuit image: {str(e)}"
