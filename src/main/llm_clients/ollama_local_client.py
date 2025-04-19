from main.llm_clients.llm_client_interface import LLMClient
from ollama import ChatResponse
from ollama import AsyncClient
from main.config_loader import config_loader
from dotenv import load_dotenv
import os
import pathlib
from langfuse.decorators import observe


class OllamaLocalClient(LLMClient):
    """Client for Ollama Local API"""
    
    def __init__(self):
        self.client = AsyncClient()
        # self.client = InferenceClient(provider=provider, token=token)
        self.model = config_loader.get("ollama_local.model_name", "llama3.1:8b")
        
    @observe()
    async def generate_completion(self, user_messages, max_tokens=500, temperature=0.7, top_p=0.9):
        try:
            completion: ChatResponse = await self.client.chat(
                model=self.model,
                messages=user_messages,
                stream=False,
            )

            assistant_message = completion['message']['content']

            return assistant_message
        except Exception as e:
            print(f"Error with local Ollama API: {e}")
            return "Fallback: Unable to generate response."