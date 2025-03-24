from main.llm_clients.llm_client_interface import LLMClient
from huggingface_hub import InferenceClient, AsyncInferenceClient
from main.config_loader import config_loader
from dotenv import load_dotenv
import os
import pathlib

# current_file = pathlib.Path(__file__)
# project_root = current_file.parent.parent.parent
# env_path = project_root / "main" / ".env"
# load_dotenv(dotenv_path=env_path)
load_dotenv()

class HuggingFaceClient(LLMClient):
    """Client for HuggingFace Inference API"""
    
    def __init__(self):
        provider = config_loader.get("novita.provider", "novita")
        token = os.getenv("HUGGINGFACE_KEY") or config_loader.get("novita.token")
        self.client = AsyncInferenceClient(provider=provider, token=token)
        # self.client = InferenceClient(provider=provider, token=token)
        self.model = config_loader.get("huggingface.model_name", "deepseek-ai/DeepSeek-R1")
        
    async def generate_completion(self, user_messages, max_tokens=500, temperature=0.7, top_p=0.9):
        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=user_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )

            assistant_message = completion.choices[0].message["content"]

            return assistant_message
        except Exception as e:
            print(f"Error with HuggingFace Inference API: {e}")
            return "Fallback: Unable to generate response."