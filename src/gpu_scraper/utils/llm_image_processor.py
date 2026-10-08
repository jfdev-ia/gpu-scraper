import os
from mistralai.client import Mistral
import base64
from dotenv import load_dotenv

load_dotenv()
api_key=os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key)

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

def process_image(img_path, system_prompt):
    response = client.chat.complete(
        model="mistral-small-2506",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user", 
                "content": [
                    {
                        "type": "image_url",
                        "image_url": encode_image(img_path)
                    }
                ]
            }
        ]
    )
    return response

def process_image_structured_output(img_path, system_prompt, model):
    response = client.chat.parse(
        model="mistral-small-2506",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user", 
                "content": [
                    {
                        "type": "image_url",
                        "image_url": encode_image(img_path)
                    }
                ]
            }
        ],
        response_format=model,
        temperature=0
    )
    return response
