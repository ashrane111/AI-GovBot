from main.llm_clients.llm_client_interface import LLMClient
from openai import AsyncOpenAI
from main.config_loader import config_loader
from dotenv import load_dotenv
import os
import pathlib
from langfuse.decorators import observe
from langfuse.openai import openai

# current_file = pathlib.Path(__file__)
# project_root = current_file.parent.parent.parent
# env_path = project_root / "main" / ".env"
# load_dotenv(dotenv_path=env_path)
load_dotenv()

class OpenAIClient(LLMClient):
    """Client for OpenAI API"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY") or config_loader.get("openai.api_key")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = config_loader.get("openai.model_name", "gpt-4o-mini")

    @observe()   
    async def generate_completion(self, user_messages, max_tokens=500, temperature=0.7, top_p=0.9):
        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=user_messages,
                # max_tokens=max_tokens,
                # temperature=temperature,
                # top_p=top_p,
            )

            assistant_message = completion.choices[0].message.content

            return assistant_message
        except Exception as e:
            print(f"Error with OpenAI API: {e}")
            return "Fallback: Unable to generate response."