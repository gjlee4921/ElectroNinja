import openai
import os
from dotenv import load_dotenv

# Set your OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_o3mini_response(prompt):
    response = openai.Completion.create(
        engine="o3-mini",  # Specify the engine name
        prompt=prompt
    )
    # Extract and return the text from the first response choice
    return response.choices[0].text.strip()

if __name__ == "__main__":
    models = openai.Model.list()
    for model in models["data"]:
        print(model["id"])

    user_prompt = input("Enter your prompt: ")
    output = get_o3mini_response(user_prompt)
    print("Response:", output)
    
